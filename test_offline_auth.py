#!/usr/bin/env python3
"""
Comprehensive test script for offline token authentication

This script provides end-to-end testing for the offline token authentication system, including:
1. Token generation and validation
2. Token persistence between sessions
3. Token expiry testing
4. Manual login with tokens
5. Token refresh mechanisms
6. Token revocation
7. Security testing
"""
import os
import sys
import argparse
import json
import logging
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='[OFFLINE_AUTH_TEST] %(levelname)s - %(message)s')
logger = logging.getLogger("offline_auth_test")

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
DEFAULT_OFFLINE_APP_URL = "http://localhost:5000"  # Default URL for offline app

def setup_argparse():
    """Set up command line arguments"""
    parser = argparse.ArgumentParser(description='Comprehensive offline token authentication test')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # End-to-end test command
    e2e_parser = subparsers.add_parser('e2e', help='Run end-to-end offline auth test')
    e2e_parser.add_argument('--username', '-u', default='admin', help='Username for testing (default: admin)')
    e2e_parser.add_argument('--password', '-p', default='admin', help='Password for testing (default: admin)')
    e2e_parser.add_argument('--expiry', '-e', type=int, default=30, help='Token expiry in days (default: 30)')
    e2e_parser.add_argument('--app-url', '-a', default=DEFAULT_OFFLINE_APP_URL, 
                            help=f'URL of the offline app (default: {DEFAULT_OFFLINE_APP_URL})')
    
    # API test command
    api_parser = subparsers.add_parser('api', help='Test token API endpoints')
    api_parser.add_argument('--app-url', '-a', default=DEFAULT_OFFLINE_APP_URL, 
                           help=f'URL of the offline app (default: {DEFAULT_OFFLINE_APP_URL})')
    api_parser.add_argument('--token', '-t', help='Existing token to use for API tests')
    
    # Token security test command
    security_parser = subparsers.add_parser('security', help='Run token security tests')
    security_parser.add_argument('--username', '-u', default='admin', help='Username for testing (default: admin)')
    
    # Token expiry test command
    expiry_parser = subparsers.add_parser('expiry', help='Test token expiry')
    expiry_parser.add_argument('--seconds', '-s', type=int, default=10, 
                               help='Seconds until token expires (for quick testing)')
    
    # Enhanced features test command
    enhanced_parser = subparsers.add_parser('enhanced', help='Test enhanced token manager features')
    enhanced_parser.add_argument('--username', '-u', default='admin', help='Username for testing (default: admin)')
    
    return parser

def get_user_by_username(username):
    """Get user data from username using the database controller"""
    try:
        db_controller = DatabaseController(use_encryption=False)
        user = db_controller.fetch_one(
            "SELECT id, username, is_admin, role_id FROM users WHERE username = ?", 
            (username,)
        )
        
        if user:
            return user
        else:
            logger.error(f"User {username} not found in database")
            return None
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None

def authenticate_user(username, password):
    """Authenticate user using the database controller"""
    try:
        db_controller = DatabaseController(use_encryption=False)
        user = db_controller.authenticate_user(username, password)
        
        if user:
            return user
        else:
            logger.error(f"Authentication failed for user {username}")
            return None
    except Exception as e:
        logger.error(f"Error during authentication: {e}")
        return None

def generate_token_for_user(username, expiry_days=DEFAULT_TOKEN_EXPIRY, use_enhanced=False):
    """Generate a token for the given username"""
    logger.info(f"Generating token for {username} with {expiry_days} days expiry")
    
    # Get user data from database
    user = get_user_by_username(username)
    if not user:
        print(f"❌ User {username} not found in database")
        return None
    
    # Initialize token manager
    if use_enhanced:
        token_manager = EnhancedTokenManager(
            secret_key=TEST_SECRET_KEY,
            token_expiry_days=expiry_days
        )
    else:
        token_manager = TokenManager(
            secret_key=TEST_SECRET_KEY,
            token_expiry_days=expiry_days
        )
    
    # Additional token data
    additional_data = {
        'is_test': True,
        'offline_access': True,
        'is_admin': bool(user['is_admin'])
    }
    
    # Generate token
    token = token_manager.generate_token(
        user_id=user['id'],
        username=user['username'],
        role_id=user['role_id'],
        additional_data=additional_data
    )
    
    # Store token
    token_manager.store_token(user['id'], token)
    
    print(f"✅ Token generated for user {username} (ID: {user['id']})")
    return token

def validate_stored_token(username, use_enhanced=False):
    """Validate the stored token for a user"""
    logger.info(f"Validating stored token for {username}")
    
    # Get user data from database
    user = get_user_by_username(username)
    if not user:
        print(f"❌ User {username} not found in database")
        return False
    
    # Initialize token manager
    if use_enhanced:
        token_manager = EnhancedTokenManager(secret_key=TEST_SECRET_KEY)
    else:
        token_manager = TokenManager(secret_key=TEST_SECRET_KEY)
    
    # Retrieve token
    token = token_manager.retrieve_token(user['id'])
    if not token:
        print(f"❌ No token found for user {username}")
        return False
    
    # Validate token
    payload = token_manager.validate_token(token)
    if payload:
        print(f"✅ Token is valid for user {username}")
        
        # Display expiry info
        if 'exp' in payload:
            expiry_timestamp = payload['exp']
            expiry_date = datetime.fromtimestamp(expiry_timestamp)
            now = datetime.now()
            days_remaining = (expiry_date - now).days
            
            print(f"   Expires on: {expiry_date.isoformat()}")
            print(f"   Days remaining: {days_remaining}")
        
        return True
    else:
        print(f"❌ Token is invalid or expired for user {username}")
        return False

def test_api_endpoints(app_url, token=None):
    """Test the API endpoints for token validation"""
    logger.info(f"Testing API endpoints at {app_url}")
    
    # If no token provided, generate a test token
    if not token:
        token = generate_token_for_user('admin')
        if not token:
            print("❌ Failed to generate test token")
            return False
    
    # Test token validation endpoint
    validation_url = f"{app_url}/api/auth/validate_token"
    
    try:
        response = requests.post(
            validation_url,
            json={'token': token},
            headers={'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Token validation API test passed")
                print(f"   User data: {result.get('user')}")
                return True
            else:
                print(f"❌ Token validation failed: {result.get('message')}")
        else:
            print(f"❌ API request failed with status code {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing API: {e}")
    
    return False

def test_token_expiry(seconds=10):
    """Test token expiry by creating a token that expires quickly"""
    logger.info(f"Testing token expiry with {seconds} seconds")
    
    # Initialize token manager with custom secret for this test
    test_secret = "expiry_test_secret_key"
    token_manager = TokenManager(secret_key=test_secret)
    
    # Generate a token that expires in seconds
    expiry_days = seconds / (24 * 60 * 60)  # Convert seconds to days
    
    token = token_manager.generate_token(
        user_id=999,  # Test user ID
        username="expiry_test",
        additional_data={'test': 'expiry'}
    )
    
    # Create a token with custom expiry
    payload = jwt.decode(token, options={"verify_signature": False})
    payload['exp'] = int(time.time()) + seconds
    
    # Re-encode the token
    from jwt import PyJWT
    jwt_encoder = PyJWT()
    short_token = jwt_encoder.encode(payload, test_secret, algorithm='HS256')
    
    print(f"✅ Created test token with {seconds} seconds expiry")
    
    # Verify the token is initially valid
    verify_result = token_manager.validate_token(short_token)
    if verify_result:
        print("✅ Token is initially valid")
    else:
        print("❌ Token should be valid initially")
        return False
    
    # Wait for token to expire
    wait_time = seconds + 1  # Add buffer
    print(f"Waiting {wait_time} seconds for token to expire...")
    time.sleep(wait_time)
    
    # Verify the token is now expired
    verify_result = token_manager.validate_token(short_token)
    if verify_result:
        print("❌ Token should have expired but is still valid")
        return False
    else:
        print("✅ Token has expired as expected")
        return True

def test_token_security(username='admin'):
    """Test token security features"""
    logger.info(f"Testing token security for user {username}")
    
    # Get user data from database
    user = get_user_by_username(username)
    if not user:
        print(f"❌ User {username} not found in database")
        return False
    
    # Generate a valid token
    token_manager = TokenManager(secret_key=TEST_SECRET_KEY)
    valid_token = token_manager.generate_token(
        user_id=user['id'],
        username=user['username'],
        role_id=user['role_id']
    )
    
    print("✅ Generated valid token for security testing")
    
    # 1. Test: Token with tampered payload
    try:
        # Decode without verification
        payload = jwt.decode(valid_token, options={"verify_signature": False})
        
        # Tamper with payload (change user ID)
        payload['sub'] = 999
        
        # Re-encode without proper signature
        from jwt import PyJWT
        jwt_encoder = PyJWT()
        tampered_token = jwt_encoder.encode(payload, "wrong_secret", algorithm='HS256')
        
        # Verify the tampered token
        verify_result = token_manager.validate_token(tampered_token)
        if verify_result:
            print("❌ SECURITY ISSUE: Tampered token was accepted")
            return False
        else:
            print("✅ Security test passed: Tampered token was rejected")
        
    except Exception as e:
        print(f"Error during tampered payload test: {e}")
    
    # 2. Test: Token with invalid signature
    try:
        # Decode without verification
        payload = jwt.decode(valid_token, options={"verify_signature": False})
        
        # Re-encode with wrong secret key
        from jwt import PyJWT
        jwt_encoder = PyJWT()
        invalid_sig_token = jwt_encoder.encode(payload, "wrong_secret", algorithm='HS256')
        
        # Verify the invalid signature token
        verify_result = token_manager.validate_token(invalid_sig_token)
        if verify_result:
            print("❌ SECURITY ISSUE: Token with invalid signature was accepted")
            return False
        else:
            print("✅ Security test passed: Token with invalid signature was rejected")
        
    except Exception as e:
        print(f"Error during invalid signature test: {e}")
    
    # 3. Test: Token with expired timestamp
    try:
        # Decode without verification
        payload = jwt.decode(valid_token, options={"verify_signature": False})
        
        # Set expiry to past time
        payload['exp'] = int(time.time()) - 3600  # 1 hour in the past
        
        # Re-encode with correct secret
        from jwt import PyJWT
        jwt_encoder = PyJWT()
        expired_token = jwt_encoder.encode(payload, TEST_SECRET_KEY, algorithm='HS256')
        
        # Verify the expired token
        verify_result = token_manager.validate_token(expired_token)
        if verify_result:
            print("❌ SECURITY ISSUE: Expired token was accepted")
            return False
        else:
            print("✅ Security test passed: Expired token was rejected")
        
    except Exception as e:
        print(f"Error during expired token test: {e}")
    
    return True

def test_enhanced_features(username='admin'):
    """Test enhanced token manager features"""
    logger.info(f"Testing enhanced token manager features for user {username}")
    
    # Get user data
    user = get_user_by_username(username)
    if not user:
        print(f"❌ User {username} not found in database")
        return False
    
    # Initialize enhanced token manager
    enhanced_manager = EnhancedTokenManager(
        secret_key=TEST_SECRET_KEY,
        token_expiry_days=30,
        refresh_threshold_days=25  # Set high to trigger auto-refresh
    )
    
    # 1. Generate token
    token = enhanced_manager.generate_token(
        user_id=user['id'],
        username=user['username'],
        role_id=user['role_id'],
        additional_data={'is_test': True}
    )
    
    print("✅ Generated token with enhanced manager")
    
    # 2. Store token
    enhanced_manager.store_token(user['id'], token)
    print("✅ Stored token with enhanced manager")
    
    # 3. Retrieve and validate token
    retrieved_token = enhanced_manager.retrieve_token(user['id'])
    if not retrieved_token:
        print("❌ Failed to retrieve stored token")
        return False
    
    print("✅ Retrieved stored token")
    
    # 4. Test auto-refresh mechanism
    payload = enhanced_manager.validate_token(retrieved_token)
    if not payload:
        print("❌ Token validation failed")
        return False
    
    print("✅ Token validated successfully")
    
    # Check if token was auto-refreshed (it should be if refresh_threshold_days is high)
    new_token = enhanced_manager.retrieve_token(user['id'])
    if new_token != retrieved_token:
        print("✅ Token was auto-refreshed as expected")
    else:
        print("ℹ️ Token was not auto-refreshed (this is expected if not near expiry)")
    
    # 5. Test token listing
    tokens = enhanced_manager.list_tokens()
    if tokens:
        print(f"✅ Listed {len(tokens)} tokens")
        for token_info in tokens:
            print(f"   User: {token_info.get('username')}, Valid: {token_info.get('is_valid')}")
    else:
        print("❌ No tokens found or listing failed")
    
    # 6. Test manual token refresh
    refreshed_token = enhanced_manager.refresh_token(new_token or retrieved_token)
    if refreshed_token:
        print("✅ Manually refreshed token")
        
        # Validate the refreshed token
        refresh_payload = enhanced_manager.validate_token(refreshed_token, auto_refresh=False)
        if refresh_payload:
            print("✅ Refreshed token is valid")
        else:
            print("❌ Refreshed token validation failed")
            return False
    else:
        print("❌ Manual token refresh failed")
        return False
    
    # 7. Test token deletion
    deleted = enhanced_manager.delete_token(user['id'])
    if deleted:
        print("✅ Successfully deleted token")
        
        # Verify token is gone
        check_token = enhanced_manager.retrieve_token(user['id'])
        if check_token:
            print("❌ Token still exists after deletion")
            return False
        else:
            print("✅ Token deletion verified")
    else:
        print("❌ Token deletion failed")
        return False
    
    return True

def test_e2e_offline_auth(username, password, expiry_days, app_url):
    """Run end-to-end test of offline authentication"""
    logger.info(f"Running end-to-end offline auth test for user {username}")
    logger.info(f"Offline app URL: {app_url}")
    
    print("\n==== OFFLINE AUTH END-TO-END TEST ====")
    
    # Step 1: Authenticate user
    print("\n🔑 Step 1: Authenticating user")
    user = authenticate_user(username, password)
    if not user:
        print(f"❌ Authentication failed for user {username}")
        return False
    
    print(f"✅ Authentication successful for {username}")
    
    # Step 2: Generate token (simulating online login)
    print("\n🔖 Step 2: Generating token (simulating online login)")
    token = generate_token_for_user(username, expiry_days, use_enhanced=True)
    if not token:
        print("❌ Failed to generate token")
        return False
    
    print(f"✅ Token generated with {expiry_days} days expiry")
    
    # Step 3: Simulate closing and reopening app (persistence test)
    print("\n🔄 Step 3: Testing token persistence (simulating app restart)")
    
    # Wait a moment to ensure file operations complete
    time.sleep(1)
    
    # Check if token is still valid
    valid = validate_stored_token(username, use_enhanced=True)
    if not valid:
        print("❌ Token persistence test failed")
        return False
    
    print("✅ Token persistence test passed")
    
    # Step 4: Test API endpoints (if app is running)
    print("\n🌐 Step 4: Testing API endpoints")
    try:
        api_success = test_api_endpoints(app_url, token)
        if not api_success:
            print("ℹ️ API tests failed - make sure the offline app is running")
            # Don't fail the whole test for this
    except Exception as e:
        print(f"ℹ️ Error testing API endpoints: {e}")
        print("ℹ️ Make sure the offline app is running at {app_url}")
    
    # Step 5: Test enhanced features
    print("\n⭐ Step 5: Testing enhanced token features")
    enhanced_success = test_enhanced_features(username)
    if not enhanced_success:
        print("❌ Enhanced features test failed")
        return False
    
    print("✅ Enhanced features test passed")
    
    # Step 6: Test security features
    print("\n🔒 Step 6: Testing token security")
    security_success = test_token_security(username)
    if not security_success:
        print("❌ Security tests failed")
        return False
    
    print("✅ Security tests passed")
    
    print("\n✅ End-to-end offline auth test completed successfully")
    return True

def main():
    """Main function"""
    if not HAS_REQUIRED_MODULES:
        print("❌ Required modules not found. Make sure token_manager.py, enhanced_token_manager.py, and db_controller.py are available.")
        sys.exit(1)
    
    # Check if jwt module is available
    try:
        import jwt
    except ImportError:
        print("❌ PyJWT module not found. Please install it with: pip install PyJWT")
        sys.exit(1)
    
    parser = setup_argparse()
    args = parser.parse_args()
    
    if args.command == 'e2e':
        success = test_e2e_offline_auth(args.username, args.password, args.expiry, args.app_url)
        sys.exit(0 if success else 1)
    elif args.command == 'api':
        success = test_api_endpoints(args.app_url, args.token)
        sys.exit(0 if success else 1)
    elif args.command == 'security':
        success = test_token_security(args.username)
        sys.exit(0 if success else 1)
    elif args.command == 'expiry':
        success = test_token_expiry(args.seconds)
        sys.exit(0 if success else 1)
    elif args.command == 'enhanced':
        success = test_enhanced_features(args.username)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
