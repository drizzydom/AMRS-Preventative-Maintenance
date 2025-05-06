import os
import sys
import time
import json
import urllib.request
import zipfile
import tempfile
import shutil
import subprocess
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='[APP_BOOTSTRAP] %(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("app_bootstrap")

# Configuration
TEMPLATE_SERVER_URL = "https://amrs-maintenance-tracker.onrender.com"  # Change to your actual server URL
LOCAL_TEMPLATE_DIR = "templates"
LOCAL_STATIC_DIR = "static"
APP_DATA_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Local", "AMRS-Maintenance-Tracker")
RESOURCE_PATH = os.environ.get('RESOURCE_PATH', os.path.dirname(os.path.abspath(__file__)))

def ensure_dir_exists(dir_path):
    """Ensure a directory exists, creating it if needed."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        logger.info(f"Created directory: {dir_path}")
    return dir_path

def download_file(url, local_path):
    """Download a file from URL to local path."""
    try:
        logger.info(f"Downloading {url} to {local_path}")
        with urllib.request.urlopen(url) as response, open(local_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def download_assets():
    """Download templates and static assets from the server."""
    try:
        # Create app data directory
        app_data_dir = ensure_dir_exists(APP_DATA_DIR)
        templates_dir = ensure_dir_exists(os.path.join(app_data_dir, LOCAL_TEMPLATE_DIR))
        static_dir = ensure_dir_exists(os.path.join(app_data_dir, LOCAL_STATIC_DIR))
        
        # Download assets list
        assets_url = f"{TEMPLATE_SERVER_URL}/api/assets/info"
        logger.info(f"Checking assets from: {assets_url}")
        
        try:
            with urllib.request.urlopen(assets_url) as response:
                assets_info = json.loads(response.read().decode('utf-8'))
                
                # Check if we need to download templates
                templates_archive_url = f"{TEMPLATE_SERVER_URL}/api/assets/templates.zip"
                templates_version = assets_info.get('templates_version', '0')
                
                # Check if we have the current version
                version_file = os.path.join(templates_dir, 'version.txt')
                current_version = '0'
                if os.path.exists(version_file):
                    with open(version_file, 'r') as f:
                        current_version = f.read().strip()
                
                if templates_version != current_version or not os.listdir(templates_dir):
                    logger.info(f"Downloading templates (version {templates_version})...")
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
                        if download_file(templates_archive_url, temp_file.name):
                            # Extract the templates
                            with zipfile.ZipFile(temp_file.name, 'r') as zip_ref:
                                zip_ref.extractall(templates_dir)
                            
                            # Save the version
                            with open(version_file, 'w') as f:
                                f.write(templates_version)
                            
                            logger.info("Templates downloaded and extracted successfully")
                        os.unlink(temp_file.name)
                else:
                    logger.info(f"Templates are up to date (version {current_version})")
                
                # Check if we need to download static files
                static_archive_url = f"{TEMPLATE_SERVER_URL}/api/assets/static.zip"
                static_version = assets_info.get('static_version', '0')
                
                # Check if we have the current version
                version_file = os.path.join(static_dir, 'version.txt')
                current_version = '0'
                if os.path.exists(version_file):
                    with open(version_file, 'r') as f:
                        current_version = f.read().strip()
                
                if static_version != current_version or not os.listdir(static_dir):
                    logger.info(f"Downloading static assets (version {static_version})...")
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
                        if download_file(static_archive_url, temp_file.name):
                            # Extract the static files
                            with zipfile.ZipFile(temp_file.name, 'r') as zip_ref:
                                zip_ref.extractall(static_dir)
                            
                            # Save the version
                            with open(version_file, 'w') as f:
                                f.write(static_version)
                            
                            logger.info("Static assets downloaded and extracted successfully")
                        os.unlink(temp_file.name)
                else:
                    logger.info(f"Static assets are up to date (version {current_version})")
                
                return {
                    'templates_dir': templates_dir,
                    'static_dir': static_dir
                }
        except Exception as e:
            logger.error(f"Error checking assets: {e}")
            # If we can't download, but have local files, continue with those
            if os.listdir(templates_dir) and os.listdir(static_dir):
                logger.info("Using existing local assets")
                return {
                    'templates_dir': templates_dir,
                    'static_dir': static_dir
                }
            raise
            
    except Exception as e:
        logger.error(f"Failed to download assets: {e}")
        # Fall back to using the resources directory if available
        templates_dir = os.path.join(RESOURCE_PATH, LOCAL_TEMPLATE_DIR)
        static_dir = os.path.join(RESOURCE_PATH, LOCAL_STATIC_DIR)
        
        if os.path.exists(templates_dir) and os.path.exists(static_dir):
            logger.info(f"Using bundled assets from {RESOURCE_PATH}")
            return {
                'templates_dir': templates_dir,
                'static_dir': static_dir
            }
        else:
            logger.error(f"No assets available! Templates: {templates_dir}, Static: {static_dir}")
            return None

def start_flask_app(templates_dir, static_dir, port=10000):
    """Start the Flask application."""
    flask_app = os.path.join(RESOURCE_PATH, "app.py")
    
    if not os.path.exists(flask_app):
        logger.error(f"Flask app not found at {flask_app}")
        sys.exit(1)
    
    logger.info(f"Starting Flask app from {flask_app} on port {port}")
    logger.info(f"Using templates from {templates_dir}")
    logger.info(f"Using static files from {static_dir}")
    
    # Set environment variables for Flask to know where to find templates and static files
    env = os.environ.copy()
    env["FLASK_APP"] = flask_app
    env["TEMPLATES_FOLDER"] = templates_dir
    env["STATIC_FOLDER"] = static_dir
    env["RESOURCE_PATH"] = RESOURCE_PATH
    
    # Run the Flask app
    args = [sys.executable, flask_app, "--port", str(port)]
    
    # In production, use subprocess.call to block until the Flask app exits
    # In development/debug, use subprocess.Popen to run in the background
    try:
        return subprocess.call(args, env=env)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        return 0

if __name__ == "__main__":
    logger.info("Starting AMRS Maintenance Tracker bootstrap...")
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='AMRS Maintenance Tracker Bootstrap')
    parser.add_argument('--port', type=int, default=10000, help='Port for Flask server')
    args = parser.parse_args()
    
    # Download or verify assets
    assets = download_assets()
    
    if assets:
        # Start Flask with the correct template and static directories
        exit_code = start_flask_app(
            templates_dir=assets['templates_dir'],
            static_dir=assets['static_dir'],
            port=args.port
        )
        sys.exit(exit_code)
    else:
        logger.error("Failed to initialize assets. Exiting.")
        sys.exit(1)