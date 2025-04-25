"""
Startup optimization utilities
"""
import os
import sys
import time
import logging
import sqlite3
import threading
from datetime import datetime
import json

class StartupOptimizer:
    """
    Provides tools for optimizing application startup
    """
    
    def __init__(self, config_manager, log_level=logging.INFO):
        """Initialize the startup optimizer"""
        self.config = config_manager
        
        self.logger = logging.getLogger("StartupOptimizer")
        self.logger.setLevel(log_level)
        
        # Options
        self.options = {
            'enabled': True,
            'preload_data': True,
            'cache_ui': True,
            'optimize_db': True,
            'lazy_load_components': True
        }
        
        # Load options from configuration
        self._load_options()
        
        # Startup statistics
        self.startup_times = {}
        self.preloaded_data = {}
        self.component_init_times = {}
    
    def _load_options(self):
        """Load optimization options from configuration"""
        if not self.config:
            return
            
        try:
            perf_config = self.config.get('performance', {})
            opt_config = perf_config.get('optimize_startup', {})
            
            if isinstance(opt_config, bool):
                # Simple boolean setting, use defaults with enabled/disabled
                self.options['enabled'] = opt_config
            elif isinstance(opt_config, dict):
                # Detailed settings
                for key in self.options:
                    if key in opt_config:
                        self.options[key] = opt_config[key]
                        
        except Exception as e:
            self.logger.error(f"Error loading startup optimization options: {e}")
    
    def measure(self, name):
        """
        Decorator to measure initialization time
        
        Args:
            name: Component name to measure
            
        Example:
            @startup_optimizer.measure("MainWindow")
            def __init__(self, ...):
                # Initialization code
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                if not self.options['enabled']:
                    return func(*args, **kwargs)
                    
                start_time = time.time()
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                
                # Store timing
                self.component_init_times[name] = elapsed
                self.logger.debug(f"Initialized {name} in {elapsed:.4f} seconds")
                
                return result
            return wrapper
        return decorator
    
    def start_measurement(self):
        """
        Start measuring total startup time
        Should be called at the beginning of the application startup
        """
        self.startup_times['start'] = time.time()
    
    def end_measurement(self):
        """
        End measuring total startup time
        Should be called when the application UI is fully loaded
        
        Returns:
            Total startup time in seconds
        """
        end_time = time.time()
        
        if 'start' in self.startup_times:
            total_time = end_time - self.startup_times['start']
            self.startup_times['total'] = total_time
            self.logger.info(f"Total startup time: {total_time:.4f} seconds")
            
            # Log breakdown
            if self.component_init_times:
                self.logger.info("Startup time breakdown:")
                for name, elapsed in sorted(self.component_init_times.items(), 
                                           key=lambda x: x[1], reverse=True):
                    self.logger.info(f"  - {name}: {elapsed:.4f} seconds ({(elapsed/total_time)*100:.1f}%)")
            
            # Save stats if configuration available
            if self.config:
                try:
                    startup_stats = self.config.get('startup_stats', [])
                    
                    # Add current stats
                    startup_stats.append({
                        'timestamp': datetime.now().isoformat(),
                        'total_time': total_time,
                        'components': self.component_init_times
                    })
                    
                    # Keep only last 10 entries
                    if len(startup_stats) > 10:
                        startup_stats = startup_stats[-10:]
                        
                    self.config.set('startup_stats', startup_stats)
                    
                except Exception as e:
                    self.logger.error(f"Error saving startup stats: {e}")
            
            return total_time
            
        return 0
    
    def preload_data(self, offline_db):
        """
        Preload common data in a background thread to improve responsiveness
        
        Args:
            offline_db: Offline database instance
        """
        if not self.options['enabled'] or not self.options['preload_data']:
            return
            
        try:
            thread = threading.Thread(target=self._do_preload_data, args=(offline_db,))
            thread.daemon = True
            thread.start()
            
            self.logger.debug("Started data preload in background thread")
            
        except Exception as e:
            self.logger.error(f"Error starting preload thread: {e}")
    
    def _do_preload_data(self, offline_db):
        """Worker function to preload data in background"""
        try:
            start_time = time.time()
            
            # Preload common data - these will be cached in the database connection
            preload_operations = [
                ("sites", offline_db.get_all_sites),
                ("machines", lambda: offline_db.get_all_machines(limit=100)),
                ("parts", lambda: offline_db.get_all_parts(limit=100)),
                ("maintenance_records", lambda: offline_db.get_maintenance_records_for_period(
                    datetime.now().strftime("%Y-%m-%d"), None, None, limit=50
                )),
                ("maintenance_schedules", offline_db.get_maintenance_schedules),
                ("sync_status", lambda: {
                    "pending_count": len(offline_db.get_pending_operations()), 
                    "failed_count": offline_db.get_failed_operations_count()
                })
            ]
            
            # Execute preload operations
            for name, operation in preload_operations:
                try:
                    item_start = time.time()
                    result = operation()
                    elapsed = time.time() - item_start
                    
                    # Store timing and count
                    count = len(result) if hasattr(result, "__len__") else 1
                    self.preloaded_data[name] = {
                        "time": elapsed,
                        "count": count
                    }
                    
                    self.logger.debug(f"Preloaded {name}: {count} items in {elapsed:.4f}s")
                    
                except Exception as e:
                    self.logger.error(f"Error preloading {name}: {e}")
                    
            # Calculate total time
            total_time = time.time() - start_time
            self.logger.info(f"Background data preload complete in {total_time:.4f}s")
            
        except Exception as e:
            self.logger.error(f"Error in data preload thread: {e}")
    
    def optimize_database(self, db_path):
        """
        Perform database optimizations for faster startup
        
        Args:
            db_path: Path to SQLite database file
            
        Returns:
            True if optimizations were applied, False otherwise
        """
        if not self.options['enabled'] or not self.options['optimize_db']:
            return False
            
        if not os.path.exists(db_path):
            return False
            
        try:
            start_time = time.time()
            self.logger.debug(f"Optimizing database: {db_path}")
            
            # Connect to database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Run PRAGMA optimizations
            optimizations = [
                "PRAGMA cache_size = 10000",  # Increase cache size
                "PRAGMA temp_store = MEMORY",  # Store temp tables in memory
                "PRAGMA synchronous = NORMAL",  # Slightly less safe but faster
                "PRAGMA journal_mode = WAL",   # Use Write-Ahead Logging
                "ANALYZE"                      # Update statistics
            ]
            
            for pragma in optimizations:
                cursor.execute(pragma)
            
            # Create indices for commonly queried fields if not exists
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_cached_data_type ON cached_data (type)",
                "CREATE INDEX IF NOT EXISTS idx_pending_operations_synced ON pending_operations (synced)",
                "CREATE INDEX IF NOT EXISTS idx_maintenance_history_part_id ON maintenance_history (part_id)",
                "CREATE INDEX IF NOT EXISTS idx_maintenance_history_timestamp ON maintenance_history (timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_maintenance_schedule_next_due ON maintenance_schedule (next_due)"
            ]
            
            for index_sql in indices:
                cursor.execute(index_sql)
            
            conn.commit()
            conn.close()
            
            elapsed = time.time() - start_time
            self.logger.info(f"Database optimizations applied in {elapsed:.4f} seconds")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error optimizing database: {e}")
            return False
    
    def get_optimization_stats(self):
        """
        Get optimization statistics
        
        Returns:
            Dictionary with optimization statistics
        """
        stats = {
            "enabled": self.options['enabled'],
            "options": self.options,
            "startup_time": self.startup_times.get('total', 0),
            "component_times": self.component_init_times,
            "preloaded_data": self.preloaded_data
        }
        
        return stats
    
    def generate_startup_report(self):
        """
        Generate a detailed startup report
        
        Returns:
            Report as formatted string
        """
        if not self.startup_times.get('total'):
            return "No startup measurements available"
            
        # Build report
        report = ["STARTUP PERFORMANCE REPORT", "=========================", ""]
        report.append(f"Total startup time: {self.startup_times['total']:.4f} seconds")
        report.append("")
        
        # Component breakdown
        report.append("Component Initialization Times:")
        report.append("-----------------------------")
        if self.component_init_times:
            sorted_components = sorted(self.component_init_times.items(), 
                                     key=lambda x: x[1], reverse=True)
            for name, elapsed in sorted_components:
                pct = (elapsed / self.startup_times['total']) * 100
                report.append(f"{name}: {elapsed:.4f}s ({pct:.1f}%)")
        else:
            report.append("No component measurements available")
        
        report.append("")
        
        # Preloaded data
        report.append("Preloaded Data:")
        report.append("--------------")
        if self.preloaded_data:
            for name, data in self.preloaded_data.items():
                report.append(f"{name}: {data['count']} items in {data['time']:.4f}s")
        else:
            report.append("No preloaded data measurements available")
        
        # Return as string
        return "\n".join(report)
