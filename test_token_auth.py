#!/usr/bin/env python3
"""
Test and validate the token authentication system for offline usage

This script helps:
1. Generate test tokens with configurable expiry
2. Validate tokens
3. Test offline login
4. Refresh tokens
5. Revoke tokens
6. Test specific user authentication (dmoriello)
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
logging.basicConfig(level=logging.INFO, format='[TEST_TOKEN_AUTH] %(levelname)s - %(message)s')
logger = logging.getLogger("test_token_auth")

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import necessary modules
try:
    from token_manager import TokenManager
    from db_controller import DatabaseController
    HAS_REQUIRED_MODULES = True
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    HAS_REQUIRED_MODULES = False

# Constants
DEFAULT_TOKEN_EXPIRY = 30  # days
TEST_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'secure_offline_jwt_secret_key_for_testing')

def setup_argparse():
    """Set up command line arguments"""
    parser = argparse.ArgumentParser(description='Test and validate token authentication')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Generate token command
    gen_parser = subparsers.add_parser('generate', help='Generate a test token')
    gen_parser.add_argument('--username', '-u', required=True, help='Username for the token')
    gen_parser.add_argument('--expiry', '-e', type=int, default=DEFAULT_TOKEN_EXPIRY, 
                            help=f'Token expiry in days (default: {DEFAULT_TOKEN_EXPIRY})')
    gen_parser.add_argument('--role', '-r', type=int, default=1, 
                            help='Role ID for the token (default: 1, admin)')
    
    # Validate token command
    val_parser = subparsers.add_parser('validate', help='Validate a token')
    val_parser.add_argument('--token', '-t', required=True, help='Token to validate')
    
    # List tokens command
    list_parser = subparsers.add_parser('list', help='List all stored tokens')
    
    # Refresh token command
    refresh_parser = subparsers.add_parser('refresh', help='Refresh a token')
    refresh_parser.add_argument('--token', '-t', required=True, help='Token to refresh')
    
    # Revoke token command
    revoke_parser = subparsers.add_parser('revoke', help='Revoke a token')
    revoke_parser.add_argument('--user-id', '-u', required=True, help='User ID to revoke token for')
    
    # Run test command
    test_parser = subparsers.add_parser('test', help='Run a complete token test cycle')
    test_parser.add_argument('--username', '-u', default='admin', help='Username for testing (default: admin)')
    test_parser.add_argument('--password', '-p', default='admin', help='Password for testing (default: admin)')
    
    return parser

def get_user_id_from_username(username):
    """Get user ID from username using the database controller"""
    try:
        db_controller = DatabaseController(use_encryption=False)
        user = db_controller.fetch_one(
            "SELECT id FROM users WHERE username = ?", 
            (username,)
        )
        
        if user:
            return user['id']
        else:
            logger.error(f"User {username} not found in database")
            return None
    except Exception as e:
        logger.error(f"Error getting user ID: {e}")
        return None

def generate_test_token(username, expiry_days=DEFAULT_TOKEN_EXPIRY, role_id=1):
    """Generate a test token for the given username"""
    logger.info(f"Generating test token for {username} with {expiry_days} days expiry")
    
    # Get user ID from database
    user_id = get_user_id_from_username(username)
    if not user_id:
        print(f"❌ User {username} not found in database")
        return None
    
    # Initialize token manager
    token_manager = TokenManager(
        secret_key=TEST_SECRET_KEY,
        token_expiry_days=expiry_days
    )
    
    # Additional token data
    additional_data = {
        'is_test': True,
        'created_by': 'test_token_auth.py',
        'offline_access': True,
        'is_admin': username == 'admin'  # Simple assumption for testing
    }
    
    # Generate token
    token = token_manager.generate_token(
        user_id=user_id,
        username=username,
        role_id=role_id,
        additional_data=additional_data
    )
    
    # Store token
    token_manager.store_token(user_id, token)
    
    # Save to a specific test tokens directory for reference
    test_tokens_dir = Path(current_dir) / 'instance' / 'test_tokens'
    test_tokens_dir.mkdir(parents=True, exist_ok=True)
    
    token_file = test_tokens_dir / f"test_token_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    token_data = {
        'token': token,
        'created_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(days=expiry_days)).isoformat(),
        'user_id': user_id,
        'username': username,
        'role_id': role_id
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
            
            # Basic validation
            if token:
                token_manager = TokenManager(secret_key=TEST_SECRET_KEY)
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
            
            print(f"  [User ID: {user_id}] {username} - {status}{expiry_info}")
            print(f"    Created: {created_at}")
            print(f"    File: {token_file.name}")
            
        except Exception as e:
            print(f"  Error reading token file {token_file.name}: {e}")

def refresh_token(token):
    """Refresh a token and display new token details"""
    logger.info("Refreshing token...")
    
    token_manager = TokenManager(secret_key=TEST_SECRET_KEY)
    new_token = token_manager.refresh_token(token)
    
    if new_token:
        print("\n✅ Token refreshed successfully")
        print(f"New token: {new_token}")
        
        # Validate the new token
        validate_token(new_token)
        return new_token
    else:
        print("\n❌ Failed to refresh token")
        return None

def revoke_token(user_id):
    """Revoke a token for a user"""
    logger.info(f"Revoking token for user ID {user_id}...")
    
    token_manager = TokenManager(secret_key=TEST_SECRET_KEY)
    result = token_manager.delete_token(user_id)
    
    if result:
        print(f"\n✅ Token for user ID {user_id} revoked successfully")
    else:
        print(f"\n❌ Failed to revoke token for user ID {user_id}")

def test_full_auth_cycle(username='admin', password='admin'):
    """Run a full test cycle of token authentication"""
    print(f"\n🔄 Running full token authentication test cycle for user {username}")
    
    # Step 1: Check if user exists
    user_id = get_user_id_from_username(username)
    if not user_id:
        print(f"❌ User {username} not found in database")
        return
    
    print(f"✅ User {username} found with ID {user_id}")
    
    # Step 2: Generate token (simulating online login)
    print("\n📝 Step 1: Generating token (simulating online login)")
    token = generate_test_token(username, expiry_days=30)
    if not token:
        print("❌ Failed to generate token")
        return
    
    # Step 3: Validate token (simulating offline login)
    print("\n🔍 Step 2: Validating token (simulating offline login)")
    if not validate_token(token):
        print("❌ Token validation failed")
        return
    
    # Step 4: Refresh token (simulating token refresh)
    print("\n🔄 Step 3: Refreshing token (simulating token refresh)")
    new_token = refresh_token(token)
    if not new_token:
        print("❌ Token refresh failed")
        return
    
    # Step 5: Wait a moment and validate the new token
    print("\n⏱️ Step 4: Waiting a moment and validating refreshed token")
    time.sleep(2)
    if not validate_token(new_token):
        print("❌ Refreshed token validation failed")
        return
    
    # Step 6: Revoke token (simulating logout or token revocation)
    print("\n❌ Step 5: Revoking token (simulating logout or token revocation)")
    revoke_token(user_id)
    
    # Step 7: Verify token is revoked
    print("\n🔍 Step 6: Verifying token is revoked")
    token_manager = TokenManager(secret_key=TEST_SECRET_KEY)
    if token_manager.retrieve_token(user_id):
        print("❌ Token was not properly revoked")
    else:
        print("✅ Token successfully revoked")
    
    print("\n✅ Full token authentication test cycle completed successfully")

def main():
    """Main function"""
    if not HAS_REQUIRED_MODULES:
        print("❌ Required modules not found. Make sure token_manager.py and db_controller.py are available.")
        return
    
    parser = setup_argparse()
    args = parser.parse_args()
    
    if args.command == 'generate':
        generate_test_token(args.username, args.expiry, args.role)
    elif args.command == 'validate':
        validate_token(args.token)
    elif args.command == 'list':
        list_stored_tokens()
    elif args.command == 'refresh':
        refresh_token(args.token)
    elif args.command == 'revoke':
        revoke_token(args.user_id)
    elif args.command == 'test':
        test_full_auth_cycle(args.username, args.password)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
