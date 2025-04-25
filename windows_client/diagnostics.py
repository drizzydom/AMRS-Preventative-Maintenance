import os
import sys
import time
import logging
import platform
import threading
import json
import sqlite3
import traceback
import psutil
from datetime import datetime
from pathlib import Path

class DiagnosticsManager:
    """
    Manages system diagnostics, performance monitoring, and error reporting
    for the Windows client application
    """
    
    def __init__(self, config=None, app_data_dir=None):
        self.config = config or {}
        
        # Set up app data directory
        if app_data_dir:
            self.app_data_dir = Path(app_data_dir)
        else:
            # Default to user's app data directory
            self.app_data_dir = Path(os.path.expanduser('~')) / '.amrs'
        
        # Ensure directory exists
        os.makedirs(self.app_data_dir, exist_ok=True)
        
        # Set up logs directory
        self.logs_dir = self.app_data_dir / 'logs'
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Set up diagnostics report directory
        self.reports_dir = self.app_data_dir / 'reports'
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger("Diagnostics")
        handler = logging.FileHandler(self.logs_dir / "diagnostics.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Configuration with defaults
        self.perf_monitoring_interval = self.config.get('perf_monitoring_interval', 60)  # seconds
        self.collect_system_metrics = self.config.get('collect_system_metrics', True)
        self.error_report_enabled = self.config.get('error_report_enabled', True)
        self.log_rotation_days = self.config.get('log_rotation_days', 7)
        
        # Metrics storage
        self.metrics = {
            'app_cpu_percent': [],
            'app_memory_mb': [],
            'system_cpu_percent': [],
            'system_memory_percent': [],
            'disk_usage_percent': []
        }
        
        # Process tracking
        self.process = psutil.Process(os.getpid())
        
        # Thread control
        self.monitor_thread = None
        self.stop_requested = False
        
        # Register exception handler
        if self.error_report_enabled:
            self._register_exception_handler()
        
        self.logger.info(f"Diagnostics manager initialized in {self.app_data_dir}")
    
    def start_monitoring(self):
        """Start performance monitoring thread"""
        if self.monitor_thread is not None and self.monitor_thread.is_alive():
            self.logger.warning("Monitor thread already running")
            return
            
        if not self.collect_system_metrics:
            self.logger.info("System metrics collection is disabled")
            return
            
        self.stop_requested = False
        self.monitor_thread = threading.Thread(target=self._monitor_worker, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Signal the monitoring thread to stop"""
        self.stop_requested = True
        self.logger.info("Stop requested for monitor thread")
    
    def _monitor_worker(self):
        """Background thread for collecting performance metrics"""
        self.logger.info("Performance monitoring thread started")
        
        while not self.stop_requested:
            try:
                # Collect metrics
                self._collect_metrics()
                
                # Sleep for the configured interval
                time.sleep(self.perf_monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitor thread: {str(e)}", exc_info=True)
                time.sleep(300)  # Wait 5 minutes after an error
        
        self.logger.info("Performance monitoring thread stopped")
    
    def _collect_metrics(self):
        """Collect performance metrics"""
        try:
            # App CPU and memory usage
            app_cpu = self.process.cpu_percent(interval=0.5)
            app_memory = self.process.memory_info().rss / (1024 * 1024)  # Convert to MB
            
            # System metrics
            system_cpu = psutil.cpu_percent(interval=0.5)
            system_memory = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/').percent
            
            # Add to metrics (keep last 1000 data points)
            self.metrics['app_cpu_percent'].append(app_cpu)
            self.metrics['app_memory_mb'].append(app_memory)
            self.metrics['system_cpu_percent'].append(system_cpu)
            self.metrics['system_memory_percent'].append(system_memory)
            self.metrics['disk_usage_percent'].append(disk_usage)
            
            # Truncate metrics to last 1000 data points
            for key in self.metrics:
                if len(self.metrics[key]) > 1000:
                    self.metrics[key] = self.metrics[key][-1000:]
                    
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {str(e)}")
    
    def _register_exception_handler(self):
        """Register a global exception handler"""
        def exception_handler(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                # Let KeyboardInterrupt pass through
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
                
            self.logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
            self.create_error_report(exc_type, exc_value, exc_traceback)
        
        # Set the exception hook
        sys.excepthook = exception_handler
        self.logger.info("Global exception handler registered")
    
    def create_error_report(self, exc_type=None, exc_value=None, exc_traceback=None):
        """Create a detailed error report"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = self.reports_dir / f"error_report_{timestamp}.json"
            
            # Basic report data
            report = {
                "timestamp": datetime.now().isoformat(),
                "application": {
                    "name": "AMRS Maintenance Tracker",
                    "version": self.config.get('app_version', 'unknown'),
                    "python_version": platform.python_version(),
                    "platform": platform.platform()
                },
                "system": {
                    "platform": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "architecture": platform.architecture(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                    "disk_free_gb": round(psutil.disk_usage('/').free / (1024**3), 2)
                },
                "metrics": {
                    "app_cpu_percent": self.metrics['app_cpu_percent'][-10:] if self.metrics['app_cpu_percent'] else [],
                    "app_memory_mb": self.metrics['app_memory_mb'][-10:] if self.metrics['app_memory_mb'] else [],
                    "system_cpu_percent": self.metrics['system_cpu_percent'][-10:] if self.metrics['system_cpu_percent'] else [],
                    "system_memory_percent": self.metrics['system_memory_percent'][-10:] if self.metrics['system_memory_percent'] else []
                }
            }
            
            # Add exception details if provided
            if exc_type and exc_value:
                report["error"] = {
                    "type": exc_type.__name__,
                    "message": str(exc_value),
                    "traceback": traceback.format_exception(exc_type, exc_value, exc_traceback) if exc_traceback else None
                }
            
            # Save the report
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
                
            self.logger.info(f"Error report created at {report_path}")
            return report_path
            
        except Exception as e:
            self.logger.error(f"Error creating error report: {str(e)}", exc_info=True)
            return None
    
    def create_diagnostics_report(self):
        """Create a comprehensive diagnostics report"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = self.reports_dir / f"diagnostics_{timestamp}.json"
            
            # Collect system information
            system_info = {
                "platform": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "architecture": platform.architecture(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "python_implementation": platform.python_implementation()
            }
            
            # Collect memory information
            memory = psutil.virtual_memory()
            memory_info = {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent_used": memory.percent
            }
            
            # Collect disk information
            disk = psutil.disk_usage('/')
            disk_info = {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent_used": disk.percent
            }
            
            # Collect network information
            try:
                net_io = psutil.net_io_counters()
                net_info = {
                    "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
                    "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                    "errin": net_io.errin,
                    "errout": net_io.errout,
                    "dropin": net_io.dropin,
                    "dropout": net_io.dropout
                }
            except:
                net_info = {"error": "Unable to collect network information"}
            
            # Collect application metrics
            app_metrics = {
                "cpu_percent": self.metrics['app_cpu_percent'][-100:] if self.metrics['app_cpu_percent'] else [],
                "memory_mb": self.metrics['app_memory_mb'][-100:] if self.metrics['app_memory_mb'] else [],
                "uptime_seconds": time.time() - self.process.create_time()
            }
            
            # Collect log statistics
            log_files = list(self.logs_dir.glob("*.log"))
            log_stats = [{
                "filename": log_file.name,
                "size_kb": round(log_file.stat().st_size / 1024, 2),
                "modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
            } for log_file in log_files]
            
            # Combine all information into a report
            report = {
                "timestamp": datetime.now().isoformat(),
                "application": {
                    "name": "AMRS Maintenance Tracker",
                    "version": self.config.get('app_version', 'unknown'),
                    "metrics": app_metrics
                },
                "system": system_info,
                "memory": memory_info,
                "disk": disk_info,
                "network": net_info,
                "logs": log_stats
            }
            
            # Save the report
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
                
            self.logger.info(f"Diagnostics report created at {report_path}")
            return report_path
            
        except Exception as e:
            self.logger.error(f"Error creating diagnostics report: {str(e)}", exc_info=True)
            return None
    
    def rotate_logs(self):
        """Rotate log files older than the configured retention period"""
        try:
            cutoff_time = time.time() - (self.log_rotation_days * 24 * 60 * 60)
            log_files = list(self.logs_dir.glob("*.log"))
            rotated_count = 0
            
            for log_file in log_files:
                # Skip current log files
                if log_file.name in ["diagnostics.log", "sync_manager.log", "offline_db.log"]:
                    continue
                    
                # Check if file is older than cutoff
                if log_file.stat().st_mtime < cutoff_time:
                    # Create rotated filename with date
                    modified_date = datetime.fromtimestamp(log_file.stat().st_mtime)
                    date_str = modified_date.strftime('%Y%m%d')
                    rotated_name = f"{log_file.stem}_{date_str}.log.old"
                    
                    # Rename the file
                    log_file.rename(self.logs_dir / rotated_name)
                    rotated_count += 1
            
            self.logger.info(f"Rotated {rotated_count} log files")
            return rotated_count
            
        except Exception as e:
            self.logger.error(f"Error rotating logs: {str(e)}", exc_info=True)
            return 0
    
    def clean_old_reports(self, days=30):
        """Remove diagnostics reports older than specified days"""
        try:
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            report_files = list(self.reports_dir.glob("*.json"))
            removed_count = 0
            
            for report_file in report_files:
                # Check if file is older than cutoff
                if report_file.stat().st_mtime < cutoff_time:
                    # Remove the file
                    report_file.unlink()
                    removed_count += 1
            
            self.logger.info(f"Removed {removed_count} old report files")
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning old reports: {str(e)}", exc_info=True)
            return 0
    
    def get_metrics_summary(self):
        """Get a summary of collected metrics"""
        summary = {}
        
        for metric_name, values in self.metrics.items():
            if not values:
                summary[metric_name] = {"avg": 0, "min": 0, "max": 0}
                continue
                
            avg = sum(values) / len(values)
            min_val = min(values)
            max_val = max(values)
            
            summary[metric_name] = {
                "avg": round(avg, 2),
                "min": round(min_val, 2),
                "max": round(max_val, 2),
                "current": round(values[-1], 2) if values else 0
            }
        
        return summary
