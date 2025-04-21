"""
System health monitoring and analytics module.
Provides tools to analyze system performance and database health.
"""
import os
import logging
import sqlite3
from datetime import datetime, timedelta
import json
import base64
from io import BytesIO

# Try importing visualization libraries, make them optional
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False

class SystemHealthAnalytics:
    """
    Analytics for system health monitoring and diagnostics
    """
    
    def __init__(self, offline_db, diagnostics_manager=None):
        """
        Initialize with offline database and optional diagnostics manager
        """
        self.db = offline_db
        self.diagnostics = diagnostics_manager
        self.logger = logging.getLogger("SystemHealthAnalytics")
    
    def get_database_health(self):
        """
        Get database health statistics
        
        Returns:
            Dictionary with database health information
        """
        try:
            # Get database file path
            db_path = self.db.db_path
            
            # Check if file exists
            if not os.path.exists(db_path):
                return {
                    "status": "error",
                    "message": "Database file not found",
                    "file_path": db_path
                }
                
            # Get file size
            file_size = os.path.getsize(db_path)
            file_size_mb = file_size / (1024 * 1024)  # Convert to MB
            
            # Connect to database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get table information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            
            # Whitelist for allowed table names
            ALLOWED_TABLES = {'user', 'site', 'machine', 'part', 'maintenance_record', 'pending_operations', 'cached_data', 'notification_history', 'maintenance_schedule'}
            
            # Get row counts for each table
            table_stats = []
            total_rows = 0
            
            for table in table_names:
                if table not in ALLOWED_TABLES:
                    continue
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    row_count = cursor.fetchone()[0]
                    total_rows += row_count
                    
                    # Get size estimate of table (approximate)
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    
                    table_stats.append({
                        "name": table,
                        "rows": row_count,
                        "columns": len(columns),
                    })
                except sqlite3.Error as e:
                    self.logger.error(f"Error getting stats for table {table}: {str(e)}")
            
            # Get integrity check
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            
            # Get database page size and count
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            
            # Calculate fragmentation stats (based on pages)
            cursor.execute("PRAGMA freelist_count")
            freelist_count = cursor.fetchone()[0]
            
            fragmentation_percent = (freelist_count / page_count) * 100 if page_count > 0 else 0
            
            conn.close()
            
            # Determine health status
            status = "good"
            warnings = []
            
            if file_size_mb > 100:  # Database is large (>100 MB)
                status = "warning"
                warnings.append(f"Database size ({file_size_mb:.2f} MB) is large")
                
            if fragmentation_percent > 20:  # High fragmentation
                status = "warning"
                warnings.append(f"Database fragmentation is high ({fragmentation_percent:.2f}%)")
                
            if integrity != "ok":
                status = "error"
                warnings.append(f"Database integrity check failed: {integrity}")
            
            # Return all gathered information
            return {
                "status": status,
                "database_path": db_path,
                "file_size_bytes": file_size,
                "file_size_mb": file_size_mb,
                "total_tables": len(table_names),
                "total_rows": total_rows,
                "integrity": integrity,
                "page_size": page_size,
                "page_count": page_count,
                "fragmentation": {
                    "free_pages": freelist_count,
                    "percent": fragmentation_percent
                },
                "tables": table_stats,
                "warnings": warnings,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in database health check: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to check database health: {str(e)}",
                "file_path": getattr(self.db, 'db_path', 'unknown')
            }
    
    def get_sync_health(self):
        """
        Get synchronization health statistics
        
        Returns:
            Dictionary with sync health information
        """
        try:
            # Get pending operations count
            pending_ops = self.db.get_pending_operations()
            pending_count = len(pending_ops) if pending_ops else 0
            
            # Get failed operations count
            failed_count = self.db.get_failed_operations_count()
            
            # Get sync history
            sync_history = self.db.get_sync_history(limit=10)
            
            # Calculate success rate
            success_rate = 0
            if sync_history:
                success_count = sum(1 for entry in sync_history if entry.get('status') == 'success')
                success_rate = (success_count / len(sync_history)) * 100
            
            # Determine last successful sync
            last_successful = None
            for entry in sync_history:
                if entry.get('status') == 'success':
                    last_successful = entry.get('timestamp')
                    break
            
            # Determine overall status
            status = "good"
            warnings = []
            
            if pending_count > 100:
                status = "warning"
                warnings.append(f"Large number of pending operations ({pending_count})")
                
            if failed_count > 0:
                status = "warning"
                warnings.append(f"Failed operations detected ({failed_count})")
                
            if success_rate < 50:
                status = "error"
                warnings.append(f"Low sync success rate ({success_rate:.1f}%)")
                
            if not last_successful:
                status = "error"
                warnings.append("No successful synchronization found in history")
            elif last_successful:
                try:
                    last_sync_dt = datetime.fromisoformat(last_successful)
                    days_since = (datetime.now() - last_sync_dt).days
                    
                    if days_since > 7:
                        status = "error"
                        warnings.append(f"No successful sync in {days_since} days")
                    elif days_since > 2:
                        status = "warning"
                        warnings.append(f"No successful sync in {days_since} days")
                except (ValueError, TypeError):
                    pass
            
            # Return all gathered information
            return {
                "status": status,
                "pending_operations": pending_count,
                "failed_operations": failed_count,
                "success_rate": success_rate,
                "last_successful_sync": last_successful,
                "recent_history": sync_history,
                "warnings": warnings,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in sync health check: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to check sync health: {str(e)}"
            }
    
    def get_performance_chart(self, days=7):
        """
        Generate a performance chart for the past days
        
        Args:
            days: Number of days to include in the chart
            
        Returns:
            Base64 encoded PNG image of the chart
        """
        if not PLOTTING_AVAILABLE:
            self.logger.warning("Plotting libraries not available")
            return None
            
        if not self.diagnostics:
            return None
            
        # Get metrics from diagnostics
        metrics = self.diagnostics.metrics
        
        # Extract data for plotting
        timestamps = []
        cpu_data = []
        memory_data = []
        
        # Find the cutoff point for the specified days
        cutoff = datetime.now() - timedelta(days=days)
        
        # Convert metrics to time series data
        # This implementation depends on how diagnostics stores metrics
        # Here's a generic approach that should be adapted to the actual data structure
        
        # For this example, I'll assume diagnostics.get_metrics_history() returns a list
        # of timestamped metrics
        try:
            metrics_history = self.diagnostics.get_metrics_history()
            
            for entry in metrics_history:
                try:
                    entry_time = datetime.fromisoformat(entry.get('timestamp'))
                    if entry_time >= cutoff:
                        timestamps.append(entry_time)
                        cpu_data.append(entry.get('app_cpu_percent', 0))
                        memory_data.append(entry.get('app_memory_mb', 0))
                except (ValueError, TypeError, AttributeError):
                    continue
                    
        except AttributeError:
            # If get_metrics_history doesn't exist, use the current metrics structure
            # This is a fallback that creates a chart with the current data point only
            now = datetime.now()
            cpu_avg = sum(metrics.get('app_cpu_percent', [0])) / len(metrics.get('app_cpu_percent', [1]))
            memory_avg = sum(metrics.get('app_memory_mb', [0])) / len(metrics.get('app_memory_mb', [1]))
            
            timestamps = [now]
            cpu_data = [cpu_avg]
            memory_data = [memory_avg]
        
        # If we have no data, return None
        if not timestamps:
            return None
            
        # Create the plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
        
        # CPU usage plot
        ax1.plot(timestamps, cpu_data, 'b-', label='CPU Usage')
        ax1.set_ylabel('CPU (%)')
        ax1.set_title('Application Performance')
        ax1.grid(True)
        ax1.legend()
        
        # Memory usage plot
        ax2.plot(timestamps, memory_data, 'g-', label='Memory Usage')
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Memory (MB)')
        ax2.grid(True)
        ax2.legend()
        
        plt.tight_layout()
        
        # Convert plot to base64 image
        buffer = BytesIO()
        fig.savefig(buffer, format='png')
        buffer.seek(0)
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close(fig)
        
        return image_data
    
    def optimize_database(self):
        """
        Optimize the SQLite database to improve performance
        
        Returns:
            Dictionary with optimization results
        """
        try:
            # Get initial database size
            db_path = self.db.db_path
            initial_size = os.path.getsize(db_path) / (1024 * 1024)  # MB
            
            # Connect to database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Run VACUUM to rebuild the database file
            cursor.execute("VACUUM")
            
            # Run ANALYZE to update statistics
            cursor.execute("ANALYZE")
            
            # Optimize indices
            cursor.execute("PRAGMA optimize")
            
            conn.close()
            
            # Get new database size
            final_size = os.path.getsize(db_path) / (1024 * 1024)  # MB
            
            # Calculate space saved
            space_saved = initial_size - final_size
            percent_saved = (space_saved / initial_size) * 100 if initial_size > 0 else 0
            
            return {
                "status": "success",
                "initial_size_mb": initial_size,
                "final_size_mb": final_size,
                "space_saved_mb": space_saved,
                "percent_saved": percent_saved,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizing database: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to optimize database: {str(e)}"
            }
