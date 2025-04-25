import threading
import time
import logging
import requests
import json
import random
from datetime import datetime, timedelta
from PyQt6.QtCore import QObject, pyqtSignal

class SyncManager(QObject):
    """Manages background synchronization of offline data"""
    
    # Signals
    sync_started = pyqtSignal()
    sync_completed = pyqtSignal(bool, str)  # success, message
    sync_progress = pyqtSignal(int, int)    # current, total
    connection_state_changed = pyqtSignal(bool)  # is_online
    
    def __init__(self, api_client, offline_db):
        super().__init__()
        self.api_client = api_client
        self.db = offline_db
        self.is_online = True
        self.is_syncing = False
        self.sync_interval = 300  # 5 minutes
        self.check_interval = 30  # 30 seconds
        self.sync_thread = None
        self.conn_check_thread = None
        self.logger = logging.getLogger("SyncManager")
        
        # Enhanced parameters for better sync reliability
        self.max_retry_attempts = 5
        self.base_retry_delay = 3  # seconds
        self.max_retry_delay = 60  # seconds
        self.jitter_factor = 0.25  # random jitter percentage
        self.batch_size = 10  # process operations in batches
        self.conflict_resolution_strategy = "server_wins"  # or "client_wins" or "newest_wins"
        
        # Set up logging
        handler = logging.FileHandler("sync_manager.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def start(self):
        """Start the sync and connection check threads"""
        # Start the sync thread
        self.sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
        self.sync_thread.start()
        
        # Start the connection check thread
        self.conn_check_thread = threading.Thread(target=self._connection_check_worker, daemon=True)
        self.conn_check_thread.start()
        
        self.logger.info("Sync manager started")
    
    def _connection_check_worker(self):
        """Worker thread to periodically check connection status"""
        while True:
            try:
                # Try to connect to the server
                response = requests.get(
                    f"{self.api_client.base_url}/api/health", 
                    timeout=5
                )
                
                online = response.status_code == 200
                
                # If connection state changed
                if online != self.is_online:
                    self.is_online = online
                    self.connection_state_changed.emit(online)
                    
                    if online:
                        self.logger.info("Connection restored, triggering sync")
                        self._trigger_sync()
                    else:
                        self.logger.info("Connection lost, entering offline mode")
            
            except Exception as e:
                # If we can't reach the server, we're offline
                if self.is_online:
                    self.is_online = False
                    self.connection_state_changed.emit(False)
                    self.logger.info(f"Connection check failed: {e}")
            
            # Wait before checking again
            time.sleep(self.check_interval)
    
    def _sync_worker(self):
        """Worker thread to periodically sync data"""
        while True:
            # Only sync if we're online and not already syncing
            if self.is_online and not self.is_syncing:
                self._trigger_sync()
            
            # Wait before syncing again
            time.sleep(self.sync_interval)
    
    def _trigger_sync(self):
        """Trigger a synchronization"""
        if self.is_syncing:
            return
            
        self.is_syncing = True
        self.sync_started.emit()
        self.logger.info("Starting synchronization")
        
        try:
            # First sync pending operations
            success = self._sync_pending_operations()
            
            # Then sync maintenance records
            if success:
                success = self._sync_maintenance_records()
            
            # Fetch updates from server if we've successfully sent our changes
            if success:
                success = self._fetch_server_updates()
            
            # Emit completion signal
            message = "Synchronization completed successfully" if success else "Synchronization completed with some errors"
            self.sync_completed.emit(success, message)
            self.logger.info(message)
            
        except Exception as e:
            self.logger.error(f"Sync error: {e}")
            self.sync_completed.emit(False, f"Synchronization failed: {str(e)}")
        
        finally:
            self.is_syncing = False

    def _calculate_retry_delay(self, attempt):
        """Calculate retry delay with exponential backoff and jitter"""
        # Base exponential delay: base_delay * 2^attempt
        delay = self.base_retry_delay * (2 ** attempt)
        
        # Cap at max delay
        delay = min(delay, self.max_retry_delay)
        
        # Add jitter to avoid thundering herd problem
        jitter = random.uniform(-self.jitter_factor, self.jitter_factor) * delay
        delay = max(1, delay + jitter)  # Ensure minimum 1 second delay
        
        return delay
    
    def _sync_pending_operations(self):
        """Synchronize pending operations with the server"""
        operations = self.db.get_pending_operations()
        if not operations:
            return True
            
        self.logger.info(f"Syncing {len(operations)} pending operations")
        
        # Process in batches for better error handling
        batches = [operations[i:i + self.batch_size] for i in range(0, len(operations), self.batch_size)]
        
        success = True
        total_ops = len(operations)
        ops_processed = 0
        
        for batch_idx, batch in enumerate(batches):
            self.logger.info(f"Processing batch {batch_idx + 1}/{len(batches)}")
            
            for op in batch:
                try:
                    # Update progress
                    ops_processed += 1
                    self.sync_progress.emit(ops_processed, total_ops)
                    
                    # Check current retry count
                    if op.get('sync_attempts', 0) >= self.max_retry_attempts:
                        self.logger.warning(f"Operation {op['id']} exceeded max retry attempts. Marking as failed.")
                        self.db.mark_operation_failed(op['id'], "Exceeded maximum retry attempts")
                        continue
                    
                    # Execute the operation
                    response = requests.request(
                        op['method'],
                        f"{self.api_client.base_url}{op['endpoint']}",
                        json=op['data'],
                        headers={'Authorization': f'Bearer {self.api_client.token}'} if self.api_client.token else {},
                        timeout=15  # Longer timeout for operations
                    )
                    
                    if response.ok:
                        # Mark as synced
                        self.db.mark_operation_synced(op['id'])
                        self.logger.info(f"Operation {op['id']} synced successfully")
                    elif response.status_code == 409:
                        # Conflict detected - resolve based on strategy
                        self._handle_conflict(op, response)
                    else:
                        # Handle server errors
                        delay = self._calculate_retry_delay(op.get('sync_attempts', 0))
                        self.logger.error(f"Operation {op['id']} failed: {response.status_code} - {response.text}. Retrying in {delay:.1f}s")
                        self.db.increment_sync_attempt(op['id'])
                        success = False
                    
                except requests.exceptions.Timeout:
                    # Handle timeout specially - might be a slow connection
                    self.logger.warning(f"Timeout for operation {op['id']}")
                    self.db.increment_sync_attempt(op['id'])
                    success = False
                    
                except Exception as e:
                    self.logger.error(f"Error syncing operation {op['id']}: {e}")
                    self.db.increment_sync_attempt(op['id'])
                    success = False
            
            # Small delay between batches to avoid overwhelming the server
            time.sleep(1)
        
        return success
    
    def _handle_conflict(self, op, response):
        """Handle data conflicts based on configured strategy"""
        try:
            server_data = response.json()
            
            if self.conflict_resolution_strategy == "server_wins":
                # Accept server's version - mark our operation as synced
                self.logger.info(f"Conflict for operation {op['id']} resolved with server_wins strategy")
                self.db.mark_operation_synced(op['id'])
                
                # Store the server's version locally if provided
                if 'entity_type' in server_data and 'entity_data' in server_data:
                    self._update_local_entity(server_data['entity_type'], server_data['entity_data'])
            
            elif self.conflict_resolution_strategy == "client_wins":
                # Force our changes with a special header
                self.logger.info(f"Conflict for operation {op['id']} resolved with client_wins strategy")
                response = requests.request(
                    op['method'],
                    f"{self.api_client.base_url}{op['endpoint']}",
                    json=op['data'],
                    headers={
                        'Authorization': f'Bearer {self.api_client.token}' if self.api_client.token else '',
                        'X-Force-Update': 'true'
                    },
                    timeout=15
                )
                
                if response.ok:
                    self.db.mark_operation_synced(op['id'])
                else:
                    self.db.increment_sync_attempt(op['id'])
            
            elif self.conflict_resolution_strategy == "newest_wins":
                # Compare timestamps and use the newest version
                client_timestamp = op.get('timestamp', datetime.min.isoformat())
                server_timestamp = server_data.get('timestamp', datetime.min.isoformat())
                
                client_dt = datetime.fromisoformat(client_timestamp)
                server_dt = datetime.fromisoformat(server_timestamp)
                
                if client_dt > server_dt:
                    # Our version is newer, force it
                    self.logger.info(f"Conflict for operation {op['id']} resolved with newest_wins strategy (client wins)")
                    response = requests.request(
                        op['method'],
                        f"{self.api_client.base_url}{op['endpoint']}",
                        json=op['data'],
                        headers={
                            'Authorization': f'Bearer {self.api_client.token}' if self.api_client.token else '',
                            'X-Force-Update': 'true'
                        },
                        timeout=15
                    )
                    
                    if response.ok:
                        self.db.mark_operation_synced(op['id'])
                    else:
                        self.db.increment_sync_attempt(op['id'])
                else:
                    # Server version is newer, accept it
                    self.logger.info(f"Conflict for operation {op['id']} resolved with newest_wins strategy (server wins)")
                    self.db.mark_operation_synced(op['id'])
                    
                    # Store the server's version locally if provided
                    if 'entity_type' in server_data and 'entity_data' in server_data:
                        self._update_local_entity(server_data['entity_type'], server_data['entity_data'])
            
        except Exception as e:
            self.logger.error(f"Error handling conflict for operation {op['id']}: {e}")
            self.db.increment_sync_attempt(op['id'])
    
    def _update_local_entity(self, entity_type, entity_data):
        """Update local entity with server data"""
        try:
            if entity_type == 'machine':
                self.db.store_machine_data(entity_data['id'], entity_data)
            elif entity_type == 'part':
                self.db.store_part_data(entity_data['id'], entity_data)
            elif entity_type == 'site':
                self.db.store_site_data(entity_data['id'], entity_data)
            self.logger.info(f"Updated local {entity_type} data from server")
        except Exception as e:
            self.logger.error(f"Error updating local {entity_type}: {e}")
    
    def _sync_maintenance_records(self):
        """Synchronize pending maintenance records"""
        records = self.db.get_pending_maintenance()
        if not records:
            return True
            
        self.logger.info(f"Syncing {len(records)} maintenance records")
        
        # Process in batches like operations
        batches = [records[i:i + self.batch_size] for i in range(0, len(records), self.batch_size)]
        
        success = True
        total_records = len(records)
        records_processed = 0
        
        for batch in batches:
            for record in batch:
                try:
                    # Update progress
                    records_processed += 1
                    self.sync_progress.emit(records_processed, total_records)
                    
                    # Check current retry count
                    if record.get('sync_attempts', 0) >= self.max_retry_attempts:
                        self.logger.warning(f"Maintenance record {record['id']} exceeded max retry attempts. Marking as failed.")
                        self.db.mark_maintenance_failed(record['id'], "Exceeded maximum retry attempts")
                        continue
                    
                    # Send to server
                    data = {
                        'part_id': record['part_id'],
                        'notes': record['data'].get('notes', ''),
                        'timestamp': record['timestamp'],
                        'client_id': record['id']  # Include client ID for deduplication
                    }
                    
                    response = requests.post(
                        f"{self.api_client.base_url}/api/maintenance/record",
                        json=data,
                        headers={'Authorization': f'Bearer {self.api_client.token}'} if self.api_client.token else {},
                        timeout=15
                    )
                    
                    if response.ok:
                        # Mark as synced
                        self.db.mark_maintenance_synced(record['id'])
                        self.logger.info(f"Maintenance record {record['id']} synced successfully")
                        
                        # If server returned updated part data, store it
                        try:
                            server_data = response.json()
                            if 'part' in server_data:
                                self.db.store_part_data(server_data['part']['id'], server_data['part'])
                        except:
                            pass
                    else:
                        delay = self._calculate_retry_delay(record.get('sync_attempts', 0))
                        self.logger.error(f"Maintenance record {record['id']} failed: {response.status_code} - {response.text}. Retrying in {delay:.1f}s")
                        self.db.increment_maintenance_sync_attempt(record['id'])
                        success = False
                        
                except Exception as e:
                    self.logger.error(f"Error syncing maintenance record {record['id']}: {e}")
                    self.db.increment_maintenance_sync_attempt(record['id'])
                    success = False
            
            # Small delay between batches
            time.sleep(1)
        
        return success
    
    def _fetch_server_updates(self):
        """Fetch updates from the server for sites, machines, and parts"""
        try:
            self.logger.info("Fetching updates from server")
            
            # Only fetch if we have authentication
            if not self.api_client.token:
                self.logger.warning("No authentication token available for fetching updates")
                return True
            
            # Get last sync timestamp or use a default
            last_sync = self.db.get_setting('last_server_sync') or datetime.min.isoformat()
            
            # Fetch sites, machines, and parts with changes since last sync
            endpoints = [
                '/api/sites?modified_since=' + last_sync,
                '/api/machines?modified_since=' + last_sync,
                '/api/parts?modified_since=' + last_sync
            ]
            
            for i, endpoint in enumerate(endpoints):
                try:
                    # Update progress based on current step
                    self.sync_progress.emit(i + 1, len(endpoints) + 1)
                    
                    response = requests.get(
                        f"{self.api_client.base_url}{endpoint}",
                        headers={'Authorization': f'Bearer {self.api_client.token}'},
                        timeout=15
                    )
                    
                    if response.ok:
                        data = response.json()
                        
                        # Store the data based on endpoint type
                        if 'sites' in endpoint:
                            for site in data.get('sites', []):
                                self.db.store_site_data(site['id'], site)
                            
                        elif 'machines' in endpoint:
                            for machine in data.get('machines', []):
                                self.db.store_machine_data(machine['id'], machine)
                            
                        elif 'parts' in endpoint:
                            for part in data.get('parts', []):
                                self.db.store_part_data(part['id'], part)
                    
                    else:
                        self.logger.error(f"Error fetching from {endpoint}: {response.status_code} - {response.text}")
                
                except Exception as e:
                    self.logger.error(f"Error processing endpoint {endpoint}: {e}")
            
            # Update last sync timestamp
            self.db.store_setting('last_server_sync', datetime.now().isoformat())
            self.sync_progress.emit(len(endpoints) + 1, len(endpoints) + 1)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error fetching server updates: {e}")
            return False
    
    def force_sync(self):
        """Force an immediate synchronization"""
        if not self.is_syncing:
            threading.Thread(target=self._trigger_sync, daemon=True).start()
    
    def is_connected(self):
        """Check if we're currently online"""
        return self.is_online
