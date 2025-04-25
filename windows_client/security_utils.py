import os
import base64
import hashlib
import logging
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class SecurityUtils:
    """Utilities for handling encryption and security operations"""
    
    def __init__(self, app_data_dir=None):
        """Initialize security utilities with optional custom app data directory"""
        self.logger = logging.getLogger("SecurityUtils")
        
        # Set up app data directory
        if app_data_dir:
            self.app_data_dir = Path(app_data_dir)
        else:
            # Default to user's app data directory
            self.app_data_dir = Path(os.path.expanduser('~')) / '.amrs'
        
        # Ensure directory exists
        os.makedirs(self.app_data_dir, exist_ok=True)
        
        # Path to store device key
        self.key_path = self.app_data_dir / '.device_key'
        
        # Initialize or load device key
        self.device_key = self._get_or_create_device_key()
        
        # Initialize encryption tool
        self.fernet = Fernet(self.device_key)
    
    def _get_or_create_device_key(self):
        """Get existing device key or create a new one"""
        if self.key_path.exists():
            try:
                # Load existing key
                with open(self.key_path, 'rb') as key_file:
                    return key_file.read()
            except Exception as e:
                self.logger.error(f"Error reading device key: {e}")
                # Fall through to key creation
        
        # Generate a new key
        return self._create_new_device_key()
    
    def _create_new_device_key(self):
        """Create a new device-specific encryption key"""
        try:
            # Generate a secure random key
            key = Fernet.generate_key()
            
            # Save the key securely
            with open(self.key_path, 'wb') as key_file:
                key_file.write(key)
            
            self.logger.info("Created new device encryption key")
            return key
        except Exception as e:
            self.logger.error(f"Error creating device key: {e}")
            raise
    
    def encrypt(self, data):
        """Encrypt data using the device key"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return self.fernet.encrypt(data)
    
    def decrypt(self, encrypted_data):
        """Decrypt data using the device key"""
        return self.fernet.decrypt(encrypted_data)
    
    def generate_password_key(self, password, salt=None):
        """Generate an encryption key from a password"""
        if salt is None:
            salt = os.urandom(16)
        elif isinstance(salt, str):
            salt = salt.encode('utf-8')
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
        return key, salt
    
    def hash_data(self, data):
        """Create a hash of data for integrity verification"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha256(data).hexdigest()
    
    def verify_data_integrity(self, data, expected_hash):
        """Verify data integrity using a hash"""
        actual_hash = self.hash_data(data)
        return actual_hash == expected_hash
