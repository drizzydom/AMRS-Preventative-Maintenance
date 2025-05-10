#!/usr/bin/env python3
"""
Create token_manager.py with the proper content
"""
import os

token_manager_content = '''#!/usr/bin/env python3
"""
Token Manager for AMRS Maintenance Tracker

This module handles the creation, validation, and storage of authentication tokens
for offline usage. It allows users to authenticate once while online and then
continue using the application offline with the stored token.
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
logging.basicConfig(level=logging.INFO, format='[TOKEN_MANAGER] %(levelname)s - %(message)s')
logger = logging.getLogger("token_manager")

class TokenManager:
    """
    Manages authentication tokens for offline use
    
    This class handles:
    - Token generation with configurable expiration
    - Token validation
    - Token storage and retrieval
    - Token refresh
    """
    
    def __init__(self, secret_key=None, token_expiry_days=30, token_dir=None):
        """
        Initialize the TokenManager
        
        Args:
            secret_key (str): Secret key for token signing
            token_expiry_days (int): Number of days before token expires
            token_dir (str): Directory to store token files
        """
        self.secret_key = secret_key or os.environ.get('JWT_SECRET_KEY') or os.urandom(32).hex()
        self.token_expiry_days = token_expiry_days
        
        # Set up token storage directory
        if token_dir:
            self.token_dir = Path(token_dir)
        else:
            current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
            self.token_dir = current_dir / 'instance' / 'tokens'
            
        self.token_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Token storage directory: {self.token_dir}")
    
    def generate_token(self, user_id, username, role_id=None, additional_data=None):
        """
        Generate a new JWT token for a user
        
        Args:
            user_id (int): User ID
            username (str): Username
            role_id (int): User's role ID
            additional_data (dict): Any additional data to include in the token
            
        Returns:
            str: JWT token
        """
        # Generate a unique token ID
        token_id = str(uuid.uuid4())
        
        # Calculate expiration time
        expiry = datetime.utcnow() + timedelta(days=self.token_expiry_days)
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
    
    def validate_token(self, token):
        """
        Validate a JWT token
        
        Args:
            token (str): JWT token to validate
            
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
                
            logger.info(f"Token validated for user {payload.get('username')} (ID: {payload.get('sub')})")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
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
                
            logger.info(f"Retrieved token for user ID {user_id}")
            return token_data.get('token')
            
        except Exception as e:
            logger.error(f"Error retrieving token: {e}")
            return None
    
    def refresh_token(self, token):
        """
        Refresh an existing token
        
        Args:
            token (str): Existing JWT token
            
        Returns:
            str: New JWT token if successful, None otherwise
        """
        try:
            # Decode without verification to get the payload
            payload = jwt.decode(token, options={"verify_signature": False})
            
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
'''

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
token_manager_path = os.path.join(current_dir, 'token_manager.py')

# Delete the file if it exists
if os.path.exists(token_manager_path):
    os.remove(token_manager_path)
    print(f"Deleted existing token_manager.py")

# Write the new content
with open(token_manager_path, 'w') as f:
    f.write(token_manager_content)

print(f"Created token_manager.py with {len(token_manager_content)} bytes")

# Test importing the module
try:
    import token_manager
    from token_manager import TokenManager
    tm = TokenManager()
    print(f"Successfully imported TokenManager class, expiry days: {tm.token_expiry_days}")
except Exception as e:
    print(f"Error importing TokenManager: {e}")
