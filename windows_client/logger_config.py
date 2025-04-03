import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def is_portable_mode():
    """Check if the application is running in portable mode"""
    # Check if portable.txt exists in the same directory as the executable
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    portable_marker = os.path.join(exe_dir, "portable.txt")
    return os.path.exists(portable_marker)

def setup_logging(app_name="MaintenanceTrackerClient", log_level=logging.INFO):
    """Set up application logging"""
    
    # Determine log directory based on portable mode
    if is_portable_mode():
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        log_dir = Path(exe_dir) / "logs"
    else:
        log_dir = Path(os.path.expanduser("~"), ".amrs", "logs")
        
    log_dir.mkdir(exist_ok=True, parents=True)
    
    # Create log file path
    log_file = log_dir / f"{app_name}.log"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create and configure file handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,  # 5 MB max file size
        backupCount=3,         # Keep 3 backup files
        encoding='utf-8'
    )
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    file_handler.setLevel(log_level)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    console_handler.setLevel(logging.WARNING)  # Only warnings and above to console
    
    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log startup information
    logger = logging.getLogger("setup")
    logger.info(f"Starting logging to {log_file}")
    logger.info(f"Portable mode: {is_portable_mode()}")
    
    # Return the log file path for reference
    return log_file

def get_logger(name):
    """Get a logger with the given name"""
    return logging.getLogger(name)
