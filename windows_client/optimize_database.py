"""
Database optimization utilities for improved performance
"""
import os
import time
import logging
import sqlite3
import threading
from datetime import datetime, timedelta

class DatabaseOptimizer:
    """
    Provides tools for optimizing the SQLite database
    """
    
    def __init__(self, db_path, config_manager=None):
        """
        Initialize the database optimizer
        
        Args:
            db_path: Path to SQLite database file
            config_manager: Optional configuration manager
        """
        self.db_path = db_path
        self.config = config_manager
        self.logger = logging.getLogger("DatabaseOptimizer")
        
        # Default options
        self.options = {
            'auto_optimize': True,
            'optimize_interval': 86400,  # Optimize every 24 hours
            'vacuum_threshold': 10,      # MB of free space to trigger VACUUM
            'max_wal_size': 1048576,     # 1MB before checkpointing WAL
            'auto_checkpoint': True,
            'aggressive_journal_mode': False,
            'auto_analyze': True,
            'pruning_enabled': True,
            'pruning_keep_days': 90,     # Number of days to keep old data
            'cache_size': 2000           # Default cache size in pages
        }
        
        # Statistics
        self.optimization_history = []
        self.last_optimize_time = None
        
        # Load options
        self._load_options()
        
        # Schedule optimization if auto-optimize is enabled
        if self.options['auto_optimize']:
            self._schedule_optimization()
    
    def _load_options(self):
        """Load optimization options from configuration"""
        if not self.config:
            return
            
        try:
            db_options = self.config.get('database_optimization', {})
            
            # Update options with configuration values
            for key in self.options:
                if key in db_options:
                    self.options[key] = db_options[key]
                    
            # Load optimization history
            history = self.config.get('optimization_history', [])
            if history:
                self.optimization_history = history
                
                # Set last optimize time if available
                if history and isinstance(history[-1], dict) and 'timestamp' in history[-1]:
                    try:
                        self.last_optimize_time = datetime.fromisoformat(history[-1]['timestamp'])
                    except (ValueError, TypeError):
                        pass
                        
        except Exception as e:
            self.logger.error(f"Error loading database optimization options: {e}")
    
    def _save_options(self):
        """Save optimization options to configuration"""
        if not self.config:
            return
            
        try:
            # Save options
            self.config.set('database_optimization', self.options)
            
            # Save history (limit to last 10 entries)
            self.config.set('optimization_history', self.optimization_history[-10:] if self.optimization_history else [])
            
        except Exception as e:
            self.logger.error(f"Error saving database optimization options: {e}")
    
    def _schedule_optimization(self):
        """Schedule periodic optimization"""
        # Calculate next run time
        next_run = None
        
        if self.last_optimize_time:
            # Schedule based on interval since last run
            interval = timedelta(seconds=self.options['optimize_interval'])
            next_run = self.last_optimize_time + interval
            
        if not next_run or next_run <= datetime.now():
            # If never run or past due, schedule soon but not immediately
            next_run = datetime.now() + timedelta(minutes=5)
            
        # Start timer thread
        seconds_until_run = (next_run - datetime.now()).total_seconds()
        
        timer = threading.Timer(max(1, seconds_until_run), self._run_scheduled_optimization)
        timer.daemon = True
        timer.start()
        
        self.logger.debug(f"Scheduled database optimization in {seconds_until_run:.1f} seconds")
    
    def _run_scheduled_optimization(self):
        """Run the scheduled optimization"""
        try:
            # Check if database exists
            if not os.path.exists(self.db_path):
                self.logger.warning(f"Database file not found: {self.db_path}")
                return
                
            # Run optimization
            self.optimize_database(scheduled=True)
            
            # Schedule next optimization
            self._schedule_optimization()
            
        except Exception as e:
            self.logger.error(f"Error in scheduled optimization: {e}")
            
            # Try to reschedule despite error
            try:
                self._schedule_optimization()
            except:
                pass
    
    def optimize_database(self, full_vacuum=False, scheduled=False):
        """
        Optimize the database for better performance
        
        Args:
            full_vacuum: Whether to run VACUUM (expensive but reclaims space)
            scheduled: Whether this is a scheduled optimization
            
        Returns:
            Dictionary with optimization results
        """
        if not os.path.exists(self.db_path):
            return {"status": "error", "message": "Database file not found"}
            
        start_time = time.time()
        results = {"status": "success", "optimizations": []}
        
        try:
            self.logger.info(f"Starting database optimization (vacuum={full_vacuum})")
            
            # Get initial database size
            initial_size = os.path.getsize(self.db_path) / (1024 * 1024)  # MB
            results["initial_size_mb"] = initial_size
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get database fragmentation info
            try:
                cursor.execute("PRAGMA page_count")
                page_count = cursor.fetchone()[0]
                
                cursor.execute("PRAGMA page_size")
                page_size = cursor.fetchone()[0]
                
                cursor.execute("PRAGMA freelist_count")
                freelist_count = cursor.fetchone()[0]
                
                db_size_pages = page_count
                free_pages = freelist_count
                fragmentation_pct = (free_pages / db_size_pages) * 100 if db_size_pages > 0 else 0
                
                results["fragmentation_before"] = {
                    "page_count": page_count,
                    "page_size": page_size,
                    "free_pages": free_pages,
                    "fragmentation_pct": fragmentation_pct
                }
            except Exception as e:
                self.logger.error(f"Error getting database info: {e}")
                
            # Apply optimizations
            optimizations = []
            
            # Apply performance PRAGMAs
            cursor.execute(f"PRAGMA cache_size = {self.options['cache_size']}")
            optimizations.append("Set cache size")
            
            cursor.execute("PRAGMA temp_store = MEMORY")
            optimizations.append("Set temp store to memory")
            
            if self.options['aggressive_journal_mode']:
                cursor.execute("PRAGMA journal_mode = MEMORY")
                optimizations.append("Set aggressive journal mode (MEMORY)")
            else:
                cursor.execute("PRAGMA journal_mode = WAL")
                optimizations.append("Set journal mode to WAL")
                
                if self.options['auto_checkpoint']:
                    cursor.execute(f"PRAGMA wal_autocheckpoint = {self.options['max_wal_size']}")
                    optimizations.append(f"Set WAL autocheckpoint size to {self.options['max_wal_size']}")
            
            # Always update statistics
            cursor.execute("ANALYZE")
            optimizations.append("Updated statistics (ANALYZE)")
            
            # Run integrity check
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            results["integrity_check"] = integrity
            
            # Check if vacuum is needed
            need_vacuum = full_vacuum
            
            if not need_vacuum and self.options['vacuum_threshold'] > 0:
                # Calculate free space in MB
                free_space_mb = (free_pages * page_size) / (1024 * 1024)
                
                # Vacuum if free space exceeds threshold
                if free_space_mb >= self.options['vacuum_threshold']:
                    need_vacuum = True
                    
                    results["vacuum_reason"] = f"Free space ({free_space_mb:.2f} MB) exceeds threshold ({self.options['vacuum_threshold']} MB)"
            
            # Run vacuum if needed
            if need_vacuum:
                vacuum_start = time.time()
                cursor.execute("VACUUM")
                vacuum_time = time.time() - vacuum_start
                
                optimizations.append(f"Rebuilt database (VACUUM) in {vacuum_time:.2f}s")
                results["vacuum_time"] = vacuum_time
            
            # Clean up data if pruning is enabled
            if self.options['pruning_enabled'] and self.options['pruning_keep_days'] > 0:
                pruning_results = self._prune_old_data(conn)
                if pruning_results.get('pruned_count', 0) > 0:
                    optimizations.append(f"Pruned {pruning_results['pruned_count']} old records")
                    results["pruning"] = pruning_results
            
            # Get final database info
            try:
                cursor.execute("PRAGMA page_count")
                final_page_count = cursor.fetchone()[0]
                
                cursor.execute("PRAGMA freelist_count")
                final_freelist_count = cursor.fetchone()[0]
                
                fragmentation_pct = (final_freelist_count / final_page_count) * 100 if final_page_count > 0 else 0
                
                results["fragmentation_after"] = {
                    "page_count": final_page_count,
                    "free_pages": final_freelist_count,
                    "fragmentation_pct": fragmentation_pct
                }
            except Exception as e:
                self.logger.error(f"Error getting final database info: {e}")
                
            # Commit changes
            conn.commit()
            conn.close()
            
            # Get final size
            final_size = os.path.getsize(self.db_path) / (1024 * 1024)  # MB
            results["final_size_mb"] = final_size
            results["size_change_mb"] = initial_size - final_size
            results["size_change_pct"] = ((initial_size - final_size) / initial_size) * 100 if initial_size > 0 else 0
            
            # Record optimizations
            results["optimizations"] = optimizations
            
            # Record total time
            elapsed_time = time.time() - start_time
            results["elapsed_time"] = elapsed_time
            
            # Log results
            self.logger.info(f"Database optimization complete in {elapsed_time:.2f}s. Size change: {initial_size - final_size:.2f} MB")
            
            # Update history
            self.last_optimize_time = datetime.now()
            
            history_entry = {
                "timestamp": self.last_optimize_time.isoformat(),
                "elapsed_time": elapsed_time,
                "initial_size_mb": initial_size,
                "final_size_mb": final_size,
                "vacuum_performed": need_vacuum,
                "fragmentation_before": results.get("fragmentation_before", {}).get("fragmentation_pct", 0),
                "fragmentation_after": results.get("fragmentation_after", {}).get("fragmentation_pct", 0)
            }
            
            self.optimization_history.append(history_entry)
            
            # Save options and history
            self._save_options()
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error optimizing database: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "elapsed_time": time.time() - start_time
            }
    
    def _prune_old_data(self, conn):
        """
        Prune old data from the database
        
        Args:
            conn: SQLite connection
            
        Returns:
            Dictionary with pruning results
        """
        results = {"pruned_count": 0}
        
        try:
            cursor = conn.cursor()
            
            # Calculate cutoff date
            cutoff_days = self.options['pruning_keep_days']
            cutoff_date = (datetime.now() - timedelta(days=cutoff_days)).isoformat()
            
            # Tables with timestamp fields
            tables_to_prune = [
                {"name": "maintenance_history", "timestamp_field": "timestamp"},
                {"name": "notification_history", "timestamp_field": "timestamp"}, 
                {"name": "cached_data", "timestamp_field": "last_updated"},
                {"name": "sync_history", "timestamp_field": "timestamp"}
            ]
            
            total_pruned = 0
            
            # Prune each table
            for table in tables_to_prune:
                name = table["name"]
                timestamp_field = table["timestamp_field"]
                
                try:
                    # Check if table exists
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{name}'")
                    if not cursor.fetchone():
                        continue
                        
                    # Check if timestamp field exists
                    cursor.execute(f"PRAGMA table_info({name})")
                    columns = cursor.fetchall()
                    if timestamp_field not in [col[1] for col in columns]:
                        continue
                        
                    # Delete old records
                    cursor.execute(f"DELETE FROM {name} WHERE {timestamp_field} < ?", (cutoff_date,))
                    pruned_count = cursor.rowcount
                    
                    if pruned_count > 0:
                        results[name] = pruned_count
                        total_pruned += pruned_count
                        
                except Exception as e:
                    self.logger.error(f"Error pruning table {name}: {e}")
            
            results["pruned_count"] = total_pruned
            
            if total_pruned > 0:
                self.logger.info(f"Pruned {total_pruned} old records from database")
                
            return results
            
        except Exception as e:
            self.logger.error(f"Error pruning database: {e}")
            return {"pruned_count": 0, "error": str(e)}
    
    def get_optimization_stats(self):
        """
        Get database optimization statistics
        
        Returns:
            Dictionary with optimization statistics
        """
        stats = {
            "options": self.options,
            "last_optimize_time": self.last_optimize_time.isoformat() if self.last_optimize_time else None,
            "optimization_count": len(self.optimization_history),
            "recent_optimizations": self.optimization_history[-5:] if self.optimization_history else []
        }
        
        # Add current database info
        if os.path.exists(self.db_path):
            try:
                # Get database size
                stats["current_size_mb"] = os.path.getsize(self.db_path) / (1024 * 1024)
                
                # Get detailed info
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("PRAGMA page_count")
                page_count = cursor.fetchone()[0]
                
                cursor.execute("PRAGMA page_size")
                page_size = cursor.fetchone()[0]
                
                cursor.execute("PRAGMA freelist_count")
                freelist_count = cursor.fetchone()[0]
                
                fragmentation_pct = (freelist_count / page_count) * 100 if page_count > 0 else 0
                
                stats["fragmentation"] = {
                    "page_count": page_count,
                    "page_size": page_size,
                    "free_pages": freelist_count,
                    "fragmentation_pct": fragmentation_pct
                }
                
                # Get table sizes
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                table_stats = []
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    table_stats.append({
                        "name": table_name,
                        "rows": row_count
                    })
                
                stats["tables"] = table_stats
                
                conn.close()
                
            except Exception as e:
                self.logger.error(f"Error getting database stats: {e}")
                stats["error"] = str(e)
        
        return stats
    
    def update_option(self, option, value):
        """
        Update an optimization option
        
        Args:
            option: Option name
            value: New value
            
        Returns:
            True if option was updated, False otherwise
        """
        if option not in self.options:
            return False
            
        self.options[option] = value
        self._save_options()
        
        return True
