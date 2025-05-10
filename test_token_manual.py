#!/usr/bin/env python3
"""
Manual test script for offline token authentication

This script provides a simple interactive way to test various aspects
of the offline token authentication system.
"""
import os
import sys
import argparse
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='[MANUAL_TOKEN_TEST] %(levelname)s - %(message)s')
logger = logging.getLogger("manual_token_test")

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import necessary modules
try:
    from token_manager import TokenManager
    from enhanced_token_manager import EnhancedTokenManager
    from db_controller import DatabaseController
    HAS_REQUIRED_MODULES = True
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    HAS_REQUIRED_MODULES = False

# Constants
DEFAULT_TOKEN_EXPIRY = 30  # days
TEST_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'secure_offline_jwt_secret_key_for_testing')

def print_menu():
    """Print the main menu"""
    print("\n===== OFFLINE TOKEN AUTHENTICATION MANUAL TEST =====")
    print("1. Generate a token for user")
    print("2. Validate a token")
    print("3. List all stored tokens")
    print("4. Refresh a token")
    print("5. Delete a token")
    print("6. Test token expiry (quick test)")
    print("7. Exit")
    print("=================================================")

def get_users():
    """Get a list of users from the database"""
    try:
        db_controller = DatabaseController(use_encryption=False)
        users = db_controller.fetch_all("SELECT id, username, is_admin FROM users")
        return users
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return []

def print_users(users):
    """Print a list of users"""
    print("\nAvailable users:")
    for i, user in enumerate(users, 1):
        print(f"{i}. {user['username']} (ID: {user['id']}, Admin: {bool(user['is_admin'])})")

def generate_token():
    """Generate a token for a user"""
    users = get_users()
    if not users:
        print("No users found in database!")
        return
    
    print_users(users)
    
    try:
        user_choice = int(input("\nSelect a user (number): ")) - 1
        if user_choice < 0 or user_choice >= len(users):
            print("Invalid selection!")
            return
        
        user = users[user_choice]
        
        # Get token settings
        expiry_days = int(input(f"Token expiry in days [{DEFAULT_TOKEN_EXPIRY}]: ") or DEFAULT_TOKEN_EXPIRY)
        use_enhanced = input("Use enhanced token manager? (y/n) [y]: ").lower() != 'n'
        
        # Initialize token manager
        if use_enhanced:
            token_manager = EnhancedTokenManager(secret_key=TEST_SECRET_KEY, token_expiry_days=expiry_days)
            print("Using EnhancedTokenManager")
        else:
            token_manager = TokenManager(secret_key=TEST_SECRET_KEY, token_expiry_days=expiry_days)
            print("Using TokenManager")
        
        # Generate token
        token = token_manager.generate_token(
            user_id=user['id'],
            username=user['username'],
            role_id=1,  # Assuming role ID 1 for testing
            additional_data={
                'is_admin': bool(user['is_admin']),
                'offline_access': True,
                'is_test': True
            }
        )
        
        # Store the token
        token_manager.store_token(user['id'], token)
        
        print(f"\n✅ Token generated for user {user['username']} (ID: {user['id']})")
        print(f"Token: {token}")
        print(f"Expires in {expiry_days} days")
        
    except ValueError:
        print("Invalid input!")
    except Exception as e:
        print(f"Error: {e}")

def validate_token():
    """Validate a token"""
    token = input("\nEnter token to validate: ")
    if not token:
        print("No token provided!")
        return
    
    use_enhanced = input("Use enhanced token manager? (y/n) [y]: ").lower() != 'n'
    
    # Initialize token manager
    if use_enhanced:
        token_manager = EnhancedTokenManager(secret_key=TEST_SECRET_KEY)
        print("Using EnhancedTokenManager")
    else:
        token_manager = TokenManager(secret_key=TEST_SECRET_KEY)
        print("Using TokenManager")
    
    # Validate token
    payload = token_manager.validate_token(token)
    
    if payload:
        print("\n✅ Token is valid!")
        print("Token details:")
        print(f"  User ID: {payload.get('sub')}")
        print(f"  Username: {payload.get('username')}")
        print(f"  Role ID: {payload.get('role_id')}")
        
        # Calculate and display expiry time
        if 'exp' in payload:
            expiry_timestamp = payload['exp']
            expiry_date = datetime.fromtimestamp(expiry_timestamp)
            now = datetime.now()
            days_remaining = (expiry_date - now).days
            
            print(f"  Expires on: {expiry_date.isoformat()}")
            print(f"  Days remaining: {days_remaining}")
        
        # Display any additional custom data
        standard_claims = {'sub', 'jti', 'iat', 'exp', 'username', 'role_id'}
        additional_data = {k: v for k, v in payload.items() if k not in standard_claims}
        
        if additional_data:
            print("  Additional data:")
            for key, value in additional_data.items():
                print(f"    {key}: {value}")
    else:
        print("\n❌ Token is invalid or expired!")

def list_tokens():
    """List all stored tokens"""
    use_enhanced = input("Use enhanced token manager? (y/n) [y]: ").lower() != 'n'
    
    # Initialize token manager
    if use_enhanced:
        token_manager = EnhancedTokenManager(secret_key=TEST_SECRET_KEY)
        print("Using EnhancedTokenManager")
    else:
        token_manager = TokenManager(secret_key=TEST_SECRET_KEY)
        print("Using TokenManager")
    
    if use_enhanced and hasattr(token_manager, 'list_tokens'):
        # Use enhanced list_tokens method
        tokens = token_manager.list_tokens()
        
        if not tokens:
            print("\nNo tokens found!")
            return
        
        print(f"\nFound {len(tokens)} tokens:")
        for token_info in tokens:
            print(f"  User: {token_info.get('username', 'unknown')}")
            print(f"  User ID: {token_info.get('user_id', 'unknown')}")
            print(f"  Valid: {token_info.get('is_valid', False)}")
            
            if 'expires_at' in token_info:
                print(f"  Expires: {token_info['expires_at']}")
            
            if 'days_remaining' in token_info:
                print(f"  Days remaining: {token_info['days_remaining']}")
            
            if 'should_refresh' in token_info:
                print(f"  Needs refresh: {token_info['should_refresh']}")
            
            print(f"  File: {token_info.get('file_path', 'unknown')}")
            print("")
        
    else:
        # Use manual file scanning
        token_files = list(token_manager.token_dir.glob("user_*_token.json"))
        
        if not token_files:
            print("\nNo tokens found!")
            return
        
        print(f"\nFound {len(token_files)} tokens:")
        
        for token_file in token_files:
            try:
                with open(token_file, 'r') as f:
                    token_data = json.load(f)
                
                user_id = token_data.get('user_id', 'unknown')
                created_at = token_data.get('created_at', 'unknown')
                token = token_data.get('token')
                
                # Check if token is valid
                if token:
                    payload = token_manager.validate_token(token)
                    status = "VALID" if payload else "INVALID/EXPIRED"
                    
                    if payload:
                        username = payload.get('username', 'unknown')
                        # Calculate remaining days
                        expiry_timestamp = payload.get('exp')
                        if expiry_timestamp:
                            expiry_date = datetime.fromtimestamp(expiry_timestamp)
                            now = datetime.now()
                            days_remaining = (expiry_date - now).days
                            expiry_info = f", expires in {days_remaining} days"
                        else:
                            expiry_info = ""
                    else:
                        username = "unknown"
                        expiry_info = ""
                else:
                    status = "INVALID (no token)"
                    username = "unknown"
                    expiry_info = ""
                
                print(f"  User ID: {user_id} | Username: {username} | Status: {status}{expiry_info}")
                print(f"  Created: {created_at}")
                print(f"  File: {token_file.name}")
                print("")
                
            except Exception as e:
                print(f"  Error reading token file {token_file.name}: {e}")

def refresh_token():
    """Refresh a token"""
    token = input("\nEnter token to refresh: ")
    if not token:
        print("No token provided!")
        return
    
    use_enhanced = input("Use enhanced token manager? (y/n) [y]: ").lower() != 'n'
    
    # Initialize token manager
    if use_enhanced:
        token_manager = EnhancedTokenManager(secret_key=TEST_SECRET_KEY)
        print("Using EnhancedTokenManager")
    else:
        token_manager = TokenManager(secret_key=TEST_SECRET_KEY)
        print("Using TokenManager")
    
    # Refresh token
    new_token = token_manager.refresh_token(token)
    
    if new_token:
        print("\n✅ Token refreshed successfully!")
        print(f"New token: {new_token}")
        
        # Validate the new token
        payload = token_manager.validate_token(new_token)
        
        if payload:
            print("\nNew token details:")
            print(f"  User ID: {payload.get('sub')}")
            print(f"  Username: {payload.get('username')}")
            
            # Calculate and display expiry time
            if 'exp' in payload:
                expiry_timestamp = payload['exp']
                expiry_date = datetime.fromtimestamp(expiry_timestamp)
                now = datetime.now()
                days_remaining = (expiry_date - now).days
                
                print(f"  Expires on: {expiry_date.isoformat()}")
                print(f"  Days remaining: {days_remaining}")
    else:
        print("\n❌ Failed to refresh token!")

def delete_token():
    """Delete a token"""
    user_id = input("\nEnter user ID to delete token for: ")
    if not user_id:
        print("No user ID provided!")
        return
    
    use_enhanced = input("Use enhanced token manager? (y/n) [y]: ").lower() != 'n'
    
    # Initialize token manager
    if use_enhanced:
        token_manager = EnhancedTokenManager(secret_key=TEST_SECRET_KEY)
        print("Using EnhancedTokenManager")
    else:
        token_manager = TokenManager(secret_key=TEST_SECRET_KEY)
        print("Using TokenManager")
    
    # Delete token
    result = token_manager.delete_token(user_id)
    
    if result:
        print(f"\n✅ Token for user ID {user_id} deleted successfully!")
    else:
        print(f"\n❌ Failed to delete token for user ID {user_id}!")

def test_expiry():
    """Test token expiry with a quick-expiring token"""
    try:
        import jwt
        from jwt import PyJWT
    except ImportError:
        print("PyJWT module not found! Please install it with: pip install PyJWT")
        return
    
    # Get expiry time in seconds
    try:
        seconds = int(input("\nToken expiry in seconds [10]: ") or 10)
    except ValueError:
        print("Invalid input! Using default (10 seconds)")
        seconds = 10
    
    # Initialize token manager
    token_manager = TokenManager(secret_key=TEST_SECRET_KEY)
    
    # Generate token payload
    user_id = 999  # Test user ID
    expiry = int(time.time()) + seconds
    
    payload = {
        'sub': user_id,
        'jti': 'test_expiry_token',
        'iat': int(time.time()),
        'exp': expiry,
        'username': 'expiry_test',
        'is_test': True
    }
    
    # Encode token
    jwt_encoder = PyJWT()
    token = jwt_encoder.encode(payload, TEST_SECRET_KEY, algorithm='HS256')
    
    print(f"\n✅ Created test token that expires in {seconds} seconds")
    print(f"Token: {token}")
    
    # Check token is initially valid
    valid = token_manager.validate_token(token)
    if valid:
        print("✅ Token is initially valid")
    else:
        print("❌ Token should be valid but is not!")
        return
    
    # Wait for token to expire
    print(f"\nWaiting {seconds} seconds for token to expire...")
    time.sleep(seconds + 1)  # Add buffer
    
    # Check if token is now expired
    valid = token_manager.validate_token(token)
    if valid:
        print("❌ Token should have expired but is still valid!")
    else:
        print("✅ Token has expired as expected!")

def main():
    """Main function"""
    if not HAS_REQUIRED_MODULES:
        print("Required modules not found. Make sure token_manager.py, enhanced_token_manager.py, and db_controller.py are available.")
        return
    
    # Check if jwt module is available for expiry test
    try:
        import jwt
    except ImportError:
        print("Note: PyJWT module not found. Token expiry test will not work.")
        print("Install with: pip install PyJWT")
    
    while True:
        print_menu()
        choice = input("\nEnter choice (1-7): ")
        
        if choice == '1':
            generate_token()
        elif choice == '2':
            validate_token()
        elif choice == '3':
            list_tokens()
        elif choice == '4':
            refresh_token()
        elif choice == '5':
            delete_token()
        elif choice == '6':
            test_expiry()
        elif choice == '7':
            print("\nExiting...")
            break
        else:
            print("\nInvalid choice! Please enter a number between 1 and 7.")
        
        input("\nPress Enter to continue...")

if __name__ == '__main__':
    main()
