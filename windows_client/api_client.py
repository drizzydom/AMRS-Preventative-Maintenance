import os
import requests
import json
import logging
import keyring
from datetime import datetime, timedelta
from pathlib import Path
from PyQt6.QtCore import QSettings

class ApiClient:
    """Client for interacting with the maintenance API with improved security"""
    
    def __init__(self, base_url=None, config_file=None):
        self.logger = logging.getLogger("ApiClient")
        
        # Set up logging
        handler = logging.FileHandler("api_client.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Set up storage paths
        self.app_dir = os.path.join(os.path.expanduser("~"), ".amrs")
        os.makedirs(self.app_dir, exist_ok=True)
        
        # Load configuration
        if config_file:
            self.config_file = config_file
        else:
            self.config_file = os.path.join(self.app_dir, "config.json")
            
        # Set base URL from config or parameter
        self.base_url = base_url
        self.config = self._load_config()
        
        if not self.base_url:
            self.base_url = self.config.get("server_url")
        
        # Set up authentication
        self.token = None
        self.refresh_token = None
        self.token_expiry = None
        self.username = None
        
        # Load any stored tokens
        self._load_auth_tokens()
        
        self.logger.info(f"ApiClient initialized with base URL: {self.base_url}")
    
    def _load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
                return {}
        return {}
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f)
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
    
    def set_server_url(self, url):
        """Set the server URL"""
        self.base_url = url
        self.config["server_url"] = url
        self._save_config()
    
    def _load_auth_tokens(self):
        """Load authentication tokens from secure storage"""
        try:
            # Try to get token from system keyring
            token_data = keyring.get_password("AMRS_Maintenance", "auth_tokens")
            if token_data:
                data = json.loads(token_data)
                self.token = data.get("token")
                self.refresh_token = data.get("refresh_token")
                self.token_expiry = datetime.fromisoformat(data.get("expiry", "2000-01-01T00:00:00"))
                self.username = data.get("username")
                
                # Check if token is expired
                if self.token_expiry <= datetime.now():
                    self.logger.info("Stored token is expired, will try to refresh")
                    if self.refresh_token:
                        self._refresh_auth_token()
                    else:
                        self.logger.info("No refresh token available")
                else:
                    self.logger.info(f"Loaded valid auth token for {self.username}")
        except Exception as e:
            self.logger.error(f"Error loading auth tokens: {e}")
            self.token = None
            self.refresh_token = None
            self.token_expiry = None
    
    def _save_auth_tokens(self):
        """Save authentication tokens to secure storage"""
        try:
            if self.token and self.username:
                token_data = {
                    "token": self.token,
                    "refresh_token": self.refresh_token,
                    "expiry": self.token_expiry.isoformat() if self.token_expiry else None,
                    "username": self.username
                }
                keyring.set_password("AMRS_Maintenance", "auth_tokens", json.dumps(token_data))
                self.logger.info(f"Saved auth tokens for {self.username}")
        except Exception as e:
            self.logger.error(f"Error saving auth tokens: {e}")
    
    def _clear_auth_tokens(self):
        """Clear authentication tokens from storage"""
        try:
            keyring.delete_password("AMRS_Maintenance", "auth_tokens")
            self.token = None
            self.refresh_token = None
            self.token_expiry = None
            self.username = None
            self.logger.info("Cleared auth tokens")
        except Exception as e:
            self.logger.error(f"Error clearing auth tokens: {e}")
    
    def login(self, username, password, remember=False):
        """Login to the API and get authentication token"""
        try:
            response = requests.post(
                f"{self.base_url}/api/login",
                json={"username": username, "password": password},
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                self.token = data.get("token")
                self.refresh_token = data.get("refresh_token")
                self.username = username
                
                # Parse expiry time or set default (24 hours)
                expiry = data.get("expiry")
                if expiry:
                    self.token_expiry = datetime.fromisoformat(expiry)
                else:
                    self.token_expiry = datetime.now() + timedelta(hours=24)
                
                # Save tokens if remember is True
                if remember:
                    self._save_auth_tokens()
                
                self.logger.info(f"Login successful for {username}")
                return True
            else:
                error_msg = "Login failed"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", error_msg)
                except:
                    error_msg = f"Login failed with status code {response.status_code}"
                
                self.logger.error(error_msg)
                return False
                
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            return False
    
    def _refresh_auth_token(self):
        """Refresh the authentication token"""
        try:
            if not self.refresh_token:
                self.logger.error("No refresh token available")
                return False
                
            response = requests.post(
                f"{self.base_url}/api/refresh-token",
                json={"refresh_token": self.refresh_token},
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                self.token = data.get("token")
                # Some APIs also refresh the refresh token
                if "refresh_token" in data:
                    self.refresh_token = data.get("refresh_token")
                
                # Parse expiry time or set default (24 hours)
                expiry = data.get("expiry")
                if expiry:
                    self.token_expiry = datetime.fromisoformat(expiry)
                else:
                    self.token_expiry = datetime.now() + timedelta(hours=24)
                
                # Save the updated tokens
                self._save_auth_tokens()
                
                self.logger.info("Token refreshed successfully")
                return True
            else:
                self.logger.error(f"Token refresh failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Token refresh error: {e}")
            return False
    
    def logout(self):
        """Logout from the API"""
        try:
            if self.token:
                # Optionally invalidate the token on server
                try:
                    requests.post(
                        f"{self.base_url}/api/logout",
                        headers={'Authorization': f'Bearer {self.token}'},
                        timeout=5  # Short timeout for logout
                    )
                except:
                    pass  # Ignore server errors during logout
            
            # Clear tokens
            self._clear_auth_tokens()
            self.logger.info("Logout successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Logout error: {e}")
            return False
    
    def authenticate_with_stored_credentials(self):
        """Try to authenticate using stored credentials"""
        try:
            # Check if we already have a valid token
            if self.token and self.token_expiry and self.token_expiry > datetime.now():
                self.logger.info("Using existing valid token")
                return True
                
            # Try to refresh token
            if self.refresh_token:
                if self._refresh_auth_token():
                    return True
            
            # No valid tokens, try to get stored credentials
            credentials = keyring.get_password("AMRS_Maintenance", "credentials")
            if credentials:
                cred_data = json.loads(credentials)
                username = cred_data.get("username")
                password = cred_data.get("password")
                
                if username and password:
                    return self.login(username, password, True)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error authenticating with stored credentials: {e}")
            return False
    
    def store_credentials(self, username, password):
        """Securely store credentials for later use"""
        try:
            credentials = {
                "username": username,
                "password": password
            }
            keyring.set_password("AMRS_Maintenance", "credentials", json.dumps(credentials))
            self.logger.info(f"Stored credentials for {username}")
            return True
        except Exception as e:
            self.logger.error(f"Error storing credentials: {e}")
            return False
    
    def clear_credentials(self):
        """Clear stored credentials"""
        try:
            keyring.delete_password("AMRS_Maintenance", "credentials")
            self.logger.info("Cleared stored credentials")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing credentials: {e}")
            return False
    
    def check_server(self):
        """Check if the server is available"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            return response.ok
        except:
            return False
    
    def execute_request(self, method, endpoint, data=None, offline_db=None):
        """Execute a request with proper auth and error handling"""
        try:
            if not self.base_url:
                raise Exception("No server URL configured")
            
            # Check if we need to handle authentication
            if self.token and self.token_expiry and self.token_expiry <= datetime.now():
                # Token expired, try to refresh
                if not self._refresh_auth_token():
                    raise Exception("Authentication token expired and refresh failed")
            
            headers = {}
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'
            
            url = f"{self.base_url}{endpoint}"
            
            # Try to execute the request
            response = requests.request(
                method, 
                url, 
                json=data,
                headers=headers,
                timeout=15
            )
            
            # Handle response codes
            if response.ok:
                # Request successful
                return response.json() if response.content else {}
            elif response.status_code == 401:  # Unauthorized
                if self.refresh_token:
                    # Try to refresh token
                    if self._refresh_auth_token():
                        # Try request again with new token
                        headers['Authorization'] = f'Bearer {self.token}'
                        response = requests.request(
                            method, 
                            url, 
                            json=data,
                            headers=headers,
                            timeout=15
                        )
                        if response.ok:
                            return response.json() if response.content else {}
                
                # Authentication failed
                raise Exception("Authentication failed")
            else:
                # Server error
                try:
                    error_message = response.json().get('message', f"Server error: {response.status_code}")
                except:
                    error_message = f"Server error: {response.status_code}"
                
                # Store for offline execution if database provided
                if offline_db and method != 'GET':
                    offline_db.store_operation(method, endpoint, data)
                    self.logger.info(f"Stored {method} operation to {endpoint} for offline execution")
                
                raise Exception(error_message)
                
        except requests.exceptions.ConnectionError:
            # Connection error - likely offline
            self.logger.warning(f"Connection error executing {method} {endpoint}")
            
            # For GET requests, try to use cached data
            if method == 'GET' and offline_db:
                cached_data, timestamp = offline_db.get_cached_response(endpoint)
                if cached_data:
                    self.logger.info(f"Using cached data for {endpoint} from {timestamp}")
                    return cached_data
            
            # For other methods, store operation for later if we have offline_db
            if offline_db and method != 'GET':
                op_id = offline_db.store_operation(method, endpoint, data)
                self.logger.info(f"Stored {method} operation to {endpoint} for offline execution (id: {op_id})")
                return {"status": "pending", "message": "Operation stored for offline execution", "id": op_id}
            
            raise Exception("Cannot connect to server and no offline fallback available")
            
        except Exception as e:
            self.logger.error(f"Error executing {method} {endpoint}: {e}")
            raise
