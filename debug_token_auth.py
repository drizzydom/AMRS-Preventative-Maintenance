#!/usr/bin/env python3
"""
Debug utility for testing the offline browser with token authentication

This script helps test the token authentication feature in the offline browser.
It allows creating, validating, and managing tokens for offline authentication.
"""
import os
import sys
import logging
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='[DEBUG_TOKEN_AUTH] %(levelname)s - %(message)s')
logger = logging.getLogger("debug_token_auth")

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import token manager
try:
    from token_manager import TokenManager
    HAS_TOKEN_MANAGER = True
except ImportError as e:
    logger.error(f"Failed to import TokenManager: {e}")
    logger.error("Make sure token_manager.py is in the current directory")
    HAS_TOKEN_MANAGER = False

# Constants
DEFAULT_TOKEN_EXPIRY = 30  # days
TEST_SECRET_KEY = "test_secret_key_for_offline_browser_debugging"

def create_test_token(user_id, username, expiry_days=DEFAULT_TOKEN_EXPIRY):
    """Create a test token for debugging"""
    logger.info(f"Creating test token for user {username} (ID: {user_id}) with {expiry_days} days expiry")
    
    token_manager = TokenManager(secret_key=TEST_SECRET_KEY, token_expiry_days=expiry_days)
    
    # Create additional data for the token
    additional_data = {
        'is_test': True,
        'created_by': 'debug_token_auth.py',
        'purpose': 'testing',
        'offline_access': True
    }
    
    # Generate the token
    token = token_manager.generate_token(
        user_id=user_id,
        username=username,
        role_id=1,  # Assuming role_id 1 is admin for testing
        additional_data=additional_data
    )
    
    # Store the token
    token_manager.store_token(user_id, token)
    
    # Also save to a specific debug tokens directory for reference
    debug_tokens_dir = Path(current_dir) / 'instance' / 'debug_tokens'
    debug_tokens_dir.mkdir(parents=True, exist_ok=True)
    
    token_file = debug_tokens_dir / f"debug_token_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    token_data = {
        'token': token,
        'created_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(days=expiry_days)).isoformat(),
        'user_id': user_id,
        'username': username
    }
    
    with open(token_file, 'w') as f:
        json.dump(token_data, f, indent=2)
    
    print(f"\n✅ Test token created and stored in {token_file}")
    print(f"Token value (for manual testing): {token}")
    
    return token

def validate_token(token):
    """Validate a token and display its details"""
    logger.info("Validating token...")
    
    token_manager = TokenManager(secret_key=TEST_SECRET_KEY)
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
                
        return True
    else:
        print("\n❌ Token is invalid or expired")
        return False

def list_stored_tokens():
    """List all stored tokens"""
    logger.info("Listing stored tokens...")
    
    token_manager = TokenManager(secret_key=TEST_SECRET_KEY)
    token_files = list(token_manager.token_dir.glob("user_*_token.json"))
    
    if not token_files:
        print("\nNo stored tokens found")
        return
    
    print(f"\nFound {len(token_files)} stored tokens:")
    
    for token_file in token_files:
        try:
            with open(token_file, 'r') as f:
                token_data = json.load(f)
            
            user_id = token_data.get('user_id', 'unknown')
            created_at = token_data.get('created_at', 'unknown')
            token = token_data.get('token')
            
            # Basic validation (not full validation to avoid cluttering output)
            if token:
                token_manager = TokenManager(secret_key=TEST_SECRET_KEY)
                payload = token_manager.validate_token(token)
                status = "VALID" if payload else "INVALID/EXPIRED"
            else:
                status = "INVALID (no token)"
            
            print(f"  {token_file.name}: User ID {user_id}, Created {created_at}, Status: {status}")
            
        except Exception as e:
            logger.error(f"  Error reading {token_file.name}: {e}")

def delete_token(user_id):
    """Delete a stored token"""
    logger.info(f"Deleting token for user ID {user_id}...")
    
    token_manager = TokenManager(secret_key=TEST_SECRET_KEY)
    result = token_manager.delete_token(user_id)
    
    if result:
        print(f"\n✅ Token for user ID {user_id} deleted successfully")
    else:
        print(f"\n❌ Failed to delete token for user ID {user_id}")

def simulate_offline_login(user_id):
    """Simulate an offline login using a stored token"""
    logger.info(f"Simulating offline login for user ID {user_id}...")
    
    token_manager = TokenManager(secret_key=TEST_SECRET_KEY)
    token = token_manager.retrieve_token(user_id)
    
    if not token:
        print(f"\n❌ No token found for user ID {user_id}")
        return False
    
    payload = token_manager.validate_token(token)
    
    if not payload:
        print("\n❌ Token is invalid or expired")
        return False
    
    print(f"\n✅ Offline login successful for user {payload.get('username')} (ID: {payload.get('sub')})")
    return True

def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description='Debug utility for offline browser token authentication')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Create token command
    create_parser = subparsers.add_parser('create', help='Create a test token')
    create_parser.add_argument('--user-id', type=int, required=True, help='User ID')
    create_parser.add_argument('--username', type=str, required=True, help='Username')
    create_parser.add_argument('--expiry', type=int, default=DEFAULT_TOKEN_EXPIRY, help='Token expiry in days')
    
    # Validate token command
    validate_parser = subparsers.add_parser('validate', help='Validate a token')
    validate_parser.add_argument('--token', type=str, required=True, help='Token to validate')
    
    # List tokens command
    list_parser = subparsers.add_parser('list', help='List all stored tokens')
    
    # Delete token command
    delete_parser = subparsers.add_parser('delete', help='Delete a stored token')
    delete_parser.add_argument('--user-id', type=int, required=True, help='User ID')
    
    # Simulate offline login command
    login_parser = subparsers.add_parser('login', help='Simulate offline login')
    login_parser.add_argument('--user-id', type=int, required=True, help='User ID')
    
    args = parser.parse_args()
    
    if not HAS_TOKEN_MANAGER:
        print("\n❌ TokenManager module not available. Please create token_manager.py first.")
        sys.exit(1)
    
    print("=" * 60)
    print("AMRS Preventative Maintenance - Offline Token Authentication Debug")
    print("=" * 60)
    
    if args.command == 'create':
        create_test_token(args.user_id, args.username, args.expiry)
    elif args.command == 'validate':
        validate_token(args.token)
    elif args.command == 'list':
        list_stored_tokens()
    elif args.command == 'delete':
        delete_token(args.user_id)
    elif args.command == 'login':
        simulate_offline_login(args.user_id)
    else:
        parser.print_help()
        print("\nExample usage:")
        print("  python debug_token_auth.py create --user-id 1 --username admin")
        print("  python debug_token_auth.py validate --token <token_value>")
        print("  python debug_token_auth.py list")
        print("  python debug_token_auth.py delete --user-id 1")
        print("  python debug_token_auth.py login --user-id 1")

if __name__ == "__main__":
    main()
