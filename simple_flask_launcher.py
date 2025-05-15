#!/usr/bin/env python
"""
Simplified launcher script for the Flask app in Electron
"""
import os
import sys
import site
import traceback
import subprocess
import importlib
from pathlib import Path
import json
import sqlite3
from datetime import datetime

def setup_environment():
    """Setup the Python environment with required paths"""
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Script directory: {script_dir}")
    
    # Add script directory to path
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    
    # Add potential site-packages locations
    site_packages_paths = [
        os.path.join(script_dir, 'site-packages'),  # Direct site-packages folder
        os.path.join(script_dir, 'venv', 'Lib', 'site-packages'),  # Windows venv path
        os.path.join(script_dir, 'venv', 'lib', 'python3.9', 'site-packages'),  # Unix venv path
        os.path.join(script_dir, 'offline', 'python_packages'),  # Our offline packages folder
        os.path.join(script_dir, 'resources', 'offline', 'python_packages'),  # Packaged offline folder
        os.path.join(os.environ.get('APPDATA', ''), 'amrs-maintenance-tracker', 'python-packages')  # User-specific packages
    ]
    
    # Add all potential paths that exist
    for site_pkg_path in site_packages_paths:
        if os.path.isdir(site_pkg_path):
            print(f"Adding site-packages: {site_pkg_path}")
            if site_pkg_path not in sys.path:
                sys.path.insert(0, site_pkg_path)
                site.addsitedir(site_pkg_path)
    
    # Setup environment variables
    setup_environment_variables()
    
    # Ensure all required packages are available
    return check_dependencies()

def setup_environment_variables():
    """Set up required environment variables"""
    os.environ['ELECTRON'] = '1'
    os.environ['FLASK_DEBUG'] = '0'
    os.environ['PYTHONUNBUFFERED'] = '1'
    
    # Set a default encryption key for Electron mode
    if 'USER_FIELD_ENCRYPTION_KEY' not in os.environ:
        os.environ['USER_FIELD_ENCRYPTION_KEY'] = 'YH15hnZYsYbMZcElKXzxY_G9oJTxg4WMgV0obzLRtAU='
    
    # Set up database directory
    app_data_dir = os.environ.get('APPDATA') or os.path.expanduser('~/Library/Application Support')
    sqlite_dir = os.path.join(app_data_dir, 'AMRS-Maintenance-Tracker')
    os.environ['SQLITE_DIR'] = sqlite_dir
    
    # Ensure database directory exists
    if not os.path.exists(sqlite_dir):
        os.makedirs(sqlite_dir, exist_ok=True)
        print(f"Created database directory: {sqlite_dir}")
    
    # Set default SQLite database path
    db_path = os.path.join(sqlite_dir, 'amrs_maintenance.db')
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    
    print(f"Using database: {os.environ['DATABASE_URL']}")

def ensure_sqlite_database():
    """Ensure SQLite database exists with basic schema"""
    sqlite_dir = os.environ.get('SQLITE_DIR')
    if not sqlite_dir:
        print("Error: SQLITE_DIR environment variable not set")
        return False
        
    db_path = os.path.join(sqlite_dir, 'amrs_maintenance.db')
    
    try:
        # Check if database exists, create it if it doesn't
        if not os.path.exists(db_path):
            print(f"Creating new SQLite database at {db_path}")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create basic tables if they don't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                password_hash TEXT,
                first_name TEXT,
                last_name TEXT,
                role_id INTEGER,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT,
                permissions TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
            ''')
            
            # Create admin role if it doesn't exist
            cursor.execute("SELECT COUNT(*) FROM roles WHERE name = 'admin'")
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                INSERT INTO roles (name, description, permissions, created_at, updated_at)
                VALUES ('admin', 'Administrator', 'admin.full', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''')
                print("Created admin role")
            
            conn.commit()
            conn.close()
            print("SQLite database initialized successfully")
        
        return True
    except Exception as e:
        print(f"Error setting up SQLite database: {e}")
        print(traceback.format_exc())
        return False

def check_dependencies():
    """Check and install required dependencies if needed"""
    required_packages = {
        'flask': '2.2.3',
        'flask_login': '0.6.0',
        'flask_sqlalchemy': '3.0.0',
        'sqlalchemy': '2.0.0',
        'flask_mail': '0.9.1',
        'werkzeug': '2.2.3',
        'cryptography': '41.0.5',
        'python-dotenv': '1.0.0'
    }
    
    missing_packages = []
    installed_versions = {}
    
    # Check each required package
    for package, version in required_packages.items():
        package_name = package.replace('_', '-')
        import_name = package
        
        try:
            # Try to import the package
            module = importlib.import_module(import_name)
            # Get version if available
            if hasattr(module, '__version__'):
                installed_versions[package] = module.__version__
                print(f"Found {package}: version {module.__version__}")
            else:
                installed_versions[package] = "unknown"
                print(f"Found {package}: version unknown")
        except ImportError:
            print(f"Package {package} not found")
            missing_packages.append((package_name, version))
    
    # Try to install missing packages
    if missing_packages:
        print(f"Installing {len(missing_packages)} missing packages...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        offline_dir = os.path.join(script_dir, 'offline', 'python_packages')
        
        for package_name, version in missing_packages:
            try:
                # Try offline installation first
                if os.path.exists(offline_dir):
                    print(f"Attempting offline installation of {package_name}...")
                    result = subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', 
                         '--no-index', f'--find-links={offline_dir}', f'{package_name}=={version}'],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        print(f"Successfully installed {package_name} from offline source")
                        continue
                    else:
                        print(f"Offline installation failed: {result.stderr}")
                
                # Fall back to online installation
                print(f"Installing {package_name} from online source...")
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', f'{package_name}=={version}'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(f"Successfully installed {package_name}")
                else:
                    print(f"Installation of {package_name} failed: {result.stderr}")
                    return False
            except Exception as e:
                print(f"Error installing {package_name}: {e}")
                return False
                
    # Ensure database is properly set up
    return ensure_sqlite_database()

# Import the CORS and method handlers
try:
    from cors_method_handlers import apply_cors_fixes, write_electron_signal_files
except ImportError:
    print("CORS handlers not found, defining inline...")
    
    # Define minimal versions if the module is not available
    def apply_cors_fixes(app):
        @app.after_request
        def add_cors_headers(response):
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
            return response
            
        @app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
        @app.route('/<path:path>', methods=['OPTIONS'])
        def options_handler(path):
            return make_response('', 204)
        
        return app
    
    def write_electron_signal_files(port):
        status_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'AMRS-Maintenance-Tracker')
        os.makedirs(status_dir, exist_ok=True)
        signal_file = os.path.join(status_dir, 'flask_ready.txt')
        port_file = os.path.join(status_dir, 'flask_port.txt')
        try:
            with open(port_file, 'w') as f:
                f.write(str(port))
            with open(signal_file, 'w') as f:
                f.write(f"Flask running on port {port} at {datetime.now().isoformat()}")
        except Exception as e:
            print(f"Error writing signal files: {e}")

def run_minimal_flask_app():
    """Run a minimal Flask app for troubleshooting"""
    try:
        from flask import Flask, jsonify, request, make_response, Response
        minimal_app = Flask(__name__)
        
        # Apply CORS and method handling fixes
        minimal_app = apply_cors_fixes(minimal_app)
        
        # Add endpoints with explicit method support
        @minimal_app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE'])
        def home():
            if request.method == 'POST':
                data = request.get_json(silent=True) or {}
                return jsonify({"status": "ok", "message": "POST received", "data": data})
            elif request.method == 'PUT':
                data = request.get_json(silent=True) or {}
                return jsonify({"status": "ok", "message": "PUT received", "data": data})
            elif request.method == 'DELETE':
                return jsonify({"status": "ok", "message": "DELETE received"})
            else:
                return "AMRS Maintenance Tracker - Diagnostic Server is running!"
        
        # Ensure all endpoints support common HTTP methods
        @minimal_app.route('/health-check', methods=['GET', 'POST', 'PUT', 'DELETE'])
        def health_check():
            return jsonify({
                "status": "ok", 
                "message": "Diagnostic server is running",
                "method": request.method,
                "timestamp": datetime.now().isoformat()
            })
        
        @minimal_app.route('/ping', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
        def ping():
            return Response("pong", content_type="text/plain")
        
        # Get port from environment or use default
        port = int(os.environ.get('PORT', 8033))
        
        # Write signal files for Electron
        write_electron_signal_files(port)
        
        print(f"\nStarting diagnostic Flask server on port {port}")
        print("This is a test server for troubleshooting only!")
        print(f"Access the server at: http://localhost:{port}")
        print(f"Health check at: http://localhost:{port}/health-check")
        print(f"Quick ping at: http://localhost:{port}/ping")
        
        # Disable reloader to avoid duplicate processes
        minimal_app.run(host='0.0.0.0', port=port, threaded=True, use_reloader=False)
        
        return True
    except Exception as e:
        print(f"Error starting minimal Flask app: {e}")
        print(traceback.format_exc())
        return False

def run_flask_app():
    """Run the Flask application"""
    # Even in troubleshooting mode, attempt to run the real app first
    try:
        # Find the main app
        script_dir = os.path.dirname(os.path.abspath(__file__))
        app_path = os.path.join(script_dir, 'app.py')
        
        if os.path.exists(app_path):
            print(f"Found main app at {app_path}, attempting to run it directly")
            
            # Import the app module
            try:
                # First, update signal file to show we're trying to load the main app
                port = int(os.environ.get('PORT', 8033))
                write_electron_signal_files(port)
                
                # Now try to load the app
                spec = importlib.util.spec_from_file_location("app_module", app_path)
                app_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(app_module)
                
                if hasattr(app_module, 'app'):
                    # Apply CORS fixes to the main app
                    app_module.app = apply_cors_fixes(app_module.app)
                    
                    # Write final signal file
                    write_electron_signal_files(port)
                    
                    print(f"Successfully loaded and fixed main app, running on port {port}")
                    app_module.app.run(host='0.0.0.0', port=port, threaded=True, use_reloader=False)
                    return True
            except Exception as e:
                print(f"Error loading main app: {e}")
                print(traceback.format_exc())
    except Exception as e:
        print(f"Error finding main app: {e}")
        print(traceback.format_exc())
    
    # If we get here, we couldn't run the main app, so fall back to the minimal app
    print("Falling back to diagnostic server")
    return run_minimal_flask_app()

if __name__ == "__main__":
    print("=" * 50)
    print("AMRS Maintenance Tracker - Flask Launcher")
    print("=" * 50)
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Arguments: {sys.argv}")
    
    # Set troubleshooting mode if requested
    if len(sys.argv) > 1 and sys.argv[1] == '--troubleshoot':
        os.environ['FLASK_TROUBLESHOOT'] = '1'
        print("TROUBLESHOOTING MODE ENABLED")
    
    # Use a consistent port if possible
    if 'PORT' not in os.environ:
        os.environ['PORT'] = '8033'  # Use a fixed port for easier connection
        print(f"Using fixed port: {os.environ['PORT']}")
        
    if setup_environment():
        print("Environment setup complete, launching Flask...")
        run_flask_app()
    else:
        print("Failed to setup environment")
        sys.exit(1)
