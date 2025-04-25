import time
import logging
import threading
import queue
from datetime import datetime, timedelta
from PyQt6.QtCore import QObject, pyqtSignal

class BatchSyncTask:
    """Represents a batch of database operations to be synchronized"""
    
    def __init__(self, task_type, items, batch_id=None):
        self.task_type = task_type  # 'push' (local → server) or 'pull' (server → local)
        self.items = items  # List of items to sync
        self.batch_id = batch_id or datetime.now().strftime('%Y%m%d%H%M%S')
        self.started_at = None
        self.completed_at = None
        self.success_count = 0
        self.failure_count = 0
        self.status = 'pending'  # pending, in_progress, completed, failed
        
    def start(self):
        """Mark the batch as started"""
        self.started_at = datetime.now()
        self.status = 'in_progress'
        
    def complete(self, success_count, failure_count):
        """Mark the batch as completed"""
        self.completed_at = datetime.now()
        self.success_count = success_count
        self.failure_count = failure_count
        
        # Set status based on outcome
        if failure_count == 0:
            self.status = 'completed'
        elif success_count > 0:
            self.status = 'partial'
        else:
            self.status = 'failed'
        
    def duration(self):
        """Calculate duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0
        
    def to_dict(self):
        """Convert batch to dictionary for storage"""
        return {
            'batch_id': self.batch_id,
            'task_type': self.task_type,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'total_count': len(self.items),
            'status': self.status,
            'duration_seconds': self.duration()
        }

class BatchSyncManager(QObject):
    """
    Enhanced synchronization manager for handling large datasets
    using batch processing and prioritization
    """
    
    # Signals
    batch_started = pyqtSignal(str)  # batch_id
    batch_completed = pyqtSignal(str, bool, int, int)  # batch_id, success, success_count, failure_count
    batch_progress = pyqtSignal(str, int, int)  # batch_id, current, total
    sync_stats_updated = pyqtSignal(dict)  # stats dict
    
    def __init__(self, api_client, offline_db, config=None):
        super().__init__()
        self.api_client = api_client
        self.db = offline_db
        self.config = config or {}
        
        # Queue for tasks
        self.task_queue = queue.PriorityQueue()
        
        # Track running tasks
        self.active_batch = None
        self.is_syncing = False
        self.stop_requested = False
        
        # Statistics
        self.stats = {
            'batches_completed': 0,
            'total_synced': 0,
            'total_failed': 0,
            'last_sync': None,
            'avg_throughput': 0  # items per second
        }
        
        # Set up logging
        self.logger = logging.getLogger("BatchSyncManager")
        handler = logging.FileHandler("batch_sync_manager.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Configuration defaults
        self.max_batch_size = self.config.get('max_batch_size', 100)
        self.min_sync_interval = self.config.get('min_sync_interval', 30)  # seconds
        self.timeout = self.config.get('timeout', 30)  # seconds
        self.max_retries = self.config.get('max_retries', 3)
        
        # Thread control
        self.sync_thread = None
        self._lock = threading.RLock()
    
    def start(self):
        """Start the sync thread"""
        if self.sync_thread is not None and self.sync_thread.is_alive():
            self.logger.warning("Sync thread already running")
            return
            
        self.stop_requested = False
        self.sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
        self.sync_thread.start()
        self.logger.info("Batch sync manager started")
    
    def stop(self):
        """Signal the sync thread to stop"""
        self.stop_requested = True
        self.logger.info("Stop requested for sync thread")
    
    def queue_push_batch(self, items, priority=2, batch_id=None):
        """Queue a batch of items to be pushed to the server"""
        if not items:
            return None
            
        # Split into smaller batches if needed
        if len(items) > self.max_batch_size:
            batch_ids = []
            for i in range(0, len(items), self.max_batch_size):
                batch = items[i:i + self.max_batch_size]
                batch_task = BatchSyncTask('push', batch, batch_id)
                self.task_queue.put((priority, batch_task))
                batch_ids.append(batch_task.batch_id)
                
            self.logger.info(f"Queued {len(batch_ids)} push batches with {len(items)} total items")
            return batch_ids
        else:
            batch_task = BatchSyncTask('push', items, batch_id)
            self.task_queue.put((priority, batch_task))
            self.logger.info(f"Queued push batch {batch_task.batch_id} with {len(items)} items")
            return batch_task.batch_id
    
    def queue_pull_batch(self, query_params, entity_type, priority=1, batch_id=None):
        """Queue a batch of data to be pulled from the server"""
        batch_task = BatchSyncTask('pull', [{'type': entity_type, 'params': query_params}], batch_id)
        self.task_queue.put((priority, batch_task))
        self.logger.info(f"Queued pull batch {batch_task.batch_id} for {entity_type}")
        return batch_task.batch_id
    
    def sync_all_pending(self, priority=0):
        """Sync all pending operations and maintenance records"""
        # Get all pending operations
        operations = self.db.get_pending_operations()
        if operations:
            self.queue_push_batch(operations, priority=priority, batch_id='pending_ops')
            
        # Get all pending maintenance records
        maintenance = self.db.get_pending_maintenance()
        if maintenance:
            self.queue_push_batch(maintenance, priority=priority, batch_id='pending_maintenance')
        
        return len(operations) + len(maintenance)
    
    def sync_data_update(self, max_age=24):
        """Pull updated data from the server if older than max_age hours"""
        last_sync = self.db.get_setting('last_server_sync')
        
        if not last_sync or self._hours_since(last_sync) >= max_age:
            # Queue data pulls in order of priority
            self.queue_pull_batch({'updated_since': last_sync}, 'sites', priority=1)
            self.queue_pull_batch({'updated_since': last_sync}, 'machines', priority=2)
            self.queue_pull_batch({'updated_since': last_sync}, 'parts', priority=3)
            self.logger.info(f"Queued data update, last sync was: {last_sync}")
            return True
        else:
            self.logger.info(f"Data update skipped, last sync was only {self._hours_since(last_sync):.1f} hours ago")
            return False
    
    def _hours_since(self, timestamp_str):
        """Calculate hours since a timestamp"""
        try:
            last_sync_time = datetime.fromisoformat(timestamp_str)
            delta = datetime.now() - last_sync_time
            return delta.total_seconds() / 3600
        except:
            return float('inf')  # If invalid timestamp, treat as very old
    
    def _sync_worker(self):
        """Background thread for processing sync tasks"""
        self.logger.info("Sync worker thread started")
        
        last_sync_time = time.time() - self.min_sync_interval  # Allow immediate first sync
        
        while not self.stop_requested:
            try:
                # Respect minimum sync interval
                time_since_last = time.time() - last_sync_time
                if time_since_last < self.min_sync_interval:
                    time.sleep(self.min_sync_interval - time_since_last)
                
                # Check if we have a task to process
                try:
                    # Non-blocking get with timeout
                    priority, batch_task = self.task_queue.get(timeout=1)
                except queue.Empty:
                    # No tasks, check for auto-sync opportunity
                    if not self.is_syncing and not self.stop_requested:
                        # Every 5 minutes, check for pending operations
                        if time.time() - last_sync_time >= 300:
                            pending_count = self.sync_all_pending(priority=2)
                            if pending_count > 0:
                                self.logger.info(f"Auto-sync queued {pending_count} pending items")
                                
                            # Every 12 hours, update server data
                            if not self.stop_requested and self._hours_since(self.db.get_setting('last_server_sync') or '2000-01-01') >= 12:
                                self.sync_data_update()
                    continue
                
                # We have a task to process
                with self._lock:
                    self.is_syncing = True
                    self.active_batch = batch_task
                
                # Process the batch
                batch_task.start()
                self.batch_started.emit(batch_task.batch_id)
                self.logger.info(f"Starting batch {batch_task.batch_id} ({batch_task.task_type})")
                
                if batch_task.task_type == 'push':
                    self._process_push_batch(batch_task)
                elif batch_task.task_type == 'pull':
                    self._process_pull_batch(batch_task)
                
                # Task complete
                last_sync_time = time.time()
                self.task_queue.task_done()
                
                with self._lock:
                    self.is_syncing = False
                    self.active_batch = None
                    
                # Update statistics
                self._update_stats(batch_task)
                
            except Exception as e:
                self.logger.error(f"Error in sync worker: {str(e)}", exc_info=True)
                with self._lock:
                    self.is_syncing = False
                    self.active_batch = None
                time.sleep(5)  # Wait before trying again after error
        
        self.logger.info("Sync worker thread stopped")
    
    def _process_push_batch(self, batch):
        """Process a push batch (local → server)"""
        success_count = 0
        failure_count = 0
        
        total_items = len(batch.items)
        for i, item in enumerate(batch.items):
            # Check for stop request
            if self.stop_requested:
                self.logger.info("Stop requested during batch processing")
                break
                
            try:
                # Update progress
                self.batch_progress.emit(batch.batch_id, i + 1, total_items)
                
                # Process based on item type
                if 'method' in item:  # It's an operation
                    success = self._process_operation(item)
                elif 'part_id' in item:  # It's a maintenance record
                    success = self._process_maintenance(item)
                else:
                    self.logger.error(f"Unknown item type in push batch: {item}")
                    success = False
                
                # Track success/failure
                if success:
                    success_count += 1
                else:
                    failure_count += 1
                    
            except Exception as e:
                self.logger.error(f"Error processing push item: {str(e)}", exc_info=True)
                failure_count += 1
        
        # Complete the batch
        batch.complete(success_count, failure_count)
        self.batch_completed.emit(batch.batch_id, failure_count == 0, success_count, failure_count)
        
        # Store batch history
        self._store_batch_history(batch)
        
        self.logger.info(f"Completed push batch {batch.batch_id}: {success_count} succeeded, {failure_count} failed")
        return success_count, failure_count
    
    def _process_operation(self, op):
        """Process a single operation"""
        try:
            response = self.api_client.execute_request(
                op['method'],
                op['endpoint'],
                op['data'],
                timeout=self.timeout
            )
            
            if response:
                self.db.mark_operation_synced(op['id'])
                return True
            else:
                self.db.increment_sync_attempt(op['id'])
                return False
        except Exception as e:
            self.logger.error(f"Error processing operation {op['id']}: {str(e)}")
            self.db.increment_sync_attempt(op['id'])
            return False
    
    def _process_maintenance(self, record):
        """Process a single maintenance record"""
        try:
            data = {
                'part_id': record['part_id'],
                'notes': record['data'].get('notes', ''),
                'timestamp': record['timestamp'],
                'client_id': record['id']
            }
            
            response = self.api_client.execute_request(
                'POST',
                '/api/maintenance/record',
                data,
                timeout=self.timeout
            )
            
            if response:
                self.db.mark_maintenance_synced(record['id'])
                return True
            else:
                self.db.increment_maintenance_sync_attempt(record['id'])
                return False
        except Exception as e:
            self.logger.error(f"Error processing maintenance record {record['id']}: {str(e)}")
            self.db.increment_maintenance_sync_attempt(record['id'])
            return False
    
    def _process_pull_batch(self, batch):
        """Process a pull batch (server → local)"""
        success_count = 0
        failure_count = 0
        
        total_items = len(batch.items)
        for i, item in enumerate(batch.items):
            # Check for stop request
            if self.stop_requested:
                self.logger.info("Stop requested during pull batch processing")
                break
                
            try:
                # Update progress
                self.batch_progress.emit(batch.batch_id, i + 1, total_items)
                
                # Call appropriate API endpoint based on entity type
                entity_type = item['type']
                params = item.get('params', {})
                
                if entity_type == 'sites':
                    self._pull_sites(params)
                    success_count += 1
                elif entity_type == 'machines':
                    self._pull_machines(params)
                    success_count += 1
                elif entity_type == 'parts':
                    self._pull_parts(params)
                    success_count += 1
                else:
                    self.logger.error(f"Unknown entity type in pull batch: {entity_type}")
                    failure_count += 1
                    
            except Exception as e:
                self.logger.error(f"Error processing pull item: {str(e)}", exc_info=True)
                failure_count += 1
        
        # Update last sync timestamp
        self.db.store_setting('last_server_sync', datetime.now().isoformat())
        
        # Complete the batch
        batch.complete(success_count, failure_count)
        self.batch_completed.emit(batch.batch_id, failure_count == 0, success_count, failure_count)
        
        # Store batch history
        self._store_batch_history(batch)
        
        self.logger.info(f"Completed pull batch {batch.batch_id}: {success_count} succeeded, {failure_count} failed")
        return success_count, failure_count
    
    def _pull_sites(self, params):
        """Pull sites data from server"""
        endpoint = '/api/sites'
        if params:
            endpoint += '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
            
        response = self.api_client.execute_request('GET', endpoint)
        
        if response and 'sites' in response:
            sites = response.get('sites', [])
            for site in sites:
                self.db.store_site_data(site['id'], site)
            self.logger.info(f"Pulled {len(sites)} sites from server")
            return True
        return False
    
    def _pull_machines(self, params):
        """Pull machines data from server"""
        endpoint = '/api/machines'
        if params:
            endpoint += '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
            
        response = self.api_client.execute_request('GET', endpoint)
        
        if response and 'machines' in response:
            machines = response.get('machines', [])
            for machine in machines:
                self.db.store_machine_data(machine['id'], machine)
            self.logger.info(f"Pulled {len(machines)} machines from server")
            return True
        return False
    
    def _pull_parts(self, params):
        """Pull parts data from server"""
        endpoint = '/api/parts'
        if params:
            endpoint += '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
            
        response = self.api_client.execute_request('GET', endpoint)
        
        if response and 'parts' in response:
            parts = response.get('parts', [])
            for part in parts:
                self.db.store_part_data(part['id'], part)
            self.logger.info(f"Pulled {len(parts)} parts from server")
            return True
        return False
    
    def _store_batch_history(self, batch):
        """Store batch history in the database"""
        try:
            self.db.store_sync_batch(batch.to_dict())
        except Exception as e:
            self.logger.error(f"Error storing batch history: {str(e)}")
    
    def _update_stats(self, batch):
        """Update sync statistics"""
        with self._lock:
            self.stats['batches_completed'] += 1
            self.stats['total_synced'] += batch.success_count
            self.stats['total_failed'] += batch.failure_count
            self.stats['last_sync'] = datetime.now().isoformat()
            
            # Update throughput calculation
            if batch.duration() > 0:
                batch_throughput = (batch.success_count + batch.failure_count) / batch.duration()
                # Exponential moving average with 0.3 weight for new value
                if self.stats['avg_throughput'] == 0:
                    self.stats['avg_throughput'] = batch_throughput
                else:
                    self.stats['avg_throughput'] = 0.3 * batch_throughput + 0.7 * self.stats['avg_throughput']
        
        # Emit updated stats
        self.sync_stats_updated.emit(self.stats)
    
    def get_stats(self):
        """Get current statistics"""
        with self._lock:
            return dict(self.stats)
    
    def get_active_batch(self):
        """Get the currently active batch if any"""
        with self._lock:
            return self.active_batch
    
    def get_queue_size(self):
        """Get the current task queue size"""
        return self.task_queue.qsize()
    
    def clear_queue(self):
        """Clear the task queue"""
        with self._lock:
            # Create a new queue
            old_queue = self.task_queue
            self.task_queue = queue.PriorityQueue()
            
        # Log the clear operation
        self.logger.info(f"Task queue cleared, {old_queue.qsize()} tasks removed")
