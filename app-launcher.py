#!/usr/bin/env python
"""
Wrapper script to launch Flask application with proper path handling
"""
import os
import sys
import importlib.util
import traceback
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("flask_launcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FlaskLauncher")

def set_offline_environment():
    """Configure environment variables for offline mode"""
    # Check if we're in Electron offline mode
    if os.environ.get('ELECTRON_RUN') == 'true':
        logger.info("Setting up offline environment for Electron")
        
        # Set offline mode flag
        os.environ['OFFLINE_MODE'] = 'true'
        
        # Use local SQLite database
        db_path = os.environ.get('DATABASE_PATH')
        if db_path:
            logger.info(f"Using database at: {db_path}")
            os.environ['DATABASE_URL'] = f"sqlite:///{db_path}"
        else:
            # Default to a local file in user's app data
            if sys.platform == 'win32':
                app_data = os.path.join(os.environ.get('APPDATA', '.'), 'AMRS-Maintenance')
            else:
                app_data = os.path.join(os.path.expanduser('~'), '.amrs-maintenance')
                
            os.makedirs(app_data, exist_ok=True)
            db_path = os.path.join(app_data, 'maintenance_local.db')
            os.environ['DATABASE_URL'] = f"sqlite:///{db_path}"
            os.environ['DATABASE_PATH'] = db_path
            logger.info(f"Using default database at: {db_path}")

def inject_sync_api(app_module):
    """Inject the sync API endpoints into the Flask app"""
    if os.environ.get('ELECTRON_RUN') == 'true' and hasattr(app_module, 'app'):
        try:
            sync_api_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                'sync_api.py'
            )
            
            if os.path.exists(sync_api_path):
                logger.info("Injecting Sync API endpoints")
                spec = importlib.util.spec_from_file_location("sync_api", sync_api_path)
                sync_api = importlib.util.module_from_spec(spec)
                
                # Pass the app instance to the module
                sync_api.app = app_module.app
                spec.loader.exec_module(sync_api)
                
                logger.info("Sync API endpoints injected successfully")
            else:
                logger.warning(f"Sync API file not found at {sync_api_path}")
        except Exception as e:
            logger.error(f"Error injecting Sync API: {e}")

def main():
    """Main entry point for the application."""
    # Print diagnostics
    logger.info(f"Python executable: {sys.executable}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    # Set up offline environment if needed
    set_offline_environment()
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"Script directory: {script_dir}")    # Add the script directory to path if not already there
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    
    # Look for app.py in current directory and script directory
    app_paths = [
        os.path.join(os.getcwd(), 'app.py'),
        os.path.join(script_dir, 'app.py')
    ]
    
    # Check for Electron's app.py
    if os.environ.get('ELECTRON_RUN') == 'true':
        electron_app_path = os.path.join(script_dir, 'electron_app', 'app.py')
        if os.path.isfile(electron_app_path):
            app_paths.insert(0, electron_app_path)
      # Find app.py
    app_path = None
    for path in app_paths:
        if os.path.isfile(path):
            app_path = path
            logger.info(f"Found app.py at: {path}")
            break
    
    if not app_path:
        logger.error("ERROR: app.py not found!")
        logger.error(f"Searched paths: {app_paths}")
        sys.exit(1)
    
    try:
        # Import app.py as a module
        logger.info(f"Importing app module from {app_path}")
        sys.path.insert(0, os.path.dirname(app_path))
        spec = importlib.util.spec_from_file_location("app_module", app_path)
        app_module = importlib.util.module_from_spec(spec)
        sys.modules["app_module"] = app_module
        spec.loader.exec_module(app_module)
        
        # Inject sync API endpoints if in Electron mode
        inject_sync_api(app_module)
        
        # Run app if it has a main function or app.run()
        if hasattr(app_module, 'main'):
            logger.info("Running app.main()")
            app_module.main()
        elif hasattr(app_module, 'app'):
            # Get port from environment or command line args
            port = int(os.environ.get('PORT', 5000))
            if len(sys.argv) > 2 and sys.argv[1] == '--port':
                port = int(sys.argv[2])
            
            host = os.environ.get('HOST', '127.0.0.1')
            debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
            
            logger.info(f"Running Flask app on {host}:{port} (debug={debug})")
            app_module.app.run(host=host, port=port, debug=debug)
        else:
            logger.error("ERROR: No app or main function found in app.py")
            sys.exit(1)
    except Exception as e:
        logger.error(f"ERROR: Failed to load or run app.py: {e}")
        traceback.print_exc()
        sys.exit(2)

if __name__ == "__main__":
    main()
