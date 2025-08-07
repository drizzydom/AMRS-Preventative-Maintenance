#!/usr/bin/env python3
"""
Flask App Launcher for Electron
This script starts the Flask backend in production mode for the Electron app.
"""

import os
import sys
import platform
from pathlib import Path

# Add the current directory to Python path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

def setup_environment():
    """Set up environment variables for production mode."""
    # Set Flask to production mode
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = 'false'
    
    # Set host and port for Electron
    os.environ['FLASK_RUN_HOST'] = '127.0.0.1'
    os.environ['FLASK_RUN_PORT'] = '10000'
    os.environ['PORT'] = '10000'
    
    # Set a secret key for production
    import secrets
    if not os.environ.get('SECRET_KEY'):
        os.environ['SECRET_KEY'] = secrets.token_hex(32)
    
    # Disable Flask development server warnings
    os.environ['FLASK_SKIP_DOTENV'] = '1'
    
    # Set up secure database path for the desktop app
    if platform.system().lower() == "darwin":
        app_support = Path.home() / "Library" / "Application Support" / "AMRS_PM"
    elif platform.system().lower() == "windows":
        app_support = Path(os.environ.get('APPDATA', Path.home())) / "AMRS_PM"
    else:
        app_support = Path.home() / ".local" / "share" / "AMRS_PM"
    
    app_support.mkdir(parents=True, exist_ok=True)
    db_path = app_support / "maintenance_secure.db"
    
    # Force SQLite database for desktop app
    os.environ['DATABASE_URL'] = f"sqlite:///{db_path}"
    
    print(f"[LAUNCHER] Using database: {db_path}")
    print(f"[LAUNCHER] Flask will run on: http://127.0.0.1:10000")

def main():
    """Main launcher function."""
    print("[LAUNCHER] Starting AMRS Flask Backend for Electron...")
    
    # Setup environment
    setup_environment()
    
    try:
        # Import and run the Flask app - this will trigger the __main__ section
        # which properly initializes everything including the database and socketio
        import app
        
    except Exception as e:
        print(f"[LAUNCHER] Error starting Flask app: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
