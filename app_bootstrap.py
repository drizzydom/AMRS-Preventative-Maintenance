#!/usr/bin/env python
"""
Bootstrap script for AMRS Maintenance Tracker Windows WebView2 Application
This script ensures all required files and directories are available before
starting the Flask application
"""

import os
# Load .env file as early as possible
from dotenv import load_dotenv
import sys

# Determine the directory to look for .env
if getattr(sys, 'frozen', False):
    # Running as a PyInstaller bundle
    exe_dir = os.path.dirname(sys.executable)
else:
    exe_dir = os.path.dirname(os.path.abspath(__file__))

# Always look for .env in the _internal folder next to the executable
internal_dir = os.path.join(exe_dir, '_internal')
dotenv_path = os.path.join(internal_dir, '.env')
print(f"[BOOTSTRAP] Looking for .env at: {dotenv_path}")
load_dotenv(dotenv_path)
if not os.path.exists(dotenv_path):
    print(f"[BOOTSTRAP] .env file not found at {dotenv_path}. Using environment variables.")
else:
    print(f"[BOOTSTRAP] .env file loaded from {dotenv_path}")
    # Secure the .env file on Windows so only the current user can read/write
    if os.name == 'nt':
        try:
            import win32security
            import ntsecuritycon as con
            import win32api
            import win32con
            user, domain, type = win32security.LookupAccountName('', win32api.GetUserName())
            sd = win32security.GetFileSecurity(dotenv_path, win32security.DACL_SECURITY_INFORMATION)
            dacl = win32security.ACL()
            dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_GENERIC_READ | con.FILE_GENERIC_WRITE, user)
            sd.SetSecurityDescriptorDacl(1, dacl, 0)
            win32security.SetFileSecurity(dotenv_path, win32security.DACL_SECURITY_INFORMATION, sd)
            print(f"[BOOTSTRAP] Secured .env file permissions for user: {win32api.GetUserName()}")
        except Exception as e:
            print(f"[BOOTSTRAP] Warning: Could not set .env file permissions: {e}")

# After loading dotenv, print the value for debugging
print("[BOOTSTRAP] USER_FIELD_ENCRYPTION_KEY from env:", os.environ.get("USER_FIELD_ENCRYPTION_KEY"))

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
    
    # Only use environment variable for encryption key
    if 'USER_FIELD_ENCRYPTION_KEY' not in os.environ:
        logger.error("USER_FIELD_ENCRYPTION_KEY environment variable not set. Set this variable before starting the application.")
        sys.exit(1)

    # For packaged app, make sure we use SQLite if no DB URL is set
    if 'DATABASE_URL' not in os.environ:
        # Create a data directory inside the user's home directory
        data_dir = os.path.join(os.path.expanduser('~'), '.amrs-maintenance-tracker')
        os.makedirs(data_dir, exist_ok=True)
        
        # Set SQLite database path
        db_path = os.path.join(data_dir, 'maintenance_tracker.db')
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
        logger.info(f"Using SQLite database at: {db_path}")
        
        # Set offline mode flag
        os.environ['OFFLINE_MODE'] = 'true'
        logger.info("Running in offline mode")

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

def extract_resource_dir(resource_name, dest_dir):
    """Extract a resource directory from the PyInstaller bundle"""
    bundle_dir = getattr(sys, '_MEIPASS', None)
    if not bundle_dir:
        return None
    src = os.path.join(bundle_dir, resource_name)
    if os.path.exists(src):
        dest = os.path.join(dest_dir, resource_name)
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        return dest
    return None

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
    
    # If running as a PyInstaller bundle, extract templates/static to temp dir
    if getattr(sys, 'frozen', False):
        temp_dir = tempfile.mkdtemp(prefix='amrs_resources_')
        templates_dir = extract_resource_dir('templates', temp_dir)
        static_dir = extract_resource_dir('static', temp_dir)
        if templates_dir:
            os.environ['TEMPLATES_FOLDER'] = templates_dir
        if static_dir:
            os.environ['STATIC_FOLDER'] = static_dir
        # Optionally, clean up temp_dir on exit
        import atexit
        atexit.register(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
    else:
        # Extract resources if running as a packaged app
        templates_dir, static_dir = extract_resources()
    
    # Start the Flask server
    start_flask_server(port, templates_dir, static_dir)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())