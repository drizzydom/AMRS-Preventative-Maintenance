#!/usr/bin/env python3
"""
Script to run the offline app and test the token authentication system

This script will:
1. Start the offline app
2. Initialize the database with test data if needed
3. Set up proper environment variables for token authentication testing
4. Provide options for manual testing

Usage:
    python run_offline_token_test.py [--expiry DAYS] [--port PORT] [--debug]
"""
import os
import sys
import argparse
import subprocess
import threading
import webbrowser
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='[RUN_OFFLINE_TOKEN_TEST] %(levelname)s - %(message)s')
logger = logging.getLogger("run_offline_token_test")

def setup_argparse():
    """Set up command line arguments"""
    parser = argparse.ArgumentParser(description='Run the offline app with token authentication testing')
    
    parser.add_argument('--expiry', type=int, default=30, 
                        help='Token expiry in days (default: 30)')
    parser.add_argument('--port', type=int, default=5000, 
                        help='Port to run the offline app on (default: 5000)')
    parser.add_argument('--debug', action='store_true', default=False,
                        help='Run the app in debug mode')
    parser.add_argument('--enhanced', action='store_true', default=True,
                        help='Use the enhanced token manager')
    parser.add_argument('--no-browser', action='store_true', default=False,
                        help='Do not automatically open browser')
    parser.add_argument('--recreate-db', action='store_true', default=False,
                        help='Recreate the database')
    
    return parser

def launch_browser(port):
    """Launch browser after a short delay"""
    time.sleep(2)  # Give the app some time to start
    webbrowser.open(f"http://localhost:{port}")

def main():
    """Main function"""
    parser = setup_argparse()
    args = parser.parse_args()
    
    # Create environment variables for the offline app
    env = os.environ.copy()
    
    # Token-related environment variables
    env['TOKEN_EXPIRY_DAYS'] = str(args.expiry)
    env['USE_ENHANCED_TOKEN_MANAGER'] = 'true' if args.enhanced else 'false'
    env['JWT_SECRET_KEY'] = 'secure_offline_jwt_secret_key_for_testing'
    env['TOKEN_REFRESH_THRESHOLD_DAYS'] = '5'
    
    # Database-related environment variables
    if args.recreate_db:
        env['RECREATE_DB'] = 'true'
    
    # App-related environment variables
    env['OFFLINE_MODE'] = 'true'
    env['FLASK_ENV'] = 'development' if args.debug else 'production'
    env['PORT'] = str(args.port)
    
    # Log configuration
    logger.info(f"Token expiry days: {args.expiry}")
    logger.info(f"Using enhanced token manager: {args.enhanced}")
    logger.info(f"App running on port: {args.port}")
    logger.info(f"Debug mode: {args.debug}")
    
    # Launch browser in a separate thread if requested
    if not args.no_browser:
        browser_thread = threading.Thread(target=launch_browser, args=(args.port,))
        browser_thread.daemon = True
        browser_thread.start()
    
    # Run the offline app
    try:
        logger.info("Starting offline app...")
        
        # Get path to offline_app.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        app_path = os.path.join(current_dir, 'offline_app.py')
        
        # Run the app
        result = subprocess.run(
            [sys.executable, app_path],
            env=env,
            check=True
        )
        
        return result.returncode
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
        return 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running offline app: {e}")
        return e.returncode
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
