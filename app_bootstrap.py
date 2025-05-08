#!/usr/bin/env python
"""
Bootstrap script for AMRS Maintenance Tracker Windows WebView2 Application
This script ensures all required files and directories are available before
starting the Flask application
"""

import os
import sys
import argparse
import logging
import tempfile
import zipfile
import shutil
import subprocess
import threading
import time
import requests
import secrets
import base64
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[BOOTSTRAP] %(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("app_bootstrap")

# Application configuration
FLASK_PORT = 10000  # Default port
FLASK_URL = None  # Will be set based on the port
SERVER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py')

# Resource directories
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def setup_environment_variables():
    """Set up necessary environment variables for the application"""
    logger.info("Setting up environment variables")
    
    # Set development mode for Flask
    if 'FLASK_ENV' not in os.environ:
        os.environ['FLASK_ENV'] = 'development'
    
    # Set app mode to development
    if 'APP_MODE' not in os.environ:
        os.environ['APP_MODE'] = 'development'
    
    # Handle encryption key using secure key manager
    if 'USER_FIELD_ENCRYPTION_KEY' not in os.environ:
        try:
            # Import our key manager
            sys.path.insert(0, SCRIPT_DIR)
            from key_manager import get_or_create_encryption_key
            
            # Get the encryption key from the key manager
            encryption_key = get_or_create_encryption_key()
            if encryption_key:
                os.environ['USER_FIELD_ENCRYPTION_KEY'] = encryption_key
                logger.info("Retrieved encryption key from secure storage")
            else:
                logger.error("Failed to get encryption key - sync with server may not work")
                # Allow app to continue but with warnings - the models.py will show appropriate errors
        except ImportError:
            logger.error("Could not import key_manager module. Make sure it's in the application directory")
            # Continue without setting the key - the models.py file will handle the error situation

    # For packaged app, make sure we use SQLite if no DB URL is set
    if is_packaged_app() and 'DATABASE_URL' not in os.environ:
        # Create a data directory inside the user's home directory
        data_dir = os.path.join(os.path.expanduser('~'), '.amrs-maintenance-tracker')
        os.makedirs(data_dir, exist_ok=True)
        
        # Set SQLite database path
        db_path = os.path.join(data_dir, 'maintenance_tracker.db')
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
        logger.info(f"Using SQLite database at: {db_path}")

def is_packaged_app():
    """Check if running as a packaged application"""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if is_packaged_app():
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    
    return os.path.join(base_path, relative_path)

def setup_temp_directories():
    """Create temporary directories for templates and static files if needed"""
    temp_dir = tempfile.gettempdir()
    templates_dir = os.path.join(temp_dir, 'amrs_maintenance_tracker_templates')
    static_dir = os.path.join(temp_dir, 'amrs_maintenance_tracker_static')
    
    # Create directories if they don't exist
    os.makedirs(templates_dir, exist_ok=True)
    os.makedirs(static_dir, exist_ok=True)
    
    return templates_dir, static_dir

def extract_zip(zip_path, extract_to):
    """Extract a ZIP file to the specified directory"""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def extract_resources():
    """Extract resources from the packaged application to temporary directories"""
    if not is_packaged_app():
        # Not a packaged app, use existing directories
        logger.info("Running from source, using existing resource directories")
        return None, None
    
    # Set up temporary directories
    templates_dir, static_dir = setup_temp_directories()
    logger.info(f"Extracting resources to temp directories: {templates_dir}, {static_dir}")
    
    # Copy templates from the packaged app
    try:
        package_templates_dir = get_resource_path('templates')
        if os.path.exists(package_templates_dir):
            logger.info(f"Copying templates from {package_templates_dir} to {templates_dir}")
            for item in os.listdir(package_templates_dir):
                source = os.path.join(package_templates_dir, item)
                dest = os.path.join(templates_dir, item)
                if os.path.isdir(source):
                    shutil.copytree(source, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(source, dest)
    except Exception as e:
        logger.error(f"Error copying templates: {e}")
    
    # Copy static files from the packaged app
    try:
        package_static_dir = get_resource_path('static')
        if os.path.exists(package_static_dir):
            logger.info(f"Copying static files from {package_static_dir} to {static_dir}")
            for item in os.listdir(package_static_dir):
                source = os.path.join(package_static_dir, item)
                dest = os.path.join(static_dir, item)
                if os.path.isdir(source):
                    shutil.copytree(source, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(source, dest)
    except Exception as e:
        logger.error(f"Error copying static files: {e}")
    
    return templates_dir, static_dir

def start_flask_server(port, templates_dir=None, static_dir=None):
    """Start the Flask server with the specified port and resource directories"""
    global FLASK_URL
    FLASK_URL = f"http://localhost:{port}"
    
    # Set environment variables if using custom directories
    if templates_dir:
        os.environ['TEMPLATES_FOLDER'] = templates_dir
    if static_dir:
        os.environ['STATIC_FOLDER'] = static_dir
    
    # Import the Flask app
    sys.path.insert(0, SCRIPT_DIR)
    from app import app
    
    # Run the Flask app
    logger.info(f"Starting Flask application on port {port}")
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)

def main():
    """Main entry point for the bootstrap script"""
    parser = argparse.ArgumentParser(description="AMRS Maintenance Tracker Bootstrap")
    parser.add_argument('--port', type=int, default=FLASK_PORT, help='Port to run the Flask server on')
    args = parser.parse_args()
    
    port = args.port
    logger.info(f"Starting AMRS Maintenance Tracker bootstrap on port {port}")
    
    # Set up environment variables
    setup_environment_variables()
    
    # Extract resources if running as a packaged app
    templates_dir, static_dir = extract_resources()
    
    # Start the Flask server
    start_flask_server(port, templates_dir, static_dir)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())