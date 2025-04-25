import os
import time
import logging
import sqlite3
import threading
from datetime import datetime, timedelta

class DataPruningManager:
    """
    Manages automatic pruning of old data from the offline database
    to prevent unbounded growth over time
    """
    
    def __init__(self, offline_db, config=None):
        self.db = offline_db
        self.config = config or {}
        
        # Set up logging
        self.logger = logging.getLogger("DataPruningManager")
        handler = logging.FileHandler("data_pruning.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Configuration with defaults
        self.default_retention_days = self.config.get('default_retention_days', 90)
        self.min_retention_days = self.config.get('min_retention_days', 30)
        self.check_frequency_hours = self.config.get('check_frequency_hours', 24)
        self.auto_prune = self.config.get('auto_prune', True)
        self.max_db_size_mb = self.config.get('max_db_size_mb', 100)
        
        # Keep track of the last prune time
        self.last_prune_time = None
        
        # Map of tables and their retention policy
        self.retention_policy = {
            'maintenance_history': {
                'completed': self.config.get('history_retention_days', 90),
                'failed': self.config.get('failed_retention_days', 30)
            },
            'pending_operations': {
                'completed': self.config.get('operation_retention_days', 30),
                'failed': self.config.get('failed_operation_retention_days', 90)
            },
            'sync_history': {
                'all': self.config.get('sync_history_retention_days', 30)
            },
            'cached_data': {
                'all': self.config.get('cache_retention_days', 7)
            }
        }
        
        # Thread control
        self.prune_thread = None
        self.stop_requested = False
    
    def start(self):
        """Start the automatic pruning thread"""
        if self.prune_thread is not None and self.prune_thread.is_alive():
            self.logger.warning("Prune thread already running")
            return
            
        if not self.auto_prune:
            self.logger.info("Auto-pruning is disabled")
            return
            
        self.stop_requested = False
        self.prune_thread = threading.Thread(target=self._prune_worker, daemon=True)
        self.prune_thread.start()
        self.logger.info("Data pruning manager started")
    
    def stop(self):
        """Signal the pruning thread to stop"""
        self.stop_requested = True
        self.logger.info("Stop requested for prune thread")
    
    def _prune_worker(self):
        """Background thread for periodic data pruning"""
        self.logger.info("Prune worker thread started")
        
        # If no previous prune time, set to now minus half the check frequency
        if not self.last_prune_time:
            self.last_prune_time = datetime.now() - timedelta(hours=self.check_frequency_hours/2)
        
        while not self.stop_requested:
            try:
                # Check if it's time to run pruning
                now = datetime.now()
                time_since_last = (now - self.last_prune_time).total_seconds() / 3600
                
                if time_since_last >= self.check_frequency_hours:
                    self.logger.info(f"Running scheduled data pruning ({time_since_last:.1f} hours since last)")
                    self.run_pruning()
                    self.last_prune_time = now
                
                # Sleep for a while before checking again
                for _ in range(60):  # Check every minute if we should stop
                    if self.stop_requested:
                        break
                    time.sleep(60)
                    
            except Exception as e:
                self.logger.error(f"Error in prune worker: {str(e)}", exc_info=True)
                time.sleep(3600)  # Wait an hour after an error
        
        self.logger.info("Prune worker thread stopped")
    
    def run_pruning(self, force=False):
        """Run a complete data pruning operation"""
        try:
            # Check database size first
            db_size_mb = self._get_database_size_mb()
            self.logger.info(f"Current database size: {db_size_mb:.2f} MB")
            
            # If database is small and we're not forcing, skip pruning
            if db_size_mb < self.max_db_size_mb and not force:
                self.logger.info(f"Database size is below threshold ({self.max_db_size_mb} MB), skipping pruning")
                return False
            
            # Otherwise proceed with pruning
            total_records_pruned = 0
            
            # Prune each table according to its policy
            total_records_pruned += self._prune_maintenance_history()
            total_records_pruned += self._prune_pending_operations()
            total_records_pruned += self._prune_sync_history()
            total_records_pruned += self._prune_cached_data()
            
            # Vacuum the database to reclaim space
            if total_records_pruned > 0:
                self._vacuum_database()
                
                # Get new database size
                new_db_size_mb = self._get_database_size_mb()
                space_saved = db_size_mb - new_db_size_mb
                
                self.logger.info(f"Pruning complete: {total_records_pruned} records removed, {space_saved:.2f} MB saved")
            else:
                self.logger.info("No records needed pruning")
                
            return total_records_pruned > 0
            
        except Exception as e:
            self.logger.error(f"Error during data pruning: {str(e)}", exc_info=True)
            return False
    
    def _prune_maintenance_history(self):
        """Prune old maintenance history records"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # Get cutoff dates
            now = datetime.now()
            completed_cutoff = now - timedelta(days=self.retention_policy['maintenance_history']['completed'])
            failed_cutoff = now - timedelta(days=self.retention_policy['maintenance_history']['failed'])
            
            # Delete completed maintenance records older than cutoff
            cursor.execute(
                "DELETE FROM maintenance_history WHERE synced = 1 AND timestamp < ?", 
                (completed_cutoff.isoformat(),)
            )
            completed_deleted = cursor.rowcount
            
            # Delete failed maintenance records older than cutoff
            cursor.execute(
                "DELETE FROM maintenance_history WHERE synced = -1 AND timestamp < ?", 
                (failed_cutoff.isoformat(),)
            )
            failed_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            total_deleted = completed_deleted + failed_deleted
            self.logger.info(f"Pruned {total_deleted} maintenance history records: {completed_deleted} completed, {failed_deleted} failed")
            
            return total_deleted
            
        except Exception as e:
            self.logger.error(f"Error pruning maintenance history: {str(e)}", exc_info=True)
            return 0
    
    def _prune_pending_operations(self):
        """Prune old pending operations"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # Get cutoff dates
            now = datetime.now()
            completed_cutoff = now - timedelta(days=self.retention_policy['pending_operations']['completed'])
            failed_cutoff = now - timedelta(days=self.retention_policy['pending_operations']['failed'])
            
            # Delete completed operations older than cutoff
            cursor.execute(
                "DELETE FROM pending_operations WHERE synced = 1 AND timestamp < ?", 
                (completed_cutoff.isoformat(),)
            )
            completed_deleted = cursor.rowcount
            
            # Delete failed operations older than cutoff
            cursor.execute(
                "DELETE FROM pending_operations WHERE synced = -1 AND timestamp < ?", 
                (failed_cutoff.isoformat(),)
            )
            failed_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            total_deleted = completed_deleted + failed_deleted
            self.logger.info(f"Pruned {total_deleted} pending operations: {completed_deleted} completed, {failed_deleted} failed")
            
            return total_deleted
            
        except Exception as e:
            self.logger.error(f"Error pruning pending operations: {str(e)}", exc_info=True)
            return 0
    
    def _prune_sync_history(self):
        """Prune old sync history records"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # Create the sync_history table if it doesn't exist
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_history (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                status TEXT,
                operations_count INTEGER,
                success_count INTEGER,
                duration_seconds REAL,
                details TEXT
            )
            """)
            
            # Get cutoff date
            cutoff = datetime.now() - timedelta(days=self.retention_policy['sync_history']['all'])
            
            # Delete sync history records older than cutoff
            cursor.execute(
                "DELETE FROM sync_history WHERE timestamp < ?", 
                (cutoff.isoformat(),)
            )
            deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Pruned {deleted} sync history records")
            return deleted
            
        except Exception as e:
            self.logger.error(f"Error pruning sync history: {str(e)}", exc_info=True)
            return 0
    
    def _prune_cached_data(self):
        """Prune old cached data"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # Get cutoff date
            cutoff = datetime.now() - timedelta(days=self.retention_policy['cached_data']['all'])
            
            # Delete cached data older than cutoff
            cursor.execute(
                "DELETE FROM cached_data WHERE timestamp < ?", 
                (cutoff.isoformat(),)
            )
            deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Pruned {deleted} cached data records")
            return deleted
            
        except Exception as e:
            self.logger.error(f"Error pruning cached data: {str(e)}", exc_info=True)
            return 0
    
    def _vacuum_database(self):
        """Vacuum the SQLite database to reclaim space"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            conn.execute("VACUUM")
            conn.close()
            self.logger.info("Database vacuumed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error vacuuming database: {str(e)}", exc_info=True)
            return False
    
    def _get_database_size_mb(self):
        """Get the size of the database file in MB"""
        try:
            size_bytes = os.path.getsize(self.db.db_path)
            size_mb = size_bytes / (1024 * 1024)
            return size_mb
        except Exception as e:
            self.logger.error(f"Error getting database size: {str(e)}", exc_info=True)
            return 0
    
    def get_database_stats(self):
        """Get statistics about the database"""
        try:
            stats = {
                'size_mb': self._get_database_size_mb(),
                'last_prune': self.last_prune_time.isoformat() if self.last_prune_time else None,
                'table_counts': {},
                'retention_policy': self.retention_policy
            }
            
            # Connect to database and get table statistics
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # Get a list of all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get count for each table
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    stats['table_counts'][table] = count
                except:
                    pass
            
            conn.close()
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting database stats: {str(e)}", exc_info=True)
            return {'error': str(e)}
