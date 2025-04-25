#!/usr/bin/env python
"""
AMRS Maintenance Tracker Launcher
This script launches the Windows client application with proper error handling
"""

import os
import sys
import logging
import traceback
from pathlib import Path

# Setup basic logging before anything else
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("Launcher")

def ensure_dependencies():
    """Check and ensure all required dependencies are installed"""
    required_packages = [
        "PyQt6", "PyQt6-WebEngine", "keyring", "requests", "cryptography",
        "psycopg2-binary"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.split('-')[0])  # Handle package names with dashes
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {', '.join(missing_packages)}")
        
        try:
            import pip
            for package in missing_packages:
                logger.info(f"Attempting to install {package}...")
                pip.main(['install', package])
        except Exception as e:
            logger.error(f"Failed to install missing packages: {e}")
            show_error_dialog("Missing Dependencies", 
                            f"The following required packages are missing: {', '.join(missing_packages)}\n\n" +
                            "Please install them manually using pip:\n" +
                            f"pip install {' '.join(missing_packages)}")
            return False
    
    return True

def show_error_dialog(title, message):
    """Show an error dialog using tkinter (no PyQt dependency)"""
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        messagebox.showerror(title, message)
        
        root.destroy()
    except Exception:
        # Fallback to console if tkinter is not available
        print(f"\nERROR: {title}\n{message}\n")

def setup_environment():
    """Setup environment variables and paths"""
    # Add the parent directory to the module search path
    parent_dir = Path(__file__).absolute().parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    # Setup environment variables
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    
    return True

def main():
    """Main entry point for the application launcher"""
    try:
        logger.info("Starting AMRS Maintenance Tracker Launcher")
        
        # Setup environment
        if not setup_environment():
            return 1
        
        # Ensure dependencies are installed
        if not ensure_dependencies():
            return 1
        
        # Import the application module
        from windows_client.application import main as app_main
        
        # Launch the application
        logger.info("Launching application...")
        app_main()
        
        return 0
        
    except Exception as e:
        error_msg = f"Failed to launch application: {str(e)}"
        error_details = traceback.format_exc()
        
        logger.critical(error_msg)
        logger.critical(error_details)
        
        show_error_dialog(
            "Launch Error",
            error_msg + "\n\nDetails:\n" + error_details
        )
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
