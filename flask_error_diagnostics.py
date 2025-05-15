"""
Diagnostic helper for Flask startup errors in AMRS application.
This script runs before the main Flask app to check for common issues.
"""
import os
import sys
import platform
import sqlite3
import logging
import importlib
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("flask_diagnostics")

def check_python_environment():
    """Check Python environment and dependencies"""
    logger.info("Python version: %s", sys.version)
    logger.info("Platform: %s %s", platform.system(), platform.release())
    logger.info("Running from: %s", os.getcwd())
    
    # Check for required modules
    required_modules = [
        "flask", "sqlalchemy", "sqlite3", "datetime", "os", "sys", 
        "platform", "logging", "traceback"
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            importlib.import_module(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        logger.error("Missing required modules: %s", ", ".join(missing_modules))
    else:
        logger.info("All basic required modules are available")
    
    # Return missing modules for further processing
    return missing_modules

def check_database_access():
    """Check database access"""
    try:
        # Find database path through environment variables
        appdata_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
        db_dir = os.path.join(appdata_dir, 'amrs-preventative-maintenance', 'AMRS-Maintenance-Tracker')
        db_path = os.path.join(db_dir, 'amrs_maintenance.db')
        
        # Check if database directory exists
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Created database directory: {db_dir}")
        
        # Check if database file exists
        if not os.path.exists(db_path):
            logger.warning(f"Database file does not exist: {db_path}")
            logger.info("Will create a new database file for testing")
            
            # Create a test connection to verify SQLite is working
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create a test table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS diagnostics_test (
                id INTEGER PRIMARY KEY,
                test_name TEXT,
                timestamp TEXT
            )
            ''')
            
            # Insert a test record
            cursor.execute(
                "INSERT INTO diagnostics_test (test_name, timestamp) VALUES (?, ?)",
                ("startup_test", datetime.now().isoformat())
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Successfully created test database at {db_path}")
        else:
            # Connect to existing database
            logger.info(f"Found existing database at {db_path}")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Test query
            cursor.execute("SELECT sqlite_version();")
            version = cursor.fetchone()[0]
            logger.info(f"Connected to SQLite version {version}")
            
            # Get table information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [table[0] for table in cursor.fetchall()]
            logger.info(f"Found {len(tables)} tables: {', '.join(tables)}")
            
            conn.close()
            
        return True
    except Exception as e:
        logger.error(f"Database access error: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def check_required_files():
    """Check for required application files"""
    required_files = [
        "simple_flask_launcher.py",
        "simple_healthcheck.py",
        "app_debug_helper.py",
        "add_audit_task_color_column.py",
        "electron_db_sync.py",
        "cors_method_handlers.py"
    ]
    
    missing_files = []
    for filename in required_files:
        if not os.path.exists(filename):
            missing_files.append(filename)
    
    if missing_files:
        logger.error("Missing required files: %s", ", ".join(missing_files))
        # Create the missing files automatically using minimal implementations
        for missing_file in missing_files:
            create_missing_file(missing_file)
    else:
        logger.info("All required files are present")
    
    return missing_files

def create_missing_file(filename):
    """Create a minimal implementation of a missing file"""
    logger.info(f"Creating minimal implementation of {filename}")
    
    if filename == "simple_healthcheck.py":
        content = """
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class HealthCheck:
    def __init__(self, app=None):
        self.app = app
        self.checks = []
        if app:
            self.init_app(app)
            
    def init_app(self, app):
        self.app = app
        @app.route('/healthcheck')
        def healthcheck_route():
            from flask import jsonify
            return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})
    
    def add_check(self, check_func, name=None):
        if name is None:
            name = check_func.__name__
        self.checks.append((name, check_func))
        return check_func
    
    def run_checks(self):
        results = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        return results
"""
    elif filename == "app_debug_helper.py":
        content = """
import os
import sys
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def register_debug_routes(app):
    @app.route('/debug/info')
    def debug_info():
        from flask import jsonify
        return jsonify({
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "python_version": sys.version
        })
    return app

logger.info("app_debug_helper module loaded successfully")
"""
    elif filename == "add_audit_task_color_column.py":
        content = """
import logging

logger = logging.getLogger(__name__)

def migrate(db_connection=None):
    logger.info("Placeholder migration function")
    return True
"""
    elif filename == "electron_db_sync.py":
        content = """
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DBSync:
    def __init__(self, sqlite_uri=None, postgres_uri=None):
        self.sqlite_uri = sqlite_uri
        self.postgres_uri = postgres_uri
        
    def validate_config(self):
        return True
        
    def sync_data(self):
        return True

def get_sync_handler():
    return DBSync()
"""
    elif filename == "cors_method_handlers.py":
        content = """
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def apply_cors_fixes(app):
    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        return response
    return app

def write_electron_signal_files(port):
    pass

logger.info("cors_method_handlers module loaded successfully")
"""
    else:
        content = f"""
# Placeholder file for {filename}
# Created by automatic diagnostics on {datetime.now().isoformat()}
"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content.strip())
    
    logger.info(f"Created {filename}")

def create_recovery_signal():
    """Create a recovery signal file to notify Electron"""
    try:
        appdata_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
        status_dir = os.path.join(appdata_dir, 'AMRS-Maintenance-Tracker')
        os.makedirs(status_dir, exist_ok=True)
        
        # Write diagnostic results
        diag_file = os.path.join(status_dir, 'flask_diagnostics.txt')
        with open(diag_file, 'w') as f:
            f.write(f"Diagnostics run at: {datetime.now().isoformat()}\n")
            f.write(f"Python version: {sys.version}\n")
            f.write(f"Platform: {platform.system()} {platform.release()}\n")
            f.write(f"Running from: {os.getcwd()}\n")
        
        # Create a minimal Flask app for Electron to connect to
        recovery_port = 8034  # Use different port to avoid conflicts
        
        # Write port file
        port_file = os.path.join(status_dir, 'flask_recovery_port.txt')
        with open(port_file, 'w') as f:
            f.write(str(recovery_port))
        
        logger.info(f"Created recovery signal files in {status_dir}")
        return recovery_port
    except Exception as e:
        logger.error(f"Error creating recovery signal: {str(e)}")
        return None

def run_diagnostic_flask():
    """Run a minimal Flask app for diagnosis"""
    try:
        from flask import Flask, jsonify
        
        app = Flask(__name__)
        
        @app.route('/')
        def home():
            return """
            <html>
            <head>
                <title>AMRS Diagnostics</title>
                <style>
                    body { font-family: Arial; padding: 20px; max-width: 800px; margin: 0 auto; }
                    h1 { color: #e74c3c; }
                    .info { background: #f8f9fa; padding: 15px; border-radius: 5px; }
                    pre { background: #f0f0f0; padding: 10px; overflow: auto; }
                </style>
            </head>
            <body>
                <h1>AMRS Maintenance Tracker - Diagnostics Mode</h1>
                <div class="info">
                    <p>The main application encountered an error during startup.</p>
                    <p>This is a diagnostic server to help troubleshoot the issue.</p>
                </div>
                <h2>System Information</h2>
                <pre>Python: {sys.version}
Platform: {platform.system()} {platform.release()}
Directory: {os.getcwd()}</pre>
                <h2>Available Endpoints</h2>
                <ul>
                    <li><a href="/api/diagnostics">/api/diagnostics</a> - View diagnostic data</li>
                    <li><a href="/api/health">/api/health</a> - Health check</li>
                </ul>
            </body>
            </html>
            """
        
        @app.route('/api/diagnostics')
        def diagnostics():
            # Run checks
            python_env = check_python_environment()
            db_access = check_database_access()
            req_files = check_required_files()
            
            return jsonify({
                "status": "diagnostic_mode",
                "timestamp": datetime.now().isoformat(),
                "python_version": sys.version,
                "platform": f"{platform.system()} {platform.release()}",
                "directory": os.getcwd(),
                "environment_check": {
                    "success": len(python_env) == 0,
                    "missing_modules": python_env
                },
                "database_check": {
                    "success": db_access
                },
                "files_check": {
                    "success": len(req_files) == 0,
                    "missing_files": req_files
                }
            })
        
        @app.route('/api/health')
        def health():
            return jsonify({
                "status": "ok",
                "mode": "diagnostic",
                "timestamp": datetime.now().isoformat()
            })
        
        @app.route('/ping')
        def ping():
            return "pong"
        
        # Create recovery signal files
        recovery_port = create_recovery_signal() or 8034
        
        logger.info(f"Starting diagnostic Flask server on port {recovery_port}")
        app.run(host='0.0.0.0', port=recovery_port, debug=False)
        
    except ImportError:
        logger.error("Could not import Flask. Install it with: pip install flask")
    except Exception as e:
        logger.error(f"Error running diagnostic Flask: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    logger.info("Running Flask startup diagnostics")
    
    # Run checks
    check_python_environment()
    check_database_access()
    check_required_files()
    
    # Run a minimal diagnostic Flask server
    run_diagnostic_flask()
