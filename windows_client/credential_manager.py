import os
import json
import logging
import keyring
import uuid
import time
import hashlib
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                           QPushButton, QCheckBox, QMessageBox, QFormLayout, 
                           QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal

from .security_utils import SecurityUtils

class CredentialManager:
    """
    Secure credential manager for storing and retrieving application credentials.
    Uses the system keyring for secure storage.
    """
    
    def __init__(self, app_name="AMRS-Maintenance-Tracker", app_data_dir=None):
        self.app_name = app_name
        self.logger = logging.getLogger("CredentialManager")
        self.security = SecurityUtils(app_data_dir)
        
        # Service names for different credential types
        self.services = {
            "user": f"{app_name}-User",
            "api": f"{app_name}-API",
            "database": f"{app_name}-Database",
            "server": f"{app_name}-Server"
        }
    
    def store_user_credentials(self, username, password, remember=True):
        """Store user credentials in the system keyring"""
        try:
            if not remember:
                # If not remembering, only store temporarily in memory
                self.temp_username = username
                self.temp_password = password
                return True
            
            # Hash the username to use as key
            key = self._hash_username(username)
            
            # Build credential data
            cred_data = {
                "username": username,
                "password": password,
                "stored_at": datetime.now().isoformat()
            }
            
            # Encrypt and store
            keyring.set_password(
                self.services["user"], 
                key, 
                json.dumps(cred_data)
            )
            
            self.logger.info(f"Stored credentials for user: {username}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing user credentials: {e}")
            return False
    
    def get_user_credentials(self, username=None):
        """Retrieve user credentials from the system keyring"""
        try:
            # First check if we have temporary credentials
            if hasattr(self, 'temp_username') and hasattr(self, 'temp_password'):
                if username is None or username == self.temp_username:
                    return {
                        "username": self.temp_username,
                        "password": self.temp_password
                    }
            
            # If no specific username, try to get the last used username
            if username is None:
                username = self.get_last_username()
                if not username:
                    return None
            
            # Hash the username to use as key
            key = self._hash_username(username)
            
            # Get stored credentials
            stored_creds = keyring.get_password(self.services["user"], key)
            
            if stored_creds:
                cred_data = json.loads(stored_creds)
                return {
                    "username": cred_data["username"],
                    "password": cred_data["password"]
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving user credentials: {e}")
            return None
    
    def store_api_key(self, api_key, api_secret=None, description=None):
        """Store API credentials"""
        try:
            # Generate a unique ID for this API key
            key_id = str(uuid.uuid4())
            
            # Build credential data
            cred_data = {
                "api_key": api_key,
                "api_secret": api_secret,
                "description": description or "API Key",
                "created_at": datetime.now().isoformat()
            }
            
            # Encrypt and store
            keyring.set_password(
                self.services["api"], 
                key_id, 
                json.dumps(cred_data)
            )
            
            # Also store in the API keys index
            self._add_to_api_keys_index(key_id, description or "API Key")
            
            self.logger.info(f"Stored API key: {key_id}")
            return key_id
            
        except Exception as e:
            self.logger.error(f"Error storing API key: {e}")
            return None
    
    def get_api_key(self, key_id):
        """Retrieve API credentials by ID"""
        try:
            stored_key = keyring.get_password(self.services["api"], key_id)
            
            if stored_key:
                return json.loads(stored_key)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving API key: {e}")
            return None
    
    def list_api_keys(self):
        """List all stored API keys"""
        try:
            # Get the API keys index
            index_json = keyring.get_password(self.services["api"], "index")
            
            if index_json:
                return json.loads(index_json)
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error listing API keys: {e}")
            return {}
    
    def delete_api_key(self, key_id):
        """Delete an API key"""
        try:
            # Remove from keyring
            keyring.delete_password(self.services["api"], key_id)
            
            # Remove from index
            self._remove_from_api_keys_index(key_id)
            
            self.logger.info(f"Deleted API key: {key_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting API key: {e}")
            return False
    
    def _add_to_api_keys_index(self, key_id, description):
        """Add an API key to the index"""
        try:
            # Get current index
            index_json = keyring.get_password(self.services["api"], "index")
            index = json.loads(index_json) if index_json else {}
            
            # Add to index
            index[key_id] = {
                "description": description,
                "created_at": datetime.now().isoformat()
            }
            
            # Save index
            keyring.set_password(
                self.services["api"], 
                "index", 
                json.dumps(index)
            )
            
        except Exception as e:
            self.logger.error(f"Error updating API keys index: {e}")
    
    def _remove_from_api_keys_index(self, key_id):
        """Remove an API key from the index"""
        try:
            # Get current index
            index_json = keyring.get_password(self.services["api"], "index")
            
            if not index_json:
                return
                
            index = json.loads(index_json)
            
            # Remove from index if exists
            if key_id in index:
                del index[key_id]
                
                # Save index
                keyring.set_password(
                    self.services["api"], 
                    "index", 
                    json.dumps(index)
                )
                
        except Exception as e:
            self.logger.error(f"Error updating API keys index: {e}")
    
    def store_database_credentials(self, db_type, host, port, database, username, password):
        """Store database connection credentials"""
        try:
            # Build credential data
            cred_data = {
                "type": db_type,
                "host": host,
                "port": port,
                "database": database,
                "username": username,
                "password": password,
                "stored_at": datetime.now().isoformat()
            }
            
            # Create a unique key based on connection details
            key = self._hash_connection(db_type, host, port, database)
            
            # Encrypt and store
            keyring.set_password(
                self.services["database"], 
                key, 
                json.dumps(cred_data)
            )
            
            # Also store as the default database
            keyring.set_password(
                self.services["database"], 
                "default", 
                key
            )
            
            self.logger.info(f"Stored database credentials for {db_type}://{host}:{port}/{database}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing database credentials: {e}")
            return False
    
    def get_database_credentials(self, db_type=None, host=None, port=None, database=None):
        """
        Retrieve database credentials either by specific connection details
        or the default connection if no details provided
        """
        try:
            # If no details provided, get the default
            if not any([db_type, host, port, database]):
                default_key = keyring.get_password(self.services["database"], "default")
                if not default_key:
                    return None
                    
                stored_creds = keyring.get_password(self.services["database"], default_key)
                
            else:
                # Create key based on provided connection details
                key = self._hash_connection(db_type, host, port, database)
                stored_creds = keyring.get_password(self.services["database"], key)
            
            if stored_creds:
                return json.loads(stored_creds)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving database credentials: {e}")
            return None
    
    def get_connection_string(self, db_type=None, host=None, port=None, database=None):
        """Generate a database connection string from stored credentials"""
        creds = self.get_database_credentials(db_type, host, port, database)
        
        if not creds:
            return None
            
        if creds["type"].lower() == "postgresql":
            return f"postgresql://{creds['username']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['database']}"
        elif creds["type"].lower() == "sqlite":
            return creds["database"]  # SQLite connection string is just the file path
        else:
            return None
    
    def clear_all_credentials(self):
        """Clear all stored credentials"""
        try:
            # Clear temporary credentials
            if hasattr(self, 'temp_username'):
                del self.temp_username
            if hasattr(self, 'temp_password'):
                del self.temp_password
                
            # Clear user credentials
            self.clear_user_credentials()
            
            # Clear API keys
            api_keys = self.list_api_keys()
            for key_id in api_keys:
                self.delete_api_key(key_id)
                
            # Clear database credentials index
            try:
                keyring.delete_password(self.services["database"], "default")
            except:
                pass
                
            # TODO: Implement clearing database credentials
            
            self.logger.info("Cleared all credentials")
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing credentials: {e}")
            return False
    
    def store_last_username(self, username):
        """Store the last used username"""
        try:
            keyring.set_password(self.services["user"], "last_username", username)
            return True
        except Exception as e:
            self.logger.error(f"Error storing last username: {e}")
            return False
    
    def get_last_username(self):
        """Get the last used username"""
        try:
            return keyring.get_password(self.services["user"], "last_username")
        except:
            return None
    
    def clear_user_credentials(self, username=None):
        """Clear stored user credentials"""
        try:
            # If username provided, clear only that user's credentials
            if username:
                key = self._hash_username(username)
                try:
                    keyring.delete_password(self.services["user"], key)
                except:
                    pass
                    
                # If this was the last username, clear that too
                last_username = self.get_last_username()
                if last_username == username:
                    try:
                        keyring.delete_password(self.services["user"], "last_username")
                    except:
                        pass
                        
            else:
                # Clear last username and any temp credentials
                try:
                    keyring.delete_password(self.services["user"], "last_username")
                except:
                    pass
                    
                if hasattr(self, 'temp_username'):
                    del self.temp_username
                if hasattr(self, 'temp_password'):
                    del self.temp_password
            
            self.logger.info(f"Cleared credentials for {'user: ' + username if username else 'all users'}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing user credentials: {e}")
            return False
    
    def _hash_username(self, username):
        """Create a hash of the username to use as a key"""
        return hashlib.sha256(username.lower().encode()).hexdigest()
    
    def _hash_connection(self, db_type, host, port, database):
        """Create a hash of connection details to use as a key"""
        connection_str = f"{db_type}:{host}:{port}:{database}".lower()
        return hashlib.sha256(connection_str.encode()).hexdigest()

class LoginDialog(QDialog):
    """Login dialog for user authentication"""
    
    login_successful = pyqtSignal(str, str, bool)  # username, password, remember
    
    def __init__(self, credential_manager, parent=None):
        super().__init__(parent)
        self.credential_manager = credential_manager
        self.setWindowTitle("AMRS Maintenance Tracker - Login")
        self.setMinimumWidth(400)
        
        # Set up logger
        self.logger = logging.getLogger("LoginDialog")
        
        # Initialize UI
        self.init_ui()
        
        # Restore last username if available
        last_username = self.credential_manager.get_last_username()
        if last_username:
            self.username_input.setText(last_username)
            self.remember_check.setChecked(True)
            self.password_input.setFocus()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("AMRS Maintenance Tracker")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # Login form
        login_group = QGroupBox("Login")
        login_layout = QFormLayout(login_group)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        login_layout.addRow("Username:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        login_layout.addRow("Password:", self.password_input)
        
        self.remember_check = QCheckBox("Remember my credentials")
        login_layout.addRow("", self.remember_check)
        
        layout.addWidget(login_group)
        
        # Server configuration
        server_group = QGroupBox("Server Configuration")
        server_layout = QFormLayout(server_group)
        
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("http://server-address:port")
        server_layout.addRow("Server URL:", self.server_input)
        
        self.test_connection_btn = QPushButton("Test Connection")
        self.test_connection_btn.clicked.connect(self.test_server_connection)
        server_layout.addRow("", self.test_connection_btn)
        
        layout.addWidget(server_group)
        
        # Status message
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: red;")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.attempt_login)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.login_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def test_server_connection(self):
        """Test connection to the server"""
        server_url = self.server_input.text().strip()
        
        if not server_url:
            self.status_label.setText("Please enter a server URL")
            return
        
        self.status_label.setText("Testing connection...")
        self.test_connection_btn.setEnabled(False)
        
        # Add http:// if not present
        if not server_url.startswith("http://") and not server_url.startswith("https://"):
            server_url = "http://" + server_url
            self.server_input.setText(server_url)
        
        # Test connection in a separate thread to avoid freezing UI
        import threading
        import requests
        
        def test_connection():
            try:
                response = requests.get(f"{server_url}/health", timeout=5)
                
                if response.ok:
                    self.status_label.setText("Connection successful!")
                    self.status_label.setStyleSheet("color: green;")
                else:
                    self.status_label.setText(f"Connection failed: {response.status_code}")
                    self.status_label.setStyleSheet("color: red;")
            except requests.exceptions.ConnectionError:
                self.status_label.setText("Server is unreachable")
                self.status_label.setStyleSheet("color: red;")
            except Exception as e:
                self.status_label.setText(f"Connection error: {str(e)}")
                self.status_label.setStyleSheet("color: red;")
            finally:
                # Re-enable the button on the main thread
                from PyQt6.QtCore import QMetaObject, Qt
                QMetaObject.invokeMethod(
                    self.test_connection_btn,
                    "setEnabled",
                    Qt.ConnectionType.QueuedConnection,
                    Qt.GenericArgument("bool", True)
                )
        
        threading.Thread(target=test_connection).start()
    
    def attempt_login(self):
        """Attempt to log in with the provided credentials"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        remember = self.remember_check.isChecked()
        server_url = self.server_input.text().strip()
        
        # Validate inputs
        if not username:
            self.status_label.setText("Username is required")
            self.status_label.setStyleSheet("color: red;")
            return
        
        if not password:
            self.status_label.setText("Password is required")
            self.status_label.setStyleSheet("color: red;")
            return
        
        # Save the server URL if provided
        if server_url:
            # Add http:// if not present
            if not server_url.startswith("http://") and not server_url.startswith("https://"):
                server_url = "http://" + server_url
            
            # TODO: Store server URL in configuration
        
        # Emit the login signal for the application to handle authentication
        self.login_successful.emit(username, password, remember)
        
        # Store last username if remember is checked
        if remember:
            self.credential_manager.store_last_username(username)
        
        # Close the dialog
        self.accept()
