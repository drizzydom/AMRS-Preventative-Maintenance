import sys
import os
import json
import requests
import platform
import webbrowser
import configparser
import sqlite3
import keyring
import threading
import time
import uuid
from pathlib import Path
from datetime import datetime
from functools import partial

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
DEFAULT_API_URL = "http://localhost:9000"  # Default to Docker container port
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
            keyring.set_password("AMRS-Client", username, password)
            
            # Save username to config file
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, 'w') as f:
                json.dump({"last_username": username, "server_url": self.base_url}, f)
                
            return True
        except Exception as e:
            print(f"Error saving credentials: {e}")
            return False

    def get_saved_credentials(self):
        """Retrieve saved credentials if available"""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r') as f:
                    config = json.load(f)
                    username = config.get("last_username")
                    if username:
                        password = keyring.get_password("AMRS-Client", username)
                        if password:
                            return username, password
        except Exception as e:
            print(f"Error retrieving credentials: {e}")
        
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
        if 'token' in response:
            self.save_token(response['token'])
            return response
        raise Exception("Invalid login response from server")
    
    def get_dashboard_data(self):
        """Get dashboard summary data"""
        return self.make_request('GET', '/api/dashboard')
    
    def get_sites(self):
        """Get all sites"""
        return self.make_request('GET', '/api/sites')
    
    def get_site(self, site_id):
        """Get site details"""
        return self.make_request('GET', f'/api/sites/{site_id}')
    
    def get_machines(self, site_id=None):
        """Get machines, optionally filtered by site"""
        params = {}
        if site_id:
            params['site_id'] = site_id
        return self.make_request('GET', '/api/machines', params=params)
    
    def get_machine(self, machine_id):
        """Get machine details with parts"""
        return self.make_request('GET', f'/api/machines/{machine_id}')
    
    def get_parts(self, machine_id=None):
        """Get parts, optionally filtered by machine"""
        params = {}
        if machine_id:
            params['machine_id'] = machine_id
        return self.make_request('GET', '/api/parts', params=params)
    
    def record_maintenance(self, part_id, notes):
        """Record maintenance for a part"""
        data = {
            'part_id': part_id,
            'notes': notes
        }
        return self.make_request('POST', '/api/maintenance/record', json_data=data)

class LoginWindow(QWidget):
    """Login window for authentication"""
    login_successful = pyqtSignal(dict)
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the login UI"""
        self.setWindowTitle(f"{APP_NAME} - Login")
        self.setFixedSize(400, 300)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Logo/Title
        title_label = QLabel("Maintenance Tracker")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        
        layout.addSpacing(20)
        
        # Server URL
        server_layout = QHBoxLayout()
        server_label = QLabel("Server:")
        self.server_input = QLineEdit()
        self.server_input.setText(self.api_client.base_url)
        self.server_input.setPlaceholderText("http://localhost:9000")
        server_layout.addWidget(server_label)
        server_layout.addWidget(self.server_input)
        layout.addLayout(server_layout)
        
        # Username field
        username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        layout.addWidget(username_label)
        layout.addWidget(self.username_input)
        
        # Password field
        password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(password_label)
        layout.addWidget(self.password_input)
        
        layout.addSpacing(20)
        
        # Remember me checkbox
        self.remember_checkbox = QCheckBox("Remember my credentials")
        layout.addWidget(self.remember_checkbox)
        
        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.attempt_login)
        # Connect Enter key in password field to login
        self.password_input.returnPressed.connect(self.login_button.click)
        layout.addWidget(self.login_button)
        
        # Error message
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # Set layout
        self.setLayout(layout)
    
    def attempt_login(self):
        """Handle login button click"""
        # Update API URL if changed
        server_url = self.server_input.text().strip()
        if server_url and server_url != self.api_client.base_url:
            self.api_client.base_url = server_url
            
            # Save to config
            config = configparser.ConfigParser()
            config['API'] = {'url': server_url}
            with open(app_data_path / CONFIG_FILE, 'w') as f:
                config.write(f)
        
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            self.show_error("Please enter both username and password.")
            return
        
        # If remember me is checked, save credentials
        if self.remember_checkbox.isChecked():
            self.api_client.save_credentials(username, password)
        
        # Disable login button and show loading state
        self.login_button.setEnabled(False)
        self.login_button.setText("Logging in...")
        self.error_label.hide()
        
        # Login in background thread
        self.worker = WorkerThread(self.api_client.login, username, password)
        self.worker.finished.connect(self.on_login_success)
        self.worker.error.connect(self.on_login_error)
        self.worker.start()
    
    def on_login_success(self, response):
        """Handle successful login"""
        self.login_button.setEnabled(True)
        self.login_button.setText("Login")
        self.login_successful.emit(response)
    
    def on_login_error(self, error_message):
        """Handle login error"""
        self.login_button.setEnabled(True)
        self.login_button.setText("Login")
        self.show_error(error_message)
    
    def show_error(self, message):
        """Display error message"""
        self.error_label.setText(message)
        self.error_label.show()

class MaintenanceChecklist(QWidget):
    """Widget for displaying maintenance items and marking them complete"""
    maintenance_recorded = pyqtSignal(int)  # Signal when maintenance is recorded
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI"""
        layout = QVBoxLayout()
        
        # Filter section
        filter_layout = QHBoxLayout()
        
        # Site filter
        site_layout = QHBoxLayout()
        site_label = QLabel("Site:")
        self.site_combo = QComboBox()
        self.site_combo.currentIndexChanged.connect(self.on_site_changed)
        site_layout.addWidget(site_label)
        site_layout.addWidget(self.site_combo)
        filter_layout.addLayout(site_layout)
        
        # Machine filter
        machine_layout = QHBoxLayout()
        machine_label = QLabel("Machine:")
        self.machine_combo = QComboBox()
        self.machine_combo.currentIndexChanged.connect(self.on_machine_changed)
        machine_layout.addWidget(machine_label)
        machine_layout.addWidget(self.machine_combo)
        filter_layout.addLayout(machine_layout)
        
        # Add filter section
        layout.addLayout(filter_layout)
        
        # Status filters
        status_layout = QHBoxLayout()
        self.show_overdue = QCheckBox("Overdue")
        self.show_overdue.setChecked(True)
        self.show_due_soon = QCheckBox("Due Soon")
        self.show_due_soon.setChecked(True)
        self.show_ok = QCheckBox("Ok")
        self.show_ok.setChecked(False)
        
        status_layout.addWidget(self.show_overdue)
        status_layout.addWidget(self.show_due_soon)
        status_layout.addWidget(self.show_ok)
        status_layout.addStretch()
        
        # Connect status filters
        self.show_overdue.stateChanged.connect(self.refresh_parts)
        self.show_due_soon.stateChanged.connect(self.refresh_parts)
        self.show_ok.stateChanged.connect(self.refresh_parts)
        
        layout.addLayout(status_layout)
        
        # Parts table
        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(6)
        self.parts_table.setHorizontalHeaderLabels([
            "Part", "Machine", "Site", "Last Maintenance", "Next Due", "Status"
        ])
        self.parts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.parts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.parts_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.parts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.parts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.parts_table.itemDoubleClicked.connect(self.on_part_double_clicked)
        layout.addWidget(self.parts_table)
        
        # Record maintenance button
        self.record_button = QPushButton("Record Maintenance")
        self.record_button.clicked.connect(self.on_record_maintenance)
        layout.addWidget(self.record_button)
        
        # Set layout
        self.setLayout(layout)
    
    def load_data(self):
        """Load initial data"""
        # Load sites in background
        self.worker = WorkerThread(self.api_client.get_sites)
        self.worker.finished.connect(self.on_sites_loaded)
        self.worker.error.connect(lambda err: QMessageBox.critical(self, "Error", f"Failed to load sites: {err}"))
        self.worker.start()
    
    def on_sites_loaded(self, sites_data):
        """Handle sites data loaded"""
        # Clear and populate site dropdown
        self.site_combo.clear()
        self.site_combo.addItem("All Sites", -1)
        
        for site in sites_data:
            self.site_combo.addItem(site['name'], site['id'])
        
        # Load machines
        self.on_site_changed()
    
    def on_site_changed(self):
        """Handle site selection change"""
        site_id = self.site_combo.currentData()
        
        # Load machines for site in background
        if site_id == -1:  # All sites
            site_id = None
            
        self.worker = WorkerThread(self.api_client.get_machines, site_id)
        self.worker.finished.connect(self.on_machines_loaded)
        self.worker.error.connect(lambda err: QMessageBox.critical(self, "Error", f"Failed to load machines: {err}"))
        self.worker.start()
    
    def on_machines_loaded(self, machines_data):
        """Handle machines data loaded"""
        # Clear and populate machine dropdown
        self.machine_combo.clear()
        self.machine_combo.addItem("All Machines", -1)
        
        for machine in machines_data:
            self.machine_combo.addItem(machine['name'], machine['id'])
        
        # Load parts
        self.on_machine_changed()
    
    def on_machine_changed(self):
        """Handle machine selection change"""
        self.refresh_parts()
    
    def refresh_parts(self):
        """Refresh parts list based on current filters"""
        machine_id = self.machine_combo.currentData()
        
        # Load parts for machine in background
        if machine_id == -1:  # All machines
            machine_id = None
            
        self.worker = WorkerThread(self.api_client.get_parts, machine_id)
        self.worker.finished.connect(self.on_parts_loaded)
        self.worker.error.connect(lambda err: QMessageBox.critical(self, "Error", f"Failed to load parts: {err}"))
        self.worker.start()
    
    def on_parts_loaded(self, parts_data):
        """Handle parts data loaded"""
        # Clear table
        self.parts_table.setRowCount(0)
        
        # Filter parts by status
        filtered_parts = []
        for part in parts_data:
            status = part['status']
            show_part = False
            
            if status == 'overdue' and self.show_overdue.isChecked():
                show_part = True
            elif status == 'due_soon' and self.show_due_soon.isChecked():
                show_part = True
            elif status == 'ok' and self.show_ok.isChecked():
                show_part = True
                
            if show_part:
                filtered_parts.append(part)
        
        # Populate table with filtered parts
        self.parts_table.setRowCount(len(filtered_parts))
        for row, part in enumerate(filtered_parts):
            # Part name
            self.parts_table.setItem(row, 0, QTableWidgetItem(part['name']))
            
            # Machine name
            self.parts_table.setItem(row, 1, QTableWidgetItem(part['machine_name']))
            
            # Site name
            self.parts_table.setItem(row, 2, QTableWidgetItem(part['site_name']))
            
            # Last maintenance
            last_date = datetime.fromisoformat(part['last_maintenance'])
            self.parts_table.setItem(row, 3, QTableWidgetItem(last_date.strftime("%Y-%m-%d")))
            
            # Next due date
            next_date = datetime.fromisoformat(part['next_maintenance'])
            self.parts_table.setItem(row, 4, QTableWidgetItem(next_date.strftime("%Y-%m-%d")))
            
            # Status with color
            status_item = QTableWidgetItem(part['status'].replace('_', ' ').title())
            if part['status'] == 'overdue':
                status_item.setForeground(QColor(THEME['danger']))
            elif part['status'] == 'due_soon':
                status_item.setForeground(QColor(THEME['warning']))
            self.parts_table.setItem(row, 5, status_item)
            
            # Store part ID in the first column's item
            self.parts_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, part['id'])
    
    def on_part_double_clicked(self, item):
        """Handle part double-click"""
        # Get the row of the clicked item
        row = item.row()
        
        # Get part ID from the first column
        part_id = self.parts_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        part_name = self.parts_table.item(row, 0).text()
        
        # Show maintenance dialog
        self.show_maintenance_dialog(part_id, part_name)
    
    def on_record_maintenance(self):
        """Handle record maintenance button click"""
        # Get selected row
        selected_rows = self.parts_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a part first.")
            return
        
        row = selected_rows[0].row()
        
        # Get part ID from the first column
        part_id = self.parts_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        part_name = self.parts_table.item(row, 0).text()
        
        # Show maintenance dialog
        self.show_maintenance_dialog(part_id, part_name)
    
    def show_maintenance_dialog(self, part_id, part_name):
        """Show dialog to record maintenance"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Record Maintenance")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Part name
        name_label = QLabel(f"<b>Part:</b> {part_name}")
        layout.addWidget(name_label)
        
        layout.addSpacing(10)
        
        # Notes field
        notes_label = QLabel("Maintenance Notes:")
        layout.addWidget(notes_label)
        
        notes_edit = QTextEdit()
        notes_edit.setPlaceholderText("Enter maintenance details...")
        layout.addWidget(notes_edit)
        
        layout.addSpacing(20)
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        
        submit_button = QPushButton("Record Maintenance")
        submit_button.clicked.connect(lambda: self.submit_maintenance(dialog, part_id, notes_edit.toPlainText()))
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(submit_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def submit_maintenance(self, dialog, part_id, notes):
        """Submit maintenance record"""
        # Record maintenance in background
        self.worker = WorkerThread(self.api_client.record_maintenance, part_id, notes)
        self.worker.finished.connect(lambda _: self.on_maintenance_recorded(dialog, part_id))
        self.worker.error.connect(lambda err: QMessageBox.critical(self, "Error", f"Failed to record maintenance: {err}"))
        self.worker.start()
    
    def on_maintenance_recorded(self, dialog, part_id):
        """Handle maintenance recorded successfully"""
        dialog.accept()
        QMessageBox.information(self, "Success", "Maintenance recorded successfully.")
        
        # Refresh parts list
        self.refresh_parts()
        
        # Emit signal that maintenance was recorded
        self.maintenance_recorded.emit(part_id)

class Dashboard(QWidget):
    """Dashboard widget showing summary information"""
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the dashboard UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Dashboard")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Maintenance summary
        self.summary_widget = QWidget()
        summary_layout = QHBoxLayout()
        self.summary_widget.setLayout(summary_layout)
        
        # Overdue card
        self.overdue_card = self.create_stat_card("Overdue", "0", THEME["danger"])
        summary_layout.addWidget(self.overdue_card)
        
        # Due soon card
        self.due_soon_card = self.create_stat_card("Due Soon", "0", THEME["warning"])
        summary_layout.addWidget(self.due_soon_card)
        
        # Total parts card
        self.total_parts_card = self.create_stat_card("Total Parts", "0", THEME["secondary"])
        summary_layout.addWidget(self.total_parts_card)
        
        layout.addWidget(self.summary_widget)
        layout.addSpacing(20)
        
        # Refresh button
        refresh_button = QPushButton("Refresh Dashboard")
        refresh_button.clicked.connect(self.load_data)
        layout.addWidget(refresh_button)
        
        # Add stretch to push everything up
        layout.addStretch()
        
        self.setLayout(layout)
    
    def create_stat_card(self, title, value, color):
        """Create a stat card widget"""
        card = QWidget()
        card.setObjectName("statCard")
        card.setStyleSheet(f"""
            #statCard {{
                background-color: white;
                border-radius: 8px;
                border-left: 5px solid {color};
                padding: 15px;
                margin: 5px;
            }}
        """)
        
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666;")
        card_layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet(f"color: {color}")
        value_label.setObjectName(f"{title.lower().replace(' ', '_')}_value")
        card_layout.addWidget(value_label)
        
        card.setLayout(card_layout)
        return card
    
    def load_data(self):
        """Load dashboard data from API"""
        # Start worker thread to fetch data
        self.worker = WorkerThread(self.api_client.get_dashboard_data)
        self.worker.finished.connect(self.update_dashboard)
        self.worker.error.connect(lambda err: QMessageBox.critical(self, "Error", f"Failed to load dashboard: {err}"))
        self.worker.start()
    
    def update_dashboard(self, data):
        """Update dashboard with new data"""
        # Update stats
        self.overdue_card.findChild(QLabel, "overdue_value").setText(str(data['overdue_count']))
        self.due_soon_card.findChild(QLabel, "due_soon_value").setText(str(data['due_soon_count']))
        self.total_parts_card.findChild(QLabel, "total_parts_value").setText(str(data['total_parts']))

class MainWindow(QMainWindow):
    """Main application window"""
    def __init__(self, server_url=None):
        super().__init__()
        self.api_client = ApiClient()
        self.load_config(server_url)
        self.setup_ui()
        self.sync_thread = self.api_client.start_sync_thread()
        self.try_auto_login()
    
    def load_config(self, server_url):
        """Load configuration from file"""
        config_path = app_data_path / CONFIG_FILE
        if config_path.exists():
            config = configparser.ConfigParser()
            config.read(config_path)
            if 'API' in config and 'url' in config['API']:
                self.api_client.base_url = config['API']['url']
        elif server_url:
            self.api_client.base_url = server_url
    
    def setup_ui(self):
        """Set up the main UI"""
        self.setWindowTitle(APP_NAME)
        self.resize(1000, 700)
        
        # Create central stacked widget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create login widget
        self.login_widget = LoginWindow(self.api_client)
        self.login_widget.login_successful.connect(self.on_login_successful)
        self.stacked_widget.addWidget(self.login_widget)
        
        # Set up system tray
        self.setup_tray()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.connection_status = QLabel("Disconnected")
        self.connection_status.setStyleSheet("color: red;")
        self.status_bar.addPermanentWidget(self.connection_status)
    
    def setup_main_ui(self):
        """Set up the main UI after login"""
        # Create main widget
        self.main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Dashboard tab
        self.dashboard = Dashboard(self.api_client)
        self.tab_widget.addTab(self.dashboard, "Dashboard")
        
        # Maintenance checklist tab
        self.maintenance_checklist = MaintenanceChecklist(self.api_client)
        self.tab_widget.addTab(self.maintenance_checklist, "Maintenance")
        
        main_layout.addWidget(self.tab_widget)
        
        # Status bar showing connection info
        status_layout = QHBoxLayout()
        server_label = QLabel(f"Connected to: {self.api_client.base_url}")
        status_layout.addWidget(server_label)
        
        status_layout.addStretch()
        logout_button = QPushButton("Logout")
        logout_button.clicked.connect(self.logout)
        status_layout.addWidget(logout_button)
        
        main_layout.addLayout(status_layout)
        
        self.main_widget.setLayout(main_layout)
        self.stacked_widget.addWidget(self.main_widget)
    
    def setup_tray(self):
        """Set up system tray icon and menu"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def try_auto_login(self):
        """Attempt to login automatically using saved credentials"""
        username, password = self.api_client.get_saved_credentials()
        if username and password:
            self.show_status_message("Attempting automatic login...")
            
            # Create a worker thread for login
            self.worker = WorkerThread(self.api_client.login, username, password)
            self.worker.finished.connect(lambda _: self.on_auto_login_success())
            self.worker.error.connect(lambda _: self.show_login())
            self.worker.start()
        else:
            self.show_login()
    
    def show_status_message(self, message):
        """Show a status message in the status bar"""
        self.status_bar.showMessage(message, 5000)
    
    def on_auto_login_success(self):
        """Handle successful automatic login"""
        # Create and show main UI
        self.setup_main_ui()
        self.stacked_widget.setCurrentWidget(self.main_widget)
        
        # Load data
        self.dashboard.load_data()
        self.maintenance_checklist.load_data()
        
        # Update connection status
        self.connection_status.setText("Connected")
        self.connection_status.setStyleSheet("color: green;")
    
    def show_login(self):
        """Show login screen"""
        self.stacked_widget.setCurrentWidget(self.login_widget)
        self.connection_status.setText("Disconnected")
        self.connection_status.setStyleSheet("color: red;")
    
    def on_login_successful(self, response):
        """Handle successful login"""
        self.setup_main_ui()
        self.stacked_widget.setCurrentWidget(self.main_widget)
        
        # Load data
        self.dashboard.load_data()
        self.maintenance_checklist.load_data()
        
        # Update connection status
        self.connection_status.setText("Connected")
        self.connection_status.setStyleSheet("color: green;")
        
        # Show welcome message
        user = response.get('user', {})
        username = user.get('username', 'User')
        QMessageBox.information(self, "Welcome", f"Welcome, {username}!")
    
    def logout(self):
        """Handle logout"""
        # Clear token
        self.api_client.clear_token()
        
        # Show login screen
        self.show_login()
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Minimize to tray instead of closing
        if self.tray_icon.isVisible():
            QMessageBox.information(self, "Information", 
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
