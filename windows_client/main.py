import sys
import os
import json
import requests
import platform
import webbrowser
import configparser
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from datetime import datetime
from functools import partial

# Try to import optional modules with fallbacks
try:
    import keyring
    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False
    print("Warning: keyring module not available. Password saving disabled.")

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QLineEdit, QMessageBox, QTableWidget, 
                            QTableWidgetItem, QComboBox, QCheckBox, QTabWidget, 
                            QSplashScreen, QSizePolicy, QDialog, QFormLayout, QSpinBox, 
                            QTextEdit, QScrollArea, QGroupBox, QHeaderView, 
                            QStackedWidget, QSystemTrayIcon, QMenu, QStatusBar, QStyle,
                            QPlainTextEdit, QProgressBar)

from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer, QUrl, QSettings
from PyQt6.QtGui import QIcon, QFont, QPixmap, QDesktopServices, QAction, QColor, QFontDatabase

from logger_config import setup_logging, get_logger

# App version
APP_VERSION = "1.0.0"
APP_NAME = "Maintenance Tracker Client"
CONFIG_FILE = "config.ini"
TOKEN_FILE = "session.token"

# Set up logging
log_file = setup_logging(APP_NAME)
logger = get_logger(__name__)

# Custom theme colors
THEME = {
    "primary": "#3498db",
    "secondary": "#2980b9",
    "accent": "#27ae60",
    "background": "#f8f9fa",
    "card": "#ffffff",
    "text": "#333333",
    "text_light": "#666666",
    "danger": "#e74c3c",
    "warning": "#f1c40f"
}

# Function to get the pre-configured server URL if it exists
def get_preconfigured_server_url():
    """Get the server URL that was configured during build"""
    try:
        # Look for server_config.json in the same directory as the executable
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        config_path = os.path.join(exe_dir, "server_config.json")
        
        # Try the package resources if not found (when running as a bundled app)
        if not os.path.exists(config_path):
            try:
                # When packaged with PyInstaller
                config_path = os.path.join(sys._MEIPASS, "server_config.json")
            except:
                pass
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                if config.get("preconfigured") and config.get("server_url"):
                    logger.info(f"Using pre-configured server URL: {config['server_url']}")
                    return config["server_url"]
    except Exception as e:
        logger.error(f"Error reading pre-configured server URL: {e}")
    
    return None

# Determine if running in portable mode
def is_portable_mode():
    """Check if the application is running in portable mode"""
    # Check if portable.txt exists in the same directory as the executable
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    portable_marker = os.path.join(exe_dir, "portable.txt")
    return os.path.exists(portable_marker)

# Paths - updated to support portable mode
IS_PORTABLE = is_portable_mode()
logger.info(f"Running in portable mode: {IS_PORTABLE}")

if IS_PORTABLE:
    # In portable mode, store data relative to the executable
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    app_data_path = Path(exe_dir) / "data"
    os.makedirs(app_data_path, exist_ok=True)
    DB_PATH = os.path.join(app_data_path, "offline_cache.db")
    CONFIG_PATH = os.path.join(app_data_path, "config.json")
    logger.info(f"Using portable data path: {app_data_path}")
else:
    # In installed mode, use user's home directory
    app_data_path = Path.home() / "AppData" / "Local" / "MaintenanceTrackerClient"
    os.makedirs(app_data_path, exist_ok=True)
    DB_PATH = os.path.join(os.path.expanduser("~"), ".amrs", "offline_cache.db")
    CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".amrs", "config.json")
    # Ensure offline data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Constants for offline sync
SYNC_INTERVAL = 300  # 5 minutes

DEFAULT_API_URL = get_preconfigured_server_url() or "http://localhost:9000"

class WorkerThread(QThread):
    """Background worker thread for network operations"""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class ApiClient:
    """Client for interacting with the maintenance API"""
    def __init__(self, base_url=DEFAULT_API_URL):
        self.base_url = base_url
        self.token = None
        self.load_token()
        self.initialize_offline_db()
    
    def initialize_offline_db(self):
        """Initialize the offline database"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create tables for offline storage
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
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cached_data (
            endpoint TEXT PRIMARY KEY,
            data TEXT,
            timestamp TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_credentials(self, username, password):
        """Securely save user credentials"""
        try:
            if HAS_KEYRING:
                keyring.set_password("AMRS-Client", username, password)
            else:
                # Fallback to simple encryption or warn user
                logger.warning("Cannot securely store password - keyring module not available")
                # Just save username without password
                
            # Save username to config file
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, 'w') as f:
                json.dump({"last_username": username, "server_url": self.base_url}, f)
                
            return True
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
            return False

    def get_saved_credentials(self):
        """Retrieve saved credentials if available"""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r') as f:
                    config = json.load(f)
                    username = config.get("last_username")
                    if username and HAS_KEYRING:
                        password = keyring.get_password("AMRS-Client", username)
                        if password:
                            return username, password
        except Exception as e:
            logger.error(f"Error retrieving credentials: {e}")
        
        return None, None
    
    def load_token(self):
        """Load saved authentication token if it exists"""
        token_path = app_data_path / TOKEN_FILE
        if token_path.exists():
            with open(token_path, 'r') as f:
                self.token = f.read().strip()
    
    def save_token(self, token):
        """Save authentication token"""
        self.token = token
        token_path = app_data_path / TOKEN_FILE
        with open(token_path, 'w') as f:
            f.write(token)
    
    def clear_token(self):
        """Clear saved authentication token"""
        self.token = None
        token_path = app_data_path / TOKEN_FILE
        if token_path.exists():
            os.remove(token_path)
    
    def make_request(self, method, endpoint, data=None, params=None, json_data=None):
        """Enhanced request method with offline support"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            response = requests.request(
                method, 
                url, 
                headers=headers,
                data=data,
                params=params,
                json=json_data,
                timeout=10
            )
            
            if response.status_code == 401:  # Unauthorized
                self.clear_token()
                raise Exception("Session expired. Please log in again.")
            
            if not response.ok:
                raise Exception(f"API error: {response.status_code} - {response.text}")
            
            if 'application/json' in response.headers.get('Content-Type', ''):
                return response.json()
            return response.text
            
        except requests.RequestException as e:
            if method == 'GET':
                # For GET requests, try to return cached data
                cached_data = self.get_cached_data(endpoint)
                if cached_data:
                    return cached_data
            else:
                # For other requests, store for later sync
                if json_data:
                    self.store_pending_operation(method, endpoint, json_data)
                    return {"success": True, "offline": True, 
                           "message": "Operation stored for later synchronization"}
                    
            # If we got here, we failed
            raise Exception(f"Network error: {str(e)}")
    
    def cache_data(self, endpoint, data):
        """Cache data for offline use"""
        try:
            conn = sqlite3.connect(DB_PATH)
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
            print(f"Error caching data: {e}")
    
    def get_cached_data(self, endpoint):
        """Retrieve cached data for endpoint"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('SELECT data FROM cached_data WHERE endpoint = ?', (endpoint,))
            result = cursor.fetchone()
            
            conn.close()
            
            if result:
                return json.loads(result[0])
        except Exception as e:
            print(f"Error retrieving cached data: {e}")
        
        return None
    
    def store_pending_operation(self, method, endpoint, data):
        """Store an operation to be performed when back online"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            op_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            data_json = json.dumps(data)
            
            cursor.execute('''
            INSERT INTO pending_operations (id, endpoint, method, data, timestamp, synced)
            VALUES (?, ?, ?, ?, ?, 0)
            ''', (op_id, endpoint, method, data_json, timestamp))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            print(f"Error storing operation: {e}")
            return False
    
    def sync_pending_operations(self):
        """Synchronize pending operations with the server"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, endpoint, method, data FROM pending_operations WHERE synced = 0')
            operations = cursor.fetchall()
            
            for op_id, endpoint, method, data_json in operations:
                try:
                    data = json.loads(data_json)
                    response = requests.request(
                        method, 
                        f"{self.base_url}{endpoint}", 
                        json=data,
                        timeout=10
                    )
                    
                    if response.ok:
                        # Mark as synced
                        cursor.execute('UPDATE pending_operations SET synced = 1 WHERE id = ?', (op_id,))
                        conn.commit()
                except Exception as e:
                    print(f"Failed to sync operation {op_id}: {e}")
                    continue
            
            conn.close()
            return True
        except Exception as e:
            print(f"Error during sync: {e}")
            return False
            
    def start_sync_thread(self):
        """Start a background thread for periodic synchronization"""
        def sync_worker():
            while True:
                try:
                    self.sync_pending_operations()
                except Exception as e:
                    print(f"Error in sync thread: {e}")
                
                time.sleep(SYNC_INTERVAL)
        
        thread = threading.Thread(target=sync_worker, daemon=True)
        thread.start()
        return thread
    
    def login(self, username, password):
        """Authenticate with the API"""
        data = {
            'username': username,
            'password': password
        }
        response = self.make_request('POST', '/api/login', json_data=data)
        if 'token' in response:mpting login to {self.base_url}/api/login")
            self.save_token(response['token'])', '/api/login', json_data=data)
            return response
        raise Exception("Invalid login response from server")
            logger.debug(f"Login response: {response}")
    def get_dashboard_data(self):
        """Get dashboard summary data""" string (might be HTML or plain text error)
        return self.make_request('GET', '/api/dashboard')
                # Try to see if this is JSON string that wasn't parsed
    def get_sites(self):
        """Get all sites"""json
        return self.make_request('GET', '/api/sites')
                except:
    def get_site(self, site_id):(f"Non-JSON response received: {response[:100]}...")
        """Get site details"""ption(f"Server returned invalid response format. Check server URL.")
        return self.make_request('GET', f'/api/sites/{site_id}')
            # Check for token - could be in different formats based on API design
    def get_machines(self, site_id=None):
        """Get machines, optionally filtered by site"""
        params = {}urn response
        if site_id:ccess_token' in response:
            params['site_id'] = site_ide['access_token'])
        return self.make_request('GET', '/api/machines', params=params)ze for our app
                return response
    def get_machine(self, machine_id):d 'token' in response['data']:
        """Get machine details with parts"""ta']['token'])
        return self.make_request('GET', f'/api/machines/{machine_id}')lize for our app
                return response
    def get_parts(self, machine_id=None):
        """Get parts, optionally filtered by machine"""mats
        params = {}or_msg = "Invalid credentials or server response format"
        if machine_id:ror' in response:
            params['machine_id'] = machine_idor']
        return self.make_request('GET', '/api/parts', params=params)
                    error_msg = response['message']
    def record_maintenance(self, part_id, notes):
        """Record maintenance for a part"""etail']
        data = {
            'part_id': part_id,Login failed: {error_msg}")
            'notes': notesor(f"Full response: {response}")
        }       raise Exception(f"Login failed: {error_msg}")
        return self.make_request('POST', '/api/maintenance/record', json_data=data)
                except Exception as e:
    def verify_connection(self):elf):dy our custom exception, re-raise it
        """Verify connection to the server"""r and get API info"""ailed:"):
        try:
            response = requests.get(self.base_url, timeout=5)        # First try a simple health check endpoint        # Otherwise, provide a more specific message
            if response.ok:pi/health', '/health', '/api/v1/health', '/api/status']ror: {str(e)}")
                return {"status": "connected", "url": self.base_url}r: {str(e)}")
            return {"status": "reachable", "url": self.base_url, "content_type": response.headers.get("Content-Type", "")}ndpoints:
        except Exception as e:(self):
            return {"status": "failed", "url": self.base_url, "error": str(e)}                response = requests.get(    """Get dashboard summary data"""
 f"{self.base_url}{endpoint}", e_request('GET', '/api/dashboard')
class LoginWindow(QWidget):
    """Login window for authentication"""
    login_successful = pyqtSignal(dict)
                    return {return self.make_request('GET', '/api/sites')
    def __init__(self, api_client):       'status': 'connected',
        super().__init__()rl': self.base_url,):
        self.api_client = api_client
        self.setup_ui()                    'response': response.text[:100]return self.make_request('GET', f'/api/sites/{site_id}')
        }
    def setup_ui(self):
        """Set up the login UI"""
        self.setWindowTitle(f"{APP_NAME} - Login")
        self.setFixedSize(400, 300)ail, try to at least connect to the base URL
        get(self.base_url, timeout=5)site_id
        # Main layoutarams=params)
        layout = QVBoxLayout(),
        layout.setContentsMargins(40, 40, 40, 40)        'url': self.base_url,get_machine(self, machine_id):
        de,
        # Logo/Titlepe', 'unknown')_id}')
        title_label = QLabel("Maintenance Tracker")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)    get_parts(self, machine_id=None):
        title_font = QFont():lly filtered by machine"""
        title_font.setPointSize(18)    return {params = {}
        title_font.setBold(True)
        title_label.setFont(title_font)chine_id
        layout.addWidget(title_label)ts', params=params)
        
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)ogin window for authentication"""data = {
        
        layout.addSpacing(20)
        ient):
        # Server URL - make it read-only if pre-configuredjson_data=data)
        server_layout = QHBoxLayout()
        server_label = QLabel("Server:")
        self.server_input = QLineEdit() window for authentication"""
        self.server_input.setText(self.api_client.base_url)
        self.server_input.setPlaceholderText("http://localhost:9000")
        } - Login")
        # If using a pre-configured URL, disable the fieldself.setFixedSize(400, 300)super().__init__()
        preconfigured_url = get_preconfigured_server_url()
        if preconfigured_url:
            self.server_input.setReadOnly(True)
            self.server_input.setStyleSheet("background-color: #f0f0f0;")
            self.server_input.setToolTip("This server URL is pre-configured and cannot be changed")
        
        server_layout.addWidget(server_label)title_label = QLabel("Maintenance Tracker")self.setFixedSize(400, 300)
        server_layout.addWidget(self.server_input)lignment(Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(server_layout)
        
        # Add Test Connection button next to server input
        server_buttons_layout = QHBoxLayout()
        self.test_connection_button = QPushButton("Test Connection")
        self.test_connection_button.clicked.connect(self.test_connection)
        server_buttons_layout.addStretch()version_label = QLabel(f"v{APP_VERSION}")title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        server_buttons_layout.addWidget(self.test_connection_button)nment(Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(server_buttons_layout)layout.addWidget(version_label)title_font.setPointSize(18)
        
        # Username field
        username_label = QLabel("Username:")
        self.username_input = QLineEdit()# Server URL - make it read-only if pre-configured
        self.username_input.setPlaceholderText("Enter username")= QHBoxLayout()= QLabel(f"v{APP_VERSION}")
        layout.addWidget(username_label)nCenter)
        layout.addWidget(self.username_input)
        _url)
        # Password field
        password_label = QLabel("Password:")
        self.password_input = QLineEdit()# If using a pre-configured URL, disable the field# Server URL - make it read-only if pre-configured
        self.password_input.setPlaceholderText("Enter password")rl = get_preconfigured_server_url() QHBoxLayout()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(password_label)
        layout.addWidget(self.password_input)0f0;")
        etToolTip("This server URL is pre-configured and cannot be changed")aceholderText("http://localhost:9000")
        layout.addSpacing(20)
        server_layout.addWidget(server_label)# If using a pre-configured URL, disable the field
        # Remember me checkboxt.addWidget(self.server_input)d_url = get_preconfigured_server_url()
        self.remember_checkbox = QCheckBox("Remember my credentials")r_layout)
        layout.addWidget(self.remember_checkbox)            self.server_input.setReadOnly(True)
        tStyleSheet("background-color: #f0f0f0;")
        # Login buttonme:")p("This server URL is pre-configured and cannot be changed")
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.attempt_login) username")
        # Connect Enter key in password field to login
        self.password_input.returnPressed.connect(self.login_button.click)layout.addWidget(self.username_input)layout.addLayout(server_layout)
        layout.addWidget(self.login_button)
        
        # Error messageword_label = QLabel("Password:")name_label = QLabel("Username:")
        self.error_label = QLabel()= QLineEdit()= QLineEdit()
        self.error_label.setStyleSheet("color: red;")Enter password")Enter username")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)it.EchoMode.Password)
        self.error_label.hide()
        layout.addWidget(self.error_label)assword_input)
        # Password field
        # Set layout
        self.setLayout(layout)
    # Remember me checkboxself.password_input.setPlaceholderText("Enter password")
    def test_connection(self):ox("Remember my credentials")QLineEdit.EchoMode.Password)
        """Test connection to the server"""
        server_url = self.server_input.text().strip()f.password_input)
        if not server_url:# Login button
            QMessageBox.warning(self, "Error", "Please enter a server URL first")
            return.attempt_login)
        
        # Update the button stateself.password_input.returnPressed.connect(self.login_button.click)self.remember_checkbox = QCheckBox("Remember my credentials")
        self.test_connection_button.setEnabled(False)
        self.test_connection_button.setText("Testing...")
        
        # Create a temporary API client for testingel()shButton("Login")
        temp_api = ApiClient(server_url)self.error_label.setStyleSheet("color: red;")self.login_button.clicked.connect(self.attempt_login)
        t(Qt.AlignmentFlag.AlignCenter)ord field to login
        # Use a worker thread to avoid UI freeze
        self.test_worker = WorkerThread(temp_api.verify_connection)
        self.test_worker.finished.connect(self.on_connection_test_result)
        self.test_worker.error.connect(self.on_connection_test_error)
        self.test_worker.start()    self.setLayout(layout)    self.error_label = QLabel()
    
    def on_connection_test_result(self, result):mentFlag.AlignCenter)
        """Handle connection test result"""
        self.test_connection_button.setEnabled(True)nd not pre-configured
        self.test_connection_button.setText("Test Connection")).strip()
            preconfigured_url = get_preconfigured_server_url()    # Set layout
        if result['status'] == 'connected':
            QMessageBox.information( and server_url and server_url != self.api_client.base_url:
                self, ver_url
                "Connection Successful", 
                f"Successfully connected to the server at {result['url']}" pre-configured
            )        config = configparser.ConfigParser()    server_url = self.server_input.text().strip()
        elif result['status'] == 'reachable':: server_url}econfigured_server_url()
            QMessageBox.warning( / CONFIG_FILE, 'w') as f:
                self,  server_url != self.api_client.base_url:
                "Server Reachable", 
                f"Server at {result['url']} is reachable, but API endpoints may not be available.\n\n"        username = self.username_input.text().strip()            
                f"Content type: {result['content_type']}"ut.text()
            )
        else:
            QMessageBox.critical(        self.show_error("Please enter both username and password.")        with open(app_data_path / CONFIG_FILE, 'w') as f:
                self, 
                "Connection Failed", 
                f"Could not connect to the server at {result['url']}\n\nError: {result['error']}" save credentialsut.text().strip()
            )r_checkbox.isChecked():.password_input.text()
            self.api_client.save_credentials(username, password)    
    def on_connection_test_error(self, error_message):d:
        """Handle connection test error"""ton and show loading state("Please enter both username and password.")
        self.test_connection_button.setEnabled(True)nabled(False)
        self.test_connection_button.setText("Test Connection")self.login_button.setText("Logging in...")
        QMessageBox.critical(self, "Connection Test Failed", f"Error: {error_message}").hide() is checked, save credentials
    
    def attempt_login(self):# Login in background thread    self.api_client.save_credentials(username, password)
        """Handle login button click""" WorkerThread(self.api_client.login, username, password)
        # Only update API URL if changed and not pre-configuredt(self.on_login_success)show loading state
        server_url = self.server_input.text().strip()lf.on_login_error)(False)
        preconfigured_url = get_preconfigured_server_url().")
        
        if not preconfigured_url and server_url and server_url != self.api_client.base_url:
            self.api_client.base_url = server_url
            ient.login, username, password)
            # Save to configself.login_button.setText("Login")self.worker.finished.connect(self.on_login_success)
            config = configparser.ConfigParser()ssful.emit(response)r.connect(self.on_login_error)
            config['API'] = {'url': server_url}
            with open(app_data_path / CONFIG_FILE, 'w') as f:):
                config.write(f)
        
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:show_error(self, message):
            self.show_error("Please enter both username and password.")sage""" error_message):
            returne)
        self.error_label.show()self.login_button.setEnabled(True)
        # If remember me is checked, save credentials
        if self.remember_checkbox.isChecked():
            self.api_client.save_credentials(username, password)nd marking them complete"""
          # Signal when maintenance is recorded
        # Disable login button and show loading state
        self.login_button.setEnabled(False)
        self.login_button.setText("Logging in...")
        self.error_label.hide()
        self.setup_ui()intenanceChecklist(QWidget):
        # Login in background thread
        self.worker = WorkerThread(self.api_client.login, username, password)ed
        self.worker.finished.connect(self.on_login_success)
        self.worker.error.connect(self.on_login_error)
        self.worker.start()super().__init__()
    
    def on_login_success(self, response):
        """Handle successful login"""
        self.login_button.setEnabled(True)
        self.login_button.setText("Login")site_layout = QHBoxLayout()"""Set up the UI"""
        self.login_successful.emit(response)
    self.site_combo = QComboBox()
    def on_login_error(self, error_message):bo.currentIndexChanged.connect(self.on_site_changed)ion
        """Handle login error"""
        self.login_button.setEnabled(True)mbo)
        self.login_button.setText("Login")
        self.show_error(error_message)
    Machine filterte_label = QLabel("Site:")
    def show_error(self, message):
        """Display error message"""
        self.error_label.setText(message)
        self.error_label.show()

class MaintenanceChecklist(QWidget):
    """Widget for displaying maintenance items and marking them complete"""yout)
    maintenance_recorded = pyqtSignal(int)  # Signal when maintenance is recordedmachine_layout = QHBoxLayout()
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.setup_ui()status_layout = QHBoxLayout()machine_layout.addWidget(self.machine_combo)
    erdue = QCheckBox("Overdue")t.addLayout(machine_layout)
    def setup_ui(self):hecked(True)
        """Set up the UI"""    self.show_due_soon = QCheckBox("Due Soon")    # Add filter section
        layout = QVBoxLayout()on.setChecked(True)(filter_layout)
        x("Ok")
        # Filter sectionlse)
        filter_layout = QHBoxLayout()
        
        # Site filter
        site_layout = QHBoxLayout()dget(self.show_ok)= QCheckBox("Due Soon")
        site_label = QLabel("Site:")    status_layout.addStretch()    self.show_due_soon.setChecked(True)
        self.site_combo = QComboBox()
        self.site_combo.currentIndexChanged.connect(self.on_site_changed)
        site_layout.addWidget(site_label)nect(self.refresh_parts)
        site_layout.addWidget(self.site_combo)eChanged.connect(self.refresh_parts)(self.show_overdue)
        filter_layout.addLayout(site_layout)efresh_parts)on)
        status_layout.addWidget(self.show_ok)
        # Machine filter_layout)h()
        machine_layout = QHBoxLayout()
        machine_label = QLabel("Machine:")# Parts table# Connect status filters
        self.machine_combo = QComboBox()e = QTableWidget()ue.stateChanged.connect(self.refresh_parts)
        self.machine_combo.currentIndexChanged.connect(self.on_machine_changed)lumnCount(6)teChanged.connect(self.refresh_parts)
        machine_layout.addWidget(machine_label)    self.parts_table.setHorizontalHeaderLabels([    self.show_ok.stateChanged.connect(self.refresh_parts)
        machine_layout.addWidget(self.machine_combo) "Site", "Last Maintenance", "Next Due", "Status"
        filter_layout.addLayout(machine_layout)
        SectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        # Add filter sectionself.parts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)# Parts table
        layout.addLayout(filter_layout)tSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        rs(QTableWidget.EditTrigger.NoEditTriggers)t(6)
        # Status filtersetSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)etHorizontalHeaderLabels([
        status_layout = QHBoxLayout().parts_table.itemDoubleClicked.connect(self.on_part_double_clicked)"Part", "Machine", "Site", "Last Maintenance", "Next Due", "Status"
        self.show_overdue = QCheckBox("Overdue")
        self.show_overdue.setChecked(True)
        self.show_due_soon = QCheckBox("Due Soon")
        self.show_due_soon.setChecked(True)= QPushButton("Record Maintenance")rizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.show_ok = QCheckBox("Ok")    self.record_button.clicked.connect(self.on_record_maintenance)    self.parts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.show_ok.setChecked(False)Widget.SelectionBehavior.SelectRows)
        cked)
        status_layout.addWidget(self.show_overdue)
        status_layout.addWidget(self.show_due_soon)
        status_layout.addWidget(self.show_ok)
        status_layout.addStretch()load_data(self):self.record_button = QPushButton("Record Maintenance")
        self.on_record_maintenance)
        # Connect status filters
        self.show_overdue.stateChanged.connect(self.refresh_parts)self.worker = WorkerThread(self.api_client.get_sites)
        self.show_due_soon.stateChanged.connect(self.refresh_parts)finished.connect(self.on_sites_loaded)
        self.show_ok.stateChanged.connect(self.refresh_parts)(lambda err: QMessageBox.critical(self, "Error", f"Failed to load sites: {err}"))
            self.worker.start()
        layout.addLayout(status_layout)
        
        # Parts table loaded"""ground
        self.parts_table = QTableWidget()    # Clear and populate site dropdown    self.worker = WorkerThread(self.api_client.get_sites)
        self.parts_table.setColumnCount(6)r().connect(self.on_sites_loaded)
        self.parts_table.setHorizontalHeaderLabels([(self, "Error", f"Failed to load sites: {err}"))
            "Part", "Machine", "Site", "Last Maintenance", "Next Due", "Status"
        ])for site in sites_data:
        self.parts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)'], site['id'])
        self.parts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.parts_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)ropdown
        self.parts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers).on_site_changed().site_combo.clear()
        self.parts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.parts_table.itemDoubleClicked.connect(self.on_part_double_clicked)
        layout.addWidget(self.parts_table)
        _combo.currentData().addItem(site['name'], site['id'])
        # Record maintenance button        
        self.record_button = QPushButton("Record Maintenance")ound
        self.record_button.clicked.connect(self.on_record_maintenance)
        layout.addWidget(self.record_button) None
        
        # Set layoutself.worker = WorkerThread(self.api_client.get_machines, site_id)"""Handle site selection change"""
        self.setLayout(layout)nect(self.on_machines_loaded)o.currentData()
    onnect(lambda err: QMessageBox.critical(self, "Error", f"Failed to load machines: {err}"))
    def load_data(self): background
        """Load initial data"""
        # Load sites in backgroundlf, machines_data):
        self.worker = WorkerThread(self.api_client.get_sites)andle machines data loaded"""
        self.worker.finished.connect(self.on_sites_loaded)
        self.worker.error.connect(lambda err: QMessageBox.critical(self, "Error", f"Failed to load sites: {err}"))()nect(self.on_machines_loaded)
        self.worker.start()o load machines: {err}"))
    
    def on_sites_loaded(self, sites_data):
        """Handle sites data loaded"""ddItem(machine['name'], machine['id']) machines_data):
        # Clear and populate site dropdownes data loaded"""
        self.site_combo.clear()achine dropdown
        self.site_combo.addItem("All Sites", -1)
        .machine_combo.addItem("All Machines", -1)
        for site in sites_data:
            self.site_combo.addItem(site['name'], site['id'])
        
        # Load machines
        self.on_site_changed()
    efresh parts list based on current filters""".on_machine_changed()
    def on_site_changed(self):machine_combo.currentData()
        """Handle site selection change"""
        site_id = self.site_combo.currentData()ad parts for machine in backgroundandle machine selection change"""
        = -1:  # All machinesrts()
        # Load machines for site in background
        if site_id == -1:  # All sitesesh_parts(self):
            site_id = Noneread(self.api_client.get_parts, machine_id)based on current filters"""
            
        self.worker = WorkerThread(self.api_client.get_machines, site_id)load parts: {err}"))
        self.worker.finished.connect(self.on_machines_loaded).worker.start()ad parts for machine in background
        self.worker.error.connect(lambda err: QMessageBox.critical(self, "Error", f"Failed to load machines: {err}"))
        self.worker.start()
    
    def on_machines_loaded(self, machines_data):ear table.worker = WorkerThread(self.api_client.get_parts, machine_id)
        """Handle machines data loaded"""Count(0)nnect(self.on_parts_loaded)
        # Clear and populate machine dropdown
        self.machine_combo.clear()
        self.machine_combo.addItem("All Machines", -1)
        
        for machine in machines_data:
            self.machine_combo.addItem(machine['name'], machine['id'])
        .parts_table.setRowCount(0)
        # Load partsue.isChecked():
        self.on_machine_changed()
            elif status == 'due_soon' and self.show_due_soon.isChecked():    filtered_parts = []
    def on_machine_changed(self):
        """Handle machine selection change"""lf.show_ok.isChecked():
        self.refresh_parts()
    
    def refresh_parts(self):    if show_part:    if status == 'overdue' and self.show_overdue.isChecked():
        """Refresh parts list based on current filters"""
        machine_id = self.machine_combo.currentData()
        
        # Load parts for machine in backgroundself.parts_table.setRowCount(len(filtered_parts))    elif status == 'ok' and self.show_ok.isChecked():
        if machine_id == -1:  # All machinese(filtered_parts):
            machine_id = None
                    self.parts_table.setItem(row, 0, QTableWidgetItem(part['name']))        if show_part:
        self.worker = WorkerThread(self.api_client.get_parts, machine_id)
        self.worker.finished.connect(self.on_parts_loaded)
        self.worker.error.connect(lambda err: QMessageBox.critical(self, "Error", f"Failed to load parts: {err}"))le.setItem(row, 1, QTableWidgetItem(part['machine_name']))ith filtered parts
        self.worker.start()
    filtered_parts):
    def on_parts_loaded(self, parts_data):
        """Handle parts data loaded"""able.setItem(row, 0, QTableWidgetItem(part['name']))
        # Clear table    # Last maintenance    
        self.parts_table.setRowCount(0)misoformat(part['last_maintenance'])
            self.parts_table.setItem(row, 3, QTableWidgetItem(last_date.strftime("%Y-%m-%d")))    self.parts_table.setItem(row, 1, QTableWidgetItem(part['machine_name']))
        # Filter parts by status
        filtered_parts = []
        for part in parts_data:t_maintenance'])tItem(part['site_name']))
            status = part['status']    self.parts_table.setItem(row, 4, QTableWidgetItem(next_date.strftime("%Y-%m-%d")))    
            show_part = False
            
            if status == 'overdue' and self.show_overdue.isChecked():        status_item = QTableWidgetItem(part['status'].replace('_', ' ').title())        self.parts_table.setItem(row, 3, QTableWidgetItem(last_date.strftime("%Y-%m-%d")))
                show_part = True
            elif status == 'due_soon' and self.show_due_soon.isChecked():r(THEME['danger']))
                show_part = True] == 'due_soon':me.fromisoformat(part['next_maintenance'])
            elif status == 'ok' and self.show_ok.isChecked():EME['warning']))WidgetItem(next_date.strftime("%Y-%m-%d")))
                show_part = Truem(row, 5, status_item)
                        # Status with color
            if show_part: the first column's itemleWidgetItem(part['status'].replace('_', ' ').title())
                filtered_parts.append(part)    self.parts_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, part['id'])    if part['status'] == 'overdue':
        eground(QColor(THEME['danger']))
        # Populate table with filtered parts
        self.parts_table.setRowCount(len(filtered_parts))""round(QColor(THEME['warning']))
        for row, part in enumerate(filtered_parts):# Get the row of the clicked item    self.parts_table.setItem(row, 5, status_item)
            # Part name
            self.parts_table.setItem(row, 0, QTableWidgetItem(part['name']))    # Store part ID in the first column's item
             from the first columns_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, part['id'])
            # Machine nameta(Qt.ItemDataRole.UserRole)
            self.parts_table.setItem(row, 1, QTableWidgetItem(part['machine_name']))item(row, 0).text()item):
            """Handle part double-click"""
            # Site namegcked item
            self.parts_table.setItem(row, 2, QTableWidgetItem(part['site_name']))
            
            # Last maintenanceon_record_maintenance(self):# Get part ID from the first column
            last_date = datetime.fromisoformat(part['last_maintenance'])tenance button click"""table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            self.parts_table.setItem(row, 3, QTableWidgetItem(last_date.strftime("%Y-%m-%d")))# Get selected rowpart_name = self.parts_table.item(row, 0).text()
            rows = self.parts_table.selectionModel().selectedRows()
            # Next due date
            next_date = datetime.fromisoformat(part['next_maintenance'])ection", "Please select a part first.") part_name)
            self.parts_table.setItem(row, 4, QTableWidgetItem(next_date.strftime("%Y-%m-%d")))
            on_record_maintenance(self):
            # Status with color
            status_item = QTableWidgetItem(part['status'].replace('_', ' ').title())
            if part['status'] == 'overdue':# Get part ID from the first columnselected_rows = self.parts_table.selectionModel().selectedRows()
                status_item.setForeground(QColor(THEME['danger']))).data(Qt.ItemDataRole.UserRole)
            elif part['status'] == 'due_soon': 0).text()ction", "Please select a part first.")
                status_item.setForeground(QColor(THEME['warning']))
            self.parts_table.setItem(row, 5, status_item)# Show maintenance dialog
            alog(part_id, part_name)ow()
            # Store part ID in the first column's item
            self.parts_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, part['id'])def show_maintenance_dialog(self, part_id, part_name):    # Get part ID from the first column
    e.UserRole)
    def on_part_double_clicked(self, item):).text()
        """Handle part double-click"""tenance")
        # Get the row of the clicked item
        row = item.row()
        
        # Get part ID from the first column part_name):
        part_id = self.parts_table.item(row, 0).data(Qt.ItemDataRole.UserRole)    # Part name    """Show dialog to record maintenance"""
        part_name = self.parts_table.item(row, 0).text())
        
        # Show maintenance dialog
        self.show_maintenance_dialog(part_id, part_name)
    layout = QVBoxLayout()
    def on_record_maintenance(self):
        """Handle record maintenance button click"""("Maintenance Notes:")
        # Get selected rowlayout.addWidget(notes_label)name_label = QLabel(f"<b>Part:</b> {part_name}")
        selected_rows = self.parts_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a part first.")        notes_edit.setPlaceholderText("Enter maintenance details...")        layout.addSpacing(10)
            returnnotes_edit)
        
        row = selected_rows[0].row() Notes:")
        
        # Get part ID from the first column
        part_id = self.parts_table.item(row, 0).data(Qt.ItemDataRole.UserRole) QHBoxLayout()extEdit()
        part_name = self.parts_table.item(row, 0).text()    cancel_button = QPushButton("Cancel")    notes_edit.setPlaceholderText("Enter maintenance details...")
        licked.connect(dialog.reject)t(notes_edit)
        # Show maintenance dialog
        self.show_maintenance_dialog(part_id, part_name)utton("Record Maintenance")
    submit_button.clicked.connect(lambda: self.submit_maintenance(dialog, part_id, notes_edit.toPlainText()))
    def show_maintenance_dialog(self, part_id, part_name):
        """Show dialog to record maintenance"""cel_button)()
        dialog = QDialog(self)get(submit_button)hButton("Cancel")
        dialog.setWindowTitle("Record Maintenance")out)ct(dialog.reject)
        dialog.setMinimumWidth(400)
        n("Record Maintenance")
        layout = QVBoxLayout()bda: self.submit_maintenance(dialog, part_id, notes_edit.toPlainText()))
        
        # Part namelf, dialog, part_id, notes):et(cancel_button)
        name_label = QLabel(f"<b>Part:</b> {part_name}")button)
        layout.addWidget(name_label)ound)
        cord_maintenance, part_id, notes)
        layout.addSpacing(10)self.worker.finished.connect(lambda _: self.on_maintenance_recorded(dialog, part_id))dialog.setLayout(layout)
        ror.connect(lambda err: QMessageBox.critical(self, "Error", f"Failed to record maintenance: {err}"))
        # Notes field
        notes_label = QLabel("Maintenance Notes:")
        layout.addWidget(notes_label)on_maintenance_recorded(self, dialog, part_id):"""Submit maintenance record"""
        enance recorded successfully"""nance in background
        notes_edit = QTextEdit()
        notes_edit.setPlaceholderText("Enter maintenance details...")intenance recorded successfully.")on_maintenance_recorded(dialog, part_id))
        layout.addWidget(notes_edit)self.worker.error.connect(lambda err: QMessageBox.critical(self, "Error", f"Failed to record maintenance: {err}"))
        st)
        layout.addSpacing(20)
        
        # Buttons# Emit signal that maintenance was recorded"""Handle maintenance recorded successfully"""
        button_layout = QHBoxLayout()d)
        cancel_button = QPushButton("Cancel")nce recorded successfully.")
        cancel_button.clicked.connect(dialog.reject)shboard(QWidget):
        showing summary information"""list
        submit_button = QPushButton("Record Maintenance")
        submit_button.clicked.connect(lambda: self.submit_maintenance(dialog, part_id, notes_edit.toPlainText()))
        ecorded
        button_layout.addWidget(cancel_button)self.setup_ui()self.maintenance_recorded.emit(part_id)
        button_layout.addWidget(submit_button)
        layout.addLayout(button_layout)
        """Set up the dashboard UI"""ashboard widget showing summary information"""
        dialog.setLayout(layout)ent):
        dialog.exec()        super().__init__()
    
    def submit_maintenance(self, dialog, part_id, notes):
        """Submit maintenance record"""nt()
        # Record maintenance in background
        self.worker = WorkerThread(self.api_client.record_maintenance, part_id, notes)) UI"""
        self.worker.finished.connect(lambda _: self.on_maintenance_recorded(dialog, part_id))tle_font)yout()
        self.worker.error.connect(lambda err: QMessageBox.critical(self, "Error", f"Failed to record maintenance: {err}"))
        self.worker.start()
    
    def on_maintenance_recorded(self, dialog, part_id):QWidget()
        """Handle maintenance recorded successfully"""oxLayout()ize(16)
        dialog.accept()ummary_widget.setLayout(summary_layout)font.setBold(True)
        QMessageBox.information(self, "Success", "Maintenance recorded successfully.")tFont(title_font)
        # Overdue cardlayout.addWidget(title)
        # Refresh parts listeate_stat_card("Overdue", "0", THEME["danger"])
        self.refresh_parts()
        self.summary_widget = QWidget()
        # Emit signal that maintenance was recordedoon card_layout = QHBoxLayout()
        self.maintenance_recorded.emit(part_id)reate_stat_card("Due Soon", "0", THEME["warning"])ut(summary_layout)
rd)
class Dashboard(QWidget):
    """Dashboard widget showing summary information"""# Total parts cardself.overdue_card = self.create_stat_card("Overdue", "0", THEME["danger"])
    def __init__(self, api_client):tal_parts_card = self.create_stat_card("Total Parts", "0", THEME["secondary"])_layout.addWidget(self.overdue_card)
        super().__init__()lf.total_parts_card)
        self.api_client = api_client
        self.setup_ui()ry_widget)reate_stat_card("Due Soon", "0", THEME["warning"])
    lf.due_soon_card)
    def setup_ui(self):
        """Set up the dashboard UI"""
        layout = QVBoxLayout()
        f.load_data)l_parts_card)
        # Titlelayout.addWidget(refresh_button)
        title = QLabel("Dashboard")
        title_font = QFont()ch to push everything uppacing(20)
        title_font.setPointSize(16)    layout.addStretch()    
        title_font.setBold(True)
        title.setFont(title_font)d")
        layout.addWidget(title)
        
        # Maintenance summary
        self.summary_widget = QWidget()
        summary_layout = QHBoxLayout()"statCard")
        self.summary_widget.setLayout(summary_layout)    card.setStyleSheet(f"""    
        
        # Overdue card
        self.overdue_card = self.create_stat_card("Overdue", "0", THEME["danger"])-radius: 8px;rd(self, title, value, color):
        summary_layout.addWidget(self.overdue_card)
        
        # Due soon card
        self.due_soon_card = self.create_stat_card("Due Soon", "0", THEME["warning"])            }}        card.setStyleSheet(f"""
        summary_layout.addWidget(self.due_soon_card)
        
        # Total parts card
        self.total_parts_card = self.create_stat_card("Total Parts", "0", THEME["secondary"])tentsMargins(15, 15, 15, 15)t: 5px solid {color};
        summary_layout.addWidget(self.total_parts_card)
        
        layout.addWidget(self.summary_widget)Label(title)
        layout.addSpacing(20)
        (title_label)
        # Refresh button        card_layout = QVBoxLayout()
        refresh_button = QPushButton("Refresh Dashboard")
        refresh_button.clicked.connect(self.load_data)
        layout.addWidget(refresh_button)
        24)le)
        # Add stretch to push everything up
        layout.addStretch()nt)label)
        
        self.setLayout(layout) '_')}_value")
    idget(value_label)abel(value)
    def create_stat_card(self, title, value, color):
        """Create a stat card widget"""    card.setLayout(card_layout)    value_font.setPointSize(24)
        card = QWidget()True)
        card.setObjectName("statCard")
        card.setStyleSheet(f"""")
            #statCard {{ from API"""ame(f"{title.lower().replace(' ', '_')}_value")
                background-color: white;# Start worker thread to fetch datacard_layout.addWidget(value_label)
                border-radius: 8px;.api_client.get_dashboard_data)
                border-left: 5px solid {color};te_dashboard)
                padding: 15px;sageBox.critical(self, "Error", f"Failed to load dashboard: {err}"))
                margin: 5px;self.worker.start()
            }}
        """)
        
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(15, 15, 15, 15)self.overdue_card.findChild(QLabel, "overdue_value").setText(str(data['overdue_count']))self.worker.finished.connect(self.update_dashboard)
        indChild(QLabel, "due_soon_value").setText(str(data['due_soon_count']))nnect(lambda err: QMessageBox.critical(self, "Error", f"Failed to load dashboard: {err}"))
        # Titlecard.findChild(QLabel, "total_parts_value").setText(str(data['total_parts']))()
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666;")inWindow):oard(self, data):
        card_layout.addWidget(title_label)"
        
        # Valueue_count']))
        value_label = QLabel(value)due_soon_count']))
        value_font = QFont()ts']))
        value_font.setPointSize(24)    self.setup_ui()
        value_font.setBold(True)elf.api_client.start_sync_thread()):
        value_label.setFont(value_font)
        value_label.setStyleSheet(f"color: {color}")
        value_label.setObjectName(f"{title.lower().replace(' ', '_')}_value")):
        card_layout.addWidget(value_label)file"""()
        config_path = app_data_path / CONFIG_FILEself.load_config(server_url)
        card.setLayout(card_layout)ts():
        return cardigParser()ient.start_sync_thread()
        config.read(config_path)self.try_auto_login()
    def load_data(self): config and 'url' in config['API']:
        """Load dashboard data from API"""API']['url']
        # Start worker thread to fetch data
        self.worker = WorkerThread(self.api_client.get_dashboard_data)    self.api_client.base_url = server_urlconfig_path = app_data_path / CONFIG_FILE
        self.worker.finished.connect(self.update_dashboard)
        self.worker.error.connect(lambda err: QMessageBox.critical(self, "Error", f"Failed to load dashboard: {err}"))
        self.worker.start()
    self.setWindowTitle(APP_NAME)    if 'API' in config and 'url' in config['API']:
    def update_dashboard(self, data):]
        """Update dashboard with new data"""elif server_url:
        # Update stats
        self.overdue_card.findChild(QLabel, "overdue_value").setText(str(data['overdue_count']))dWidget()
        self.due_soon_card.findChild(QLabel, "due_soon_value").setText(str(data['due_soon_count']))
        self.total_parts_card.findChild(QLabel, "total_parts_value").setText(str(data['total_parts']))
# Create login widgetself.setWindowTitle(APP_NAME)
class MainWindow(QMainWindow):indow(self.api_client)
    """Main application window"""nnect(self.on_login_successful)
    def __init__(self, server_url=None):idget)
        super().__init__()
        self.api_client = ApiClient()# Set up system trayself.setCentralWidget(self.stacked_widget)
        self.load_config(server_url)
        self.setup_ui()# Create login widget
        self.sync_thread = self.api_client.start_sync_thread()
        self.try_auto_login()ful)
        self.setStatusBar(self.status_bar)    self.stacked_widget.addWidget(self.login_widget)
    def load_config(self, server_url):tatus = QLabel("Disconnected")
        """Load configuration from file"""color: red;")
        config_path = app_data_path / CONFIG_FILEf.connection_status)
        if config_path.exists():
            config = configparser.ConfigParser()setup_main_ui(self):# Status bar
            config.read(config_path) UI after login"""QStatusBar()
            if 'API' in config and 'url' in config['API']:telf.status_bar)
                self.api_client.base_url = config['API']['url']self.main_widget = QWidget()self.connection_status = QLabel("Disconnected")
        elif server_url:: red;")
            self.api_client.base_url = server_url
    
    def setup_ui(self):self.tab_widget = QTabWidget()setup_main_ui(self):
        """Set up the main UI"""
        self.setWindowTitle(APP_NAME)
        self.resize(1000, 700)api_client)
        self.tab_widget.addTab(self.dashboard, "Dashboard")main_layout = QVBoxLayout()
        # Create central stacked widget
        self.stacked_widget = QStackedWidget()st tab
        self.setCentralWidget(self.stacked_widget)    self.maintenance_checklist = MaintenanceChecklist(self.api_client)    self.tab_widget = QTabWidget()
        b(self.maintenance_checklist, "Maintenance")
        # Create login widget
        self.login_widget = LoginWindow(self.api_client)
        self.login_widget.login_successful.connect(self.on_login_successful))
        self.stacked_widget.addWidget(self.login_widget)
        us_layout = QHBoxLayout()intenance checklist tab
        # Set up system tray{self.api_client.base_url}")ceChecklist(self.api_client)
        self.setup_tray()
        
        # Status bar
        self.status_bar = QStatusBar()tton("Logout")
        self.setStatusBar(self.status_bar)t_button.clicked.connect(self.logout)tus bar showing connection info
        self.connection_status = QLabel("Disconnected")et(logout_button)Layout()
        self.connection_status.setStyleSheet("color: red;")        server_label = QLabel(f"Connected to: {self.api_client.base_url}")
        self.status_bar.addPermanentWidget(self.connection_status))l)
    
    def setup_main_ui(self):
        """Set up the main UI after login"""    self.stacked_widget.addWidget(self.main_widget)    logout_button = QPushButton("Logout")
        # Create main widget
        self.main_widget = QWidget()
        main_layout = QVBoxLayout()n and menu"""
        stemTrayIcon(self)t(status_layout)
        # Create tab widgete.StandardPixmap.SP_ComputerIcon))
        self.tab_widget = QTabWidget()self.main_widget.setLayout(main_layout)
        ay menud_widget.addWidget(self.main_widget)
        # Dashboard tab
        self.dashboard = Dashboard(self.api_client)
        self.tab_widget.addTab(self.dashboard, "Dashboard")show_action = QAction("Show", self)"""Set up system tray icon and menu"""
        ect(self.show)ayIcon(self)
        # Maintenance checklist tabe.StandardPixmap.SP_ComputerIcon))
        self.maintenance_checklist = MaintenanceChecklist(self.api_client)
        self.tab_widget.addTab(self.maintenance_checklist, "Maintenance")    exit_action = QAction("Exit", self)    # Create tray menu
        ered.connect(QApplication.quit)()
        main_layout.addWidget(self.tab_widget)t_action)
        
        # Status bar showing connection info
        status_layout = QHBoxLayout()
        server_label = QLabel(f"Connected to: {self.api_client.base_url}")    
        status_layout.addWidget(server_label)
        ally using saved credentials"""(QApplication.quit)
        status_layout.addStretch() self.api_client.get_saved_credentials()exit_action)
        logout_button = QPushButton("Logout")
        logout_button.clicked.connect(self.logout)    self.show_status_message("Attempting automatic login...")self.tray_icon.setContextMenu(tray_menu)
        status_layout.addWidget(logout_button)w()
        ad for login
        main_layout.addLayout(status_layout)i_client.login, username, password)
            self.worker.finished.connect(lambda _: self.on_auto_login_success())"""Attempt to login automatically using saved credentials"""
        self.main_widget.setLayout(main_layout)ect(lambda _: self.show_login())api_client.get_saved_credentials()
        self.stacked_widget.addWidget(self.main_widget)
    
    def setup_tray(self):    self.show_login()    
        """Set up system tray icon and menu"""
        self.tray_icon = QSystemTrayIcon(self)ge):self.api_client.login, username, password)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))bar""" _: self.on_auto_login_success())
        
        # Create tray menu        self.worker.start()
        tray_menu = QMenu()_success(self):
        l automatic login"""()
        show_action = QAction("Show", self)show main UI
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)self.stacked_widget.setCurrentWidget(self.main_widget)"""Show a status message in the status bar"""
        000)
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.quit)    self.dashboard.load_data()def on_auto_login_success(self):
        tray_menu.addAction(exit_action)st.load_data()omatic login"""
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()("Connected")Widget(self.main_widget)
    n;")
    def try_auto_login(self):
        """Attempt to login automatically using saved credentials"""):load_data()
        username, password = self.api_client.get_saved_credentials()en"""hecklist.load_data()
        if username and password:        self.stacked_widget.setCurrentWidget(self.login_widget)        
            self.show_status_message("Attempting automatic login...")f.connection_status.setText("Disconnected")pdate connection status
            etStyleSheet("color: red;")etText("Connected")
            # Create a worker thread for login    self.connection_status.setStyleSheet("color: green;")
            self.worker = WorkerThread(self.api_client.login, username, password)elf, response):
            self.worker.finished.connect(lambda _: self.on_auto_login_success())"
            self.worker.error.connect(lambda _: self.show_login())
            self.worker.start()    self.stacked_widget.setCurrentWidget(self.main_widget)    self.stacked_widget.setCurrentWidget(self.login_widget)
        else:onnected")
            self.show_login()d;")
    
    def show_status_message(self, message):ata()e):
        """Show a status message in the status bar"""ul login"""
        self.status_bar.showMessage(message, 5000)    # Update connection status    self.setup_main_ui()
    tText("Connected")rrentWidget(self.main_widget)
    def on_auto_login_success(self): green;")
        """Handle successful automatic login"""
        # Create and show main UI    # Show welcome message    self.dashboard.load_data()
        self.setup_main_ui()('user', {})ecklist.load_data()
        self.stacked_widget.setCurrentWidget(self.main_widget)er.get('username', 'User')
        ", f"Welcome, {username}!")
        # Load data
        self.dashboard.load_data()ut(self):.connection_status.setStyleSheet("color: green;")
        self.maintenance_checklist.load_data()
        
        # Update connection status
        self.connection_status.setText("Connected")r.get('username', 'User')
        self.connection_status.setStyleSheet("color: green;")ogin screenBox.information(self, "Welcome", f"Welcome, {username}!")
        self.show_login()
    def show_login(self):
        """Show login screen"""
        self.stacked_widget.setCurrentWidget(self.login_widget) window close event"""oken
        self.connection_status.setText("Disconnected")    # Minimize to tray instead of closing    self.api_client.clear_token()
        self.connection_status.setStyleSheet("color: red;").isVisible():
    nformation(self, "Information", en
    def on_login_successful(self, response):                                "Application will keep running in the system tray. To quit, right-click the tray icon and select 'Exit'.")    self.show_login()
        """Handle successful login"""
        self.setup_main_ui()            event.ignore()    def closeEvent(self, event):
        self.stacked_widget.setCurrentWidget(self.main_widget)
        :Minimize to tray instead of closing
        # Load data    app = QApplication(sys.argv)        if self.tray_icon.isVisible():





































































    main()if __name__ == "__main__":    sys.exit(app.exec())        splash.finish(window)    # Close splash screen        window.show()    window = MainWindow(server_url)    # Create and show the main window                pass        except:                server_url = config.get("server_url")                config = json.load(f)            with open(config_path, 'r') as f:        try:    if config_path.exists():    config_path = Path(app_dir, "config.json")    server_url = None    # Load config if exists        app_dir.mkdir(exist_ok=True)    app_dir = Path(os.path.expanduser("~"), ".amrs")    # Setup application directory        splash.show()    splash = QSplashScreen(splash_pixmap)    splash_pixmap.fill(Qt.GlobalColor.white)    splash_pixmap = QPixmap(400, 300)    # Create splash screen        app.setApplicationVersion(APP_VERSION)    app.setApplicationName(APP_NAME)    # Set application details        app = QApplication(sys.argv)def main():            event.ignore()            self.hide()                                    "Application will keep running in the system tray. To quit, right-click the tray icon and select 'Exit'.")            QMessageBox.information(self, "Information",         if self.tray_icon.isVisible():        # Minimize to tray instead of closing        """Handle window close event"""    def closeEvent(self, event):            self.show_login()        # Show login screen                self.api_client.clear_token()        # Clear token        """Handle logout"""    def logout(self):            QMessageBox.information(self, "Welcome", f"Welcome, {username}!")        username = user.get('username', 'User')        user = response.get('user', {})        # Show welcome message                self.connection_status.setStyleSheet("color: green;")        self.connection_status.setText("Connected")        # Update connection status                self.maintenance_checklist.load_data()        self.dashboard.load_data()





































    main()if __name__ == "__main__":    sys.exit(app.exec())        splash.finish(window)    # Close splash screen        window.show()    window = MainWindow(server_url)    # Create and show the main window                pass        except:                server_url = config.get("server_url")                config = json.load(f)            with open(config_path, 'r') as f:        try:    if config_path.exists():    config_path = Path(app_dir, "config.json")    server_url = None    # Load config if exists        app_dir.mkdir(exist_ok=True)    app_dir = Path(os.path.expanduser("~"), ".amrs")    # Setup application directory        splash.show()    splash = QSplashScreen(splash_pixmap)    splash_pixmap.fill(Qt.GlobalColor.white)    splash_pixmap = QPixmap(400, 300)    # Create splash screen        app.setApplicationVersion(APP_VERSION)    app.setApplicationName(APP_NAME)    # Set application details                QMessageBox.information(self, "Information", 
                                    "Application will keep running in the system tray. To quit, right-click the tray icon and select 'Exit'.")
            self.hide()
            event.ignore()

def main():
    app = QApplication(sys.argv)
    
    # Set application details
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    # Create splash screen
    splash_pixmap = QPixmap(400, 300)
    splash_pixmap.fill(Qt.GlobalColor.white)
    splash = QSplashScreen(splash_pixmap)
    splash.show()
    
    # Setup application directory
    app_dir = Path(os.path.expanduser("~"), ".amrs")
    app_dir.mkdir(exist_ok=True)
    
    # Load config if exists
    server_url = None
    config_path = Path(app_dir, "config.json")
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                server_url = config.get("server_url")
        except:
            pass
    
    # Create and show the main window
    window = MainWindow(server_url)
    window.show()
    
    # Close splash screen
    splash.finish(window)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
