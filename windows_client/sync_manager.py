import threading
import time
import logging
import requests
from datetime import datetime
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
            
            # Emit completion signal
            message = "Synchronization completed successfully" if success else "Synchronization completed with errors"
            self.sync_completed.emit(success, message)
            self.logger.info(message)
            
        except Exception as e:
            self.logger.error(f"Sync error: {e}")
            self.sync_completed.emit(False, f"Synchronization failed: {str(e)}")
        
        finally:
            self.is_syncing = False
    
    def _sync_pending_operations(self):
        """Synchronize pending operations with the server"""
        operations = self.db.get_pending_operations()
        if not operations:
            return True
            
        self.logger.info(f"Syncing {len(operations)} pending operations")
        
        success = True
        for i, op in enumerate(operations):
            try:
                # Update progress
                self.sync_progress.emit(i + 1, len(operations))
                
                # Execute the operation
                response = requests.request(
                    op['method'],
                    f"{self.api_client.base_url}{op['endpoint']}",
                    json=op['data'],
                    headers={'Authorization': f'Bearer {self.api_client.token}'} if self.api_client.token else {},
                    timeout=10
                )
                
                if response.ok:
                    # Mark as synced
                    self.db.mark_operation_synced(op['id'])
                    self.logger.info(f"Operation {op['id']} synced successfully")
                else:
                    self.logger.error(f"Operation {op['id']} failed: {response.status_code} - {response.text}")
                    success = False
                    
            except Exception as e:
                self.logger.error(f"Error syncing operation {op['id']}: {e}")
                success = False
        
        return success
    
    def _sync_maintenance_records(self):
        """Synchronize pending maintenance records"""
        records = self.db.get_pending_maintenance()
        if not records:
            return True
            
        self.logger.info(f"Syncing {len(records)} maintenance records")
        
        success = True
        for i, record in enumerate(records):
            try:
                # Update progress
                self.sync_progress.emit(i + 1, len(records))
                
                # Send to server
                data = {
                    'part_id': record['part_id'],
                    'notes': record['data'].get('notes', ''),
                    'timestamp': record['timestamp']
                }
                
                response = requests.post(
                    f"{self.api_client.base_url}/api/maintenance/record",
                    json=data,
                    headers={'Authorization': f'Bearer {self.api_client.token}'} if self.api_client.token else {},
                    timeout=10
                )
                
                if response.ok:
                    # Mark as synced
                    self.db.mark_maintenance_synced(record['id'])
                    self.logger.info(f"Maintenance record {record['id']} synced successfully")
                else:
                    self.logger.error(f"Maintenance record {record['id']} failed: {response.status_code} - {response.text}")
                    success = False
                    
            except Exception as e:
                self.logger.error(f"Error syncing maintenance record {record['id']}: {e}")
                success = False
        
        return success
    
    def force_sync(self):
        """Force an immediate synchronization"""
        if not self.is_syncing:
            threading.Thread(target=self._trigger_sync, daemon=True).start()
    
    def is_connected(self):
        """Check if we're currently online"""
        return self.is_online
