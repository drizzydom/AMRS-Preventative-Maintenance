"""
AMRS Maintenance Tracker - Desktop Application

This application creates a standalone desktop version of the AMRS Maintenance Tracker
using CEF Python (Chromium Embedded Framework) to display the web interface.
"""
import os
import sys
import time
import json
import threading
import logging
import sqlite3
import signal
import uuid
from pathlib import Path
from datetime import datetime
import subprocess
import socket
import webbrowser
import platform
import argparse

# Try to import CEF Python
try:
    from cefpython3 import cefpython as cef
except ImportError:
    print("Error: CEF Python not installed. Please run: pip install cefpython3==66.1")
    sys.exit(1)

# Constants
APP_NAME = "AMRS Maintenance Tracker"
APP_VERSION = "1.0.0"
APP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".amrs-maintenance")
OFFLINE_DB_PATH = os.path.join(APP_DATA_DIR, "offline_data.db")
LOG_PATH = os.path.join(APP_DATA_DIR, "desktop_app.log")
CEF_LOG_PATH = os.path.join(APP_DATA_DIR, "cef_debug.log")
DEBUG = False  # Set to True to enable debug logging

# Determine if we're running as an executable or as a script
FROZEN = getattr(sys, 'frozen', False)
if FROZEN:
    # Running as compiled executable
    APP_PATH = os.path.dirname(sys.executable)
else:
    # Running as script
    APP_PATH = os.path.dirname(os.path.abspath(__file__))

# Create app data directory if it doesn't exist
os.makedirs(APP_DATA_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OfflineDatabase:
    """Handle offline database operations"""
    def __init__(self, db_path):
        self.db_path = db_path
        self.initialize()

    def initialize(self):
        """Initialize the offline database"""
        try:
            # Create database directory if it doesn't exist
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables for offline data storage
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS cached_data (
                endpoint TEXT PRIMARY KEY,
                data TEXT,
                timestamp TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_operations (
                id TEXT PRIMARY KEY,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                data TEXT,
                timestamp TEXT,
                synced INTEGER DEFAULT 0
            )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Offline database initialized")
        except Exception as e:
            logger.error(f"Error initializing offline database: {e}")

    def cache_data(self, endpoint, data):
        """Cache data for offline use"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            data_json = json.dumps(data)
            
            cursor.execute('''
                INSERT OR REPLACE INTO cached_data (endpoint, data, timestamp)
                VALUES (?, ?, ?)
            ''', (endpoint, data_json, timestamp))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error caching data: {e}")
            
    def get_cached_data(self, endpoint):
        """Retrieve cached data for an endpoint"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT data, timestamp FROM cached_data WHERE endpoint = ?', (endpoint,))
            result = cursor.fetchone()
            
            conn.close()
            
            if result:
                data = json.loads(result[0])
                timestamp = result[1]
                return data, timestamp
            return None, None
        except Exception as e:
            logger.error(f"Error retrieving cached data: {e}")
            return None, None
    
    def store_pending_operation(self, endpoint, method, data):
        """Store an operation to be performed when back online"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            operation_id = str(uuid.uuid4())
            data_json = json.dumps(data)
            
            cursor.execute('''
                INSERT INTO pending_operations (id, endpoint, method, data, timestamp, synced)
                VALUES (?, ?, ?, ?, ?, 0)
            ''', (operation_id, endpoint, method, data_json, timestamp))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Stored pending operation: {method} {endpoint}")
            return True
        except Exception as e:
            logger.error(f"Error storing pending operation: {e}")
            return False

    def get_pending_operations(self):
        """Get all pending operations"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, endpoint, method, data, timestamp FROM pending_operations WHERE synced = 0')
            operations = []
            
            for row in cursor.fetchall():
                operations.append({
                    'id': row[0],
                    'endpoint': row[1],
                    'method': row[2],
                    'data': json.loads(row[3]),
                    'timestamp': row[4]
                })
            
            conn.close()
            return operations
        except Exception as e:
            logger.error(f"Error getting pending operations: {e}")
            return []
    
    def mark_operation_synced(self, operation_id):
        """Mark an operation as synced"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('UPDATE pending_operations SET synced = 1 WHERE id = ?', (operation_id,))
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"Error marking operation as synced: {e}")
            return False

def get_available_port():
    """Find an available port to run the Flask server on"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

def start_flask_server(port, debug=False):
    """Start the Flask server in a separate process"""
    try:
        # Get path to the Flask app
        if FROZEN:
            app_script = os.path.join(APP_PATH, "app.py")
        else:
            app_script = os.path.join(APP_PATH, "app.py")
            
        # Check if file exists
        if not os.path.isfile(app_script):
            logger.error(f"Flask app not found at {app_script}")
            return None
            
        logger.info(f"Starting Flask server with {app_script} on port {port}")
        
        # Build the command
        cmd = [
            sys.executable, 
            app_script,
            "--port", str(port)
        ]
        
        if debug:
            cmd.append("--debug")
        
        # Use subprocess to run the Flask application
        flask_process = subprocess.Popen(
            cmd,
            # Capture output for debugging
            stdout=subprocess.PIPE if DEBUG else subprocess.DEVNULL,
            stderr=subprocess.PIPE if DEBUG else subprocess.DEVNULL
        )
        
        # Check if process started successfully
        if flask_process.poll() is None:
            logger.info(f"Flask server started on port {port}")
            return flask_process
        else:
            logger.error(f"Failed to start Flask server: Exit code {flask_process.returncode}")
            return None
            
    except Exception as e:
        logger.error(f"Error starting Flask server: {e}")
        return None

def wait_for_flask_server(port, timeout=30):
    """Wait for Flask server to become available"""
    logger.info(f"Waiting for Flask server on port {port}")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            if result == 0:  # Port is open and accepting connections
                logger.info(f"Flask server is ready on port {port}")
                # Give it a little extra time for routes to be registered
                time.sleep(1)
                return True
            time.sleep(0.5)
        except Exception:
            time.sleep(0.5)
    
    logger.error(f"Timed out waiting for Flask server on port {port}")
    return False

def setup_cef():
    """Set up CEF browser"""
    logger.info("Setting up CEF browser")
    sys.excepthook = cef.ExceptHook  # To shutdown CEF processes on exception
    
    # CEF configuration settings
    settings = {
        "product_version": f"{APP_NAME}/{APP_VERSION}",
        "user_agent": f"{APP_NAME}/{APP_VERSION} CEF Python/{cef.GetVersion()}",
        "cache_path": os.path.join(APP_DATA_DIR, "cef_cache"),
    }
    
    if DEBUG:
        settings["log_severity"] = cef.LOGSEVERITY_INFO
        settings["log_file"] = CEF_LOG_PATH
    else:
        settings["log_severity"] = cef.LOGSEVERITY_WARNING
    
    # Initialize CEF
    cef.Initialize(settings=settings)
    logger.info("CEF initialized")

class SyncManager:
    """Manage synchronization of offline data with the server"""
    def __init__(self, offline_db, url):
        self.offline_db = offline_db
        self.base_url = url
        self.online = False
    
    def check_online_status(self):
        """Check if we are online"""
        try:
            # Try to connect to the base URL
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            url_parts = self.base_url.split("//")[1].split(":")
            host = url_parts[0]
            port = int(url_parts[1]) if len(url_parts) > 1 else 80
            result = sock.connect_ex((host, port))
            sock.close()
            
            self.online = (result == 0)
            return self.online
        except Exception as e:
            logger.error(f"Error checking online status: {e}")
            self.online = False
            return False
    
    def sync_pending_operations(self):
        """Synchronize pending operations with the server"""
        if not self.check_online_status():
            logger.info("Not online, skipping synchronization")
            return False
        
        # Get pending operations
        operations = self.offline_db.get_pending_operations()
        if not operations:
            logger.info("No pending operations to synchronize")
            return True
        
        logger.info(f"Synchronizing {len(operations)} pending operations")
        
        import requests
        synced_count = 0
        
        for operation in operations:
            try:
                endpoint = operation['endpoint']
                method = operation['method']
                data = operation['data']
                operation_id = operation['id']
                
                # Send request to server
                url = f"{self.base_url}{endpoint}"
                response = requests.request(
                    method=method,
                    url=url,
                    json=data,
                    timeout=10
                )
                
                if response.ok:
                    # Mark operation as synced
                    self.offline_db.mark_operation_synced(operation_id)
                    synced_count += 1
                else:
                    logger.error(f"Failed to sync operation {operation_id}: {response.status_code} {response.text}")
            except Exception as e:
                logger.error(f"Error syncing operation {operation.get('id', 'unknown')}: {e}")
        
        logger.info(f"Synchronized {synced_count}/{len(operations)} operations")
        return synced_count > 0

class AppJSHandler:
    """Handle JavaScript interactions with Python"""
    def __init__(self, offline_db, sync_manager):
        self.offline_db = offline_db
        self.sync_manager = sync_manager
        
    def getCachedData(self, endpoint):
        """Get cached data for an API endpoint"""
        data, timestamp = self.offline_db.get_cached_data(endpoint)
        if data:
            return json.dumps({
                "data": data,
                "timestamp": timestamp,
                "fromCache": True
            })
        return json.dumps({"error": "No cached data found"})
    
    def storePendingOperation(self, endpoint, method, data):
        """Store an operation to be performed when back online"""
        success = self.offline_db.store_pending_operation(endpoint, method, data)
        return json.dumps({"success": success})
    
    def checkOnlineStatus(self):
        """Check if the application is online"""
        is_online = self.sync_manager.check_online_status()
        return json.dumps({"online": is_online})
    
    def syncData(self):
        """Synchronize pending operations with server"""
        success = self.sync_manager.sync_pending_operations()
        return json.dumps({"success": success})

class LoadHandler(object):
    """Handler for browser load events"""
    def __init__(self, browser, offline_db, sync_manager):
        self.browser = browser
        self.offline_db = offline_db
        self.sync_manager = sync_manager
        self.js_bindings = None
        
    def OnLoadingStateChange(self, browser, is_loading, **_):
        """Handle page load state changes"""
        if not is_loading:
            logger.info("Page loaded successfully")
            
            # Inject JavaScript API for offline capabilities
            self._inject_js_api()
            
            # Check online status
            is_online = self.sync_manager.check_online_status()
            
            # Set the application mode (online or offline)
            browser.ExecuteJavascript(f"""
                console.log('Setting application mode: {"ONLINE" if is_online else "OFFLINE"}');
                window.AMRS = window.AMRS || {{}};
                window.AMRS.isOnline = {str(is_online).lower()};
            """)
    
    def _inject_js_api(self):
        """Inject JavaScript API for offline capabilities"""
        if not self.js_bindings:
            self.js_bindings = cef.JavascriptBindings(bindToFrames=False, bindToPopups=False)
            
            # Create JavaScript handler
            js_handler = AppJSHandler(self.offline_db, self.sync_manager)
            
            # Add functions to the JavaScript API
            self.js_bindings.SetObject("amrsOfflineAPI", js_handler)
            self.browser.SetJavascriptBindings(self.js_bindings)
            
            # Inject the API wrapper
            self.browser.ExecuteJavascript("""
                console.log('Injecting AMRS offline API');
                window.AMRS = window.AMRS || {};
                window.AMRS.offline = {
                    getCachedData: function(endpoint) {
                        return JSON.parse(amrsOfflineAPI.getCachedData(endpoint));
                    },
                    storePendingOperation: function(endpoint, method, data) {
                        return JSON.parse(amrsOfflineAPI.storePendingOperation(endpoint, method, data));
                    },
                    checkOnlineStatus: function() {
                        return JSON.parse(amrsOfflineAPI.checkOnlineStatus());
                    },
                    syncData: function() {
                        return JSON.parse(amrsOfflineAPI.syncData());
                    }
                };
                console.log('AMRS offline API injected');
            """)

class RequestHandler(object):
    """Handler for network requests"""
    def __init__(self, base_url, offline_db):
        self.base_url = base_url
        self.offline_db = offline_db
        self.is_monitoring_api = False
    
    def OnBeforeResourceLoad(self, browser, frame, request, callback, **_):
        """Handle resource loading before network request"""
        # Continue with request
        return False
    
    def OnResourceResponse(self, browser, frame, request, response, **_):
        """Handle resource loading after response is received"""
        if not self.is_monitoring_api:
            return
            
        try:
            url = request.GetUrl()
            
            # Check if this is an API response to cache
            if '/api/' in url and not url.endswith('/api/login'):
                # Extract the API endpoint
                endpoint = url.split(self.base_url)[1] if self.base_url in url else url
                
                # Get the response as text
                response_text = response.GetBody() if hasattr(response, 'GetBody') else None
                
                if response_text:
                    try:
                        # Parse the JSON response
                        data = json.loads(response_text)
                        
                        # Cache the data
                        self.offline_db.cache_data(endpoint, data)
                        logger.debug(f"Cached API response for {endpoint}")
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON response from {endpoint}")
                else:
                    logger.debug(f"No response body available for {endpoint}")
        except Exception as e:
            logger.error(f"Error in OnResourceResponse: {e}")

def create_browser_window(url, offline_db, sync_manager):
    """Create and configure the CEF browser window"""
    logger.info(f"Creating browser window with URL: {url}")
    
    # Create browser settings
    browser_settings = {
        "application_cache_disabled": False,
        "default_encoding": "utf-8",
        "javascript_close_windows_disallowed": False
    }
    
    # Define window size
    window_info = cef.WindowInfo()
    window_info.SetAsChild(0, [0, 0, 1200, 800])  # Initial size
    
    # Create the browser
    browser = cef.CreateBrowserSync(
        window_info=window_info,
        url=url,
        settings=browser_settings
    )
    
    # Set handlers
    load_handler = LoadHandler(browser, offline_db, sync_manager)
    browser.SetClientHandler(load_handler)
    
    request_handler = RequestHandler(url, offline_db)
    browser.SetClientHandler(request_handler)
    
    return browser

def check_app_dependencies():
    """Check if all required dependencies are installed"""
    try:
        # Check if Flask is installed
        import flask
        logger.info("Flask is installed")
        
        # Check if SQLAlchemy is installed (used by the Flask app)
        import sqlalchemy
        logger.info("SQLAlchemy is installed")
        
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        return False

def install_missing_dependencies():
    """Install missing dependencies"""
    logger.info("Installing missing dependencies...")
    
    dependencies = [
        "flask==2.2.5",
        "flask_sqlalchemy==3.0.5",
        "flask_login==0.6.2",
        "werkzeug==2.2.3",
        "SQLAlchemy==2.0.21",
        "requests==2.28.2"
    ]
    
    try:
        import pip
        for dep in dependencies:
            logger.info(f"Installing {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
        return True
    except Exception as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False

def handle_close(flask_process, browser):
    """Handle application close"""
    # Ensure browser is properly shut down
    if browser:
        browser.CloseBrowser(True)
    
    # Ensure Flask server is terminated
    if flask_process:
        logger.info("Terminating Flask server")
        if platform.system() == "Windows":
            # On Windows, we need to use taskkill to ensure the process and its children are terminated
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(flask_process.pid)])
        else:
            # On Unix systems, terminate process group
            os.killpg(os.getpgid(flask_process.pid), signal.SIGTERM)

def main():
    """Main function to run the desktop application"""
    parser = argparse.ArgumentParser(description='AMRS Maintenance Tracker Desktop App')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--port', type=int, help='Port to use for Flask server')
    args = parser.parse_args()
    
    global DEBUG
    DEBUG = args.debug
    
    try:
        logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
        
        # Check dependencies
        if not check_app_dependencies():
            if not install_missing_dependencies():
                logger.error("Failed to install dependencies. Please install manually.")
                return 1
        
        # Initialize offline database
        logger.info("Initializing offline database")
        offline_db = OfflineDatabase(OFFLINE_DB_PATH)
        
        # Get port for Flask server
        port = args.port or get_available_port()
        
        # Start Flask server
        logger.info(f"Starting Flask server on port {port}")
        flask_process = start_flask_server(port, DEBUG)
        if not flask_process:
            logger.error("Failed to start Flask server. Exiting.")
            return 1
        
        # Wait for Flask server to start
        if not wait_for_flask_server(port, timeout=30):
            logger.error("Flask server did not start in time. Exiting.")
            if flask_process:
                flask_process.terminate()
            return 1
        
        # Setup CEF
        logger.info("Setting up CEF")
        setup_cef()
        
        # Set up base URL and create sync manager
        base_url = f"http://localhost:{port}"
        sync_manager = SyncManager(offline_db, base_url)
        
        # Create browser window
        logger.info("Creating browser window")
        browser = create_browser_window(base_url, offline_db, sync_manager)
        
        # Set up close handler
        def app_exit():
            handle_close(flask_process, browser)
        cef.SetExitHandler(app_exit)
        
        # Start CEF message loop
        logger.info("Starting CEF message loop")
        cef.MessageLoop()
        
        # Clean up after message loop ends
        cef.Shutdown()
        
        # Ensure Flask process is terminated
        if flask_process:
            flask_process.terminate()
        
        logger.info("Application closed")
        return 0
        
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
