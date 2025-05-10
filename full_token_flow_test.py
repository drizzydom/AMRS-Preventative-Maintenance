#!/usr/bin/env python3
"""
Full test of the offline token authentication flow.

This script tests the complete end-to-end token authentication flow:
1. Generate a token for a user
2. Store the token
3. Validate the token
4. Refresh the token
5. Simulate offline usage

Usage:
    python full_token_flow_test.py --username <username> [--expiry <days>]
"""
import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='[TOKEN_FLOW_TEST] %(levelname)s - %(message)s')
logger = logging.getLogger("token_flow_test")

def setup_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Test the full token authentication flow")
    parser.add_argument("--username", required=True, help="Username to create token for")
    parser.add_argument("--expiry", type=int, default=30, help="Token expiry in days (default: 30)")
    parser.add_argument("--enhanced", action="store_true", help="Use enhanced token manager")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()

def get_token_manager(args):
    """Get the appropriate token manager based on arguments"""
    if args.enhanced:
        try:
            from enhanced_token_manager import EnhancedTokenManager
            return EnhancedTokenManager(token_expiry_days=args.expiry)
        except ImportError:
            logger.warning("Enhanced token manager not available, falling back to standard")
            
    # Use standard token manager
    try:
        from token_manager import TokenManager
        return TokenManager(token_expiry_days=args.expiry)
    except ImportError:
        logger.error("Cannot import TokenManager. Make sure token_manager.py is available.")
        sys.exit(1)

def get_user_id(username):
    """Get or create a user ID for testing"""
    try:
        from db_controller import DatabaseController
        db = DatabaseController()
        
        # Try to find the user in the database
        user = db.get_user_by_username(username)
        if user:
            logger.info(f"Found existing user: {username} (ID: {user.get('id')})")
            return user.get('id')
        
        # Create a test user
        logger.info(f"User {username} not found, creating test user")
        user_id = db.create_user(
            username=username,
            email=f"{username}@example.com",
            full_name=f"Test User {username}",
            password="password123", 
            is_admin=False,
            role_id=2  # Regular user role
        )
        
        logger.info(f"Created new test user: {username} (ID: {user_id})")
        return user_id
        
    except Exception as e:
        logger.error(f"Error getting/creating user: {e}")
        # Return a fake user ID for testing
        logger.info("Using dummy user ID for testing")
        return 1

def test_token_flow(args, token_manager, user_id):
    """Test the complete token authentication flow"""
    username = args.username
    
    # Step 1: Generate a token
    logger.info(f"Step 1: Generating token for {username} (ID: {user_id})")
    token = token_manager.generate_token(user_id, username, role_id=2)
    
    if not token:
        logger.error("Failed to generate token")
        return False
    
    logger.info(f"Token generated successfully (first 20 chars): {token[:20]}...")
    
    # Step 2: Store the token
    logger.info(f"Step 2: Storing token for {username}")
    success = token_manager.store_token(user_id, token)
    
    if not success:
        logger.error("Failed to store token")
        return False
        
    logger.info("Token stored successfully")
    
    # Step 3: Retrieve and validate the token
    logger.info(f"Step 3: Retrieving and validating token for {username}")
    retrieved_token = token_manager.retrieve_token(user_id)
    
    if not retrieved_token:
        logger.error("Failed to retrieve token")
        return False
    
    logger.info("Token retrieved successfully")
    
    # Validate token
    payload = token_manager.validate_token(retrieved_token)
    
    if not payload:
        logger.error("Failed to validate token")
        return False
        
    logger.info(f"Token validated successfully. Payload: {payload}")
    
    # Step 4: Refresh the token
    logger.info(f"Step 4: Refreshing token for {username}")
    refreshed_token = token_manager.refresh_token(retrieved_token)
    
    if not refreshed_token:
        logger.error("Failed to refresh token")
        return False
        
    logger.info("Token refreshed successfully")
    
    # Validate refreshed token
    refreshed_payload = token_manager.validate_token(refreshed_token)
    
    if not refreshed_payload:
        logger.error("Failed to validate refreshed token")
        return False
        
    logger.info(f"Refreshed token validated successfully. Payload: {refreshed_payload}")
    
    # Step 5: Simulate offline usage
    logger.info(f"Step 5: Simulating offline usage for {username}")
    
    # Create a token file that would be used in offline mode
    offline_token_dir = Path("instance") / "offline_tokens"
    offline_token_dir.mkdir(parents=True, exist_ok=True)
    
    offline_token_file = offline_token_dir / f"offline_token_{username}.json"
    
    offline_token_data = {
        "token": refreshed_token,
        "username": username,
        "user_id": user_id,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(days=args.expiry)).isoformat()
    }
    
    with open(offline_token_file, "w") as f:
        json.dump(offline_token_data, f, indent=2)
        
    logger.info(f"Offline token file created: {offline_token_file}")
    
    # Test the offline token
    with open(offline_token_file, "r") as f:
        loaded_token_data = json.load(f)
        
    offline_token = loaded_token_data.get("token")
    offline_payload = token_manager.validate_token(offline_token)
    
    if not offline_payload:
        logger.error("Failed to validate offline token")
        return False
        
    logger.info(f"Offline token validated successfully. Payload: {offline_payload}")
    
    return True

def main():
    """Main function"""
    args = setup_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    logger.info(f"Starting token flow test for user: {args.username}")
    logger.info(f"Token expiry days: {args.expiry}")
    logger.info(f"Using enhanced token manager: {args.enhanced}")
    
    # Get token manager implementation
    token_manager = get_token_manager(args)
    
    # Get user ID for testing
    user_id = get_user_id(args.username)
    
    # Run the full flow test
    success = test_token_flow(args, token_manager, user_id)
    
    if success:
        logger.info("✅ All token authentication flow tests PASSED!")
        return 0
    else:
        logger.error("❌ Token authentication flow tests FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
