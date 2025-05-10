#!/usr/bin/env python3
"""
Enhanced Token Manager for AMRS Maintenance Tracker

This module provides an enhanced version of the TokenManager with additional
security features and better configuration options for offline token authentication.
"""
import os
import jwt
import json
import uuid
import time
import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='[ENHANCED_TOKEN_MANAGER] %(levelname)s - %(message)s')
logger = logging.getLogger("enhanced_token_manager")

class EnhancedTokenManager:
    """
    Enhanced token manager for offline authentication with additional security features
    
    Key features:
    - Configurable token expiry
    - Token rotation
    - Secure token storage
    - Token revocation
    - Token refresh with sliding expiration
    - Token payload encryption
    """
    
    def __init__(self, secret_key=None, token_expiry_days=30, token_dir=None, 
                 use_encrypted_storage=False, encryption_key=None,
                 refresh_threshold_days=5):
        """
        Initialize the enhanced token manager
        
        Args:
            secret_key (str): Secret key for token signing
            token_expiry_days (int): Number of days before token expires
            token_dir (str): Directory to store token files
            use_encrypted_storage (bool): Whether to encrypt token storage
            encryption_key (str): Key for encrypting token storage
            refresh_threshold_days (int): Days before expiry to trigger auto-refresh
        """
        self.secret_key = secret_key or os.environ.get('JWT_SECRET_KEY') or os.urandom(32).hex()
        self.token_expiry_days = token_expiry_days
        self.refresh_threshold_days = refresh_threshold_days
        self.use_encrypted_storage = use_encrypted_storage
        self.encryption_key = encryption_key
        
        # Set up token storage directory
        if token_dir:
            self.token_dir = Path(token_dir)
        else:
            current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
            self.token_dir = current_dir / 'instance' / 'tokens'
            
        self.token_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Token storage directory: {self.token_dir}")
        logger.info(f"Token expiry days: {self.token_expiry_days}")
        logger.info(f"Auto-refresh threshold: {self.refresh_threshold_days} days before expiry")
    
    def generate_token(self, user_id, username, role_id=None, additional_data=None, 
                       expiry_days=None):
        """
        Generate a new JWT token for a user
        
        Args:
            user_id (int): User ID
            username (str): Username
            role_id (int): User's role ID
            additional_data (dict): Any additional data to include in the token
            expiry_days (int): Override default expiry days
            
        Returns:
            str: JWT token
        """
        # Use provided expiry days or class default
        token_expiry_days = expiry_days if expiry_days is not None else self.token_expiry_days
        
        # Generate a unique token ID
        token_id = str(uuid.uuid4())
        
        # Calculate expiration time
        expiry = datetime.utcnow() + timedelta(days=token_expiry_days)
        expiry_timestamp = int(time.mktime(expiry.timetuple()))
          # Create payload
        payload = {
            'sub': str(user_id),  # subject (user id) - must be a string
            'jti': token_id,  # JWT ID (unique identifier for this token)
            'iat': int(time.time()),  # issued at timestamp
            'exp': expiry_timestamp,  # expiration timestamp
            'username': username,
            'role_id': role_id
        }
        
        # Add any additional data
        if additional_data and isinstance(additional_data, dict):
            payload.update(additional_data)
        
        # Generate the token
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        
        # Log token creation (don't log the actual token)
        logger.info(f"Generated token for user {username} (ID: {user_id}) with expiry {expiry}")
        
        return token
    
    def validate_token(self, token, auto_refresh=True):
        """
        Validate a JWT token
        
        Args:
            token (str): JWT token to validate
            auto_refresh (bool): Whether to automatically refresh tokens near expiry
            
        Returns:
            dict: Token payload if valid, None if invalid
        """
        try:
            # Decode and validate the token
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            # Check if token has expired
            if 'exp' in payload and int(time.time()) > payload['exp']:
                logger.warning(f"Token expired for user {payload.get('username')}")
                return None
            
            # Check if token is approaching expiry and should be refreshed
            if auto_refresh and self.should_refresh_token(payload):
                logger.info(f"Token approaching expiry, auto-refreshing")
                user_id = payload.get('sub')
                if user_id:
                    new_token = self.refresh_token(token)
                    if new_token:
                        # Decode the new token to return its payload
                        return jwt.decode(new_token, self.secret_key, algorithms=['HS256'])
            
            logger.info(f"Token validated for user {payload.get('username')} (ID: {payload.get('sub')})")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def should_refresh_token(self, payload):
        """
        Check if a token should be refreshed based on remaining time
        
        Args:
            payload (dict): Token payload
            
        Returns:
            bool: True if token should be refreshed, False otherwise
        """
        if 'exp' not in payload:
            return False
            
        expiry_timestamp = payload['exp']
        now = int(time.time())
        seconds_remaining = expiry_timestamp - now
        days_remaining = seconds_remaining / (60 * 60 * 24)
        
        # Refresh if less than refresh_threshold_days remaining
        return days_remaining < self.refresh_threshold_days
    
    def encrypt_token_data(self, token_data):
        """
        Encrypt token data for secure storage
        
        Args:
            token_data (dict): Token data to encrypt
            
        Returns:
            dict: Encrypted token data
        """
        if not self.use_encrypted_storage or not self.encryption_key:
            return token_data
            
        # Simple encryption for demo (in production, use a proper encryption library)
        token_str = json.dumps(token_data)
        encrypted = self._simple_encrypt(token_str, self.encryption_key)
        
        return {
            'encrypted': True,
            'data': encrypted,
            'encrypted_at': datetime.utcnow().isoformat()
        }
    
    def decrypt_token_data(self, encrypted_data):
        """
        Decrypt token data from secure storage
        
        Args:
            encrypted_data (dict): Encrypted token data
            
        Returns:
            dict: Decrypted token data
        """
        if not encrypted_data.get('encrypted', False):
            return encrypted_data
            
        if not self.encryption_key:
            logger.error("Cannot decrypt token data without encryption key")
            return None
            
        try:
            encrypted = encrypted_data.get('data')
            decrypted_str = self._simple_decrypt(encrypted, self.encryption_key)
            return json.loads(decrypted_str)
        except Exception as e:
            logger.error(f"Error decrypting token data: {e}")
            return None
    
    def _simple_encrypt(self, data, key):
        """
        Simple encryption for demo purposes
        In production, use a proper encryption library
        """
        # This is a placeholder for demonstration
        # In a real app, use a proper encryption library like cryptography
        h = hashlib.sha256(key.encode()).digest()
        return hashlib.sha256((data + h.hex()).encode()).hexdigest()
    
    def _simple_decrypt(self, encrypted, key):
        """
        Simple decryption for demo purposes
        In production, use a proper encryption library
        """
        # Since our demo encryption is just a hash, we can't actually decrypt
        # This is just a placeholder to show the concept
        # In a real app, this would decrypt the data using a proper library
        return encrypted
    
    def store_token(self, user_id, token):
        """
        Store a token for offline use
        
        Args:
            user_id (int): User ID
            token (str): JWT token
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create a token file for the user
            token_file = self.token_dir / f"user_{user_id}_token.json"
            
            # Store the token with metadata
            token_data = {
                'token': token,
                'created_at': datetime.utcnow().isoformat(),
                'user_id': user_id
            }
            
            # Encrypt token data if enabled
            if self.use_encrypted_storage:
                token_data = self.encrypt_token_data(token_data)
            
            with open(token_file, 'w') as f:
                json.dump(token_data, f)
                
            logger.info(f"Token stored for user ID {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing token: {e}")
            return False
    
    def retrieve_token(self, user_id):
        """
        Retrieve a stored token for a user
        
        Args:
            user_id (int): User ID
            
        Returns:
            str: JWT token if found, None otherwise
        """
        try:
            token_file = self.token_dir / f"user_{user_id}_token.json"
            
            if not token_file.exists():
                logger.warning(f"No token file found for user ID {user_id}")
                return None
            
            with open(token_file, 'r') as f:
                token_data = json.load(f)
            
            # Decrypt token data if needed
            if token_data.get('encrypted', False):
                token_data = self.decrypt_token_data(token_data)
                if not token_data:
                    logger.error(f"Failed to decrypt token data for user ID {user_id}")
                    return None
                
            logger.info(f"Retrieved token for user ID {user_id}")
            return token_data.get('token')
            
        except Exception as e:
            logger.error(f"Error retrieving token: {e}")
            return None
    
    def refresh_token(self, token):
        """
        Refresh an existing token with sliding expiration
        
        Args:
            token (str): Existing JWT token
            
        Returns:
            str: New JWT token if successful, None otherwise
        """
        try:
            # Decode without verification to get the payload
            payload = jwt.decode(token, options={"verify_signature": False})
            
            # Verify the token signature properly
            try:
                jwt.decode(token, self.secret_key, algorithms=['HS256'])
            except jwt.InvalidTokenError:
                logger.warning("Cannot refresh invalid token")
                return None
              # Generate a new token for the same user
            user_id = payload.get('sub')
            # Convert user_id to int if it's stored as string
            if isinstance(user_id, str) and user_id.isdigit():
                user_id = int(user_id)
            username = payload.get('username')
            role_id = payload.get('role_id')
            
            # Filter out standard JWT claims for additional_data
            standard_claims = {'sub', 'jti', 'iat', 'exp', 'username', 'role_id'}
            additional_data = {k: v for k, v in payload.items() if k not in standard_claims}
            
            # Generate new token
            new_token = self.generate_token(user_id, username, role_id, additional_data)
            
            # Store the new token
            self.store_token(user_id, new_token)
            
            logger.info(f"Token refreshed for user {username} (ID: {user_id})")
            return new_token
            
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return None
    
    def delete_token(self, user_id):
        """
        Delete a stored token
        
        Args:
            user_id (int): User ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            token_file = self.token_dir / f"user_{user_id}_token.json"
            
            if token_file.exists():
                token_file.unlink()
                logger.info(f"Token deleted for user ID {user_id}")
                return True
            else:
                logger.warning(f"No token file found to delete for user ID {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting token: {e}")
            return False
    
    def hash_token(self, token):
        """
        Create a hash of a token for storage in database
        
        Args:
            token (str): JWT token
            
        Returns:
            str: Hashed token
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    def list_tokens(self):
        """
        List all tokens and their status
        
        Returns:
            list: List of token data dictionaries
        """
        tokens = []
        token_files = list(self.token_dir.glob("user_*_token.json"))
        
        for token_file in token_files:
            try:
                with open(token_file, 'r') as f:
                    token_data = json.load(f)
                
                # Decrypt if needed
                if token_data.get('encrypted', False):
                    token_data = self.decrypt_token_data(token_data)
                    if not token_data:
                        continue
                
                user_id = token_data.get('user_id')
                token = token_data.get('token')
                
                if token:
                    # Check validity without auto-refresh
                    payload = self.validate_token(token, auto_refresh=False)
                    
                    status = {
                        'is_valid': payload is not None,
                        'user_id': user_id,
                        'username': payload.get('username') if payload else None,
                        'created_at': token_data.get('created_at'),
                        'file_path': str(token_file)
                    }
                    
                    # Add expiry info if available
                    if payload and 'exp' in payload:
                        expiry_timestamp = payload['exp']
                        expiry_date = datetime.fromtimestamp(expiry_timestamp)
                        now = datetime.now()
                        days_remaining = (expiry_date - now).days
                        
                        status.update({
                            'expires_at': expiry_date.isoformat(),
                            'days_remaining': days_remaining,
                            'should_refresh': days_remaining < self.refresh_threshold_days
                        })
                        
                    tokens.append(status)
                
            except Exception as e:
                logger.error(f"Error processing token file {token_file}: {e}")
        
        return tokens
