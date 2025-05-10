#!/usr/bin/env python3
"""
Simple script to test the token authentication for user 'dmoriello'
"""

from db_controller import DatabaseController
from token_manager import TokenManager
import json

# Create a database controller
db = DatabaseController(use_encryption=False)

# Authenticate user
username = 'dmoriello'
password = 'password123'

print(f"Testing authentication for user '{username}'")
user_data = db.authenticate_user(username, password)

if not user_data:
    print(f"Authentication failed for user '{username}'")
    exit(1)
    
print(f"Authentication successful for user '{username}': {user_data}")

# Create token manager
secret_key = 'secure_offline_jwt_secret_key_for_testing'
token_manager = TokenManager(secret_key=secret_key)

# Generate token
print(f"Generating token for user_id: {user_data['id']} (type: {type(user_data['id']).__name__})")
token = token_manager.generate_token(
    user_id=user_data['id'],
    username=user_data['username'],
    role_id=user_data['role_id'],
    additional_data={
        'is_admin': user_data['is_admin'],
        'offline_access': True
    }
)

if not token:
    print("Failed to generate token")
    exit(1)
    
print(f"Token generated successfully: {token[:50]}...")

# Validate token
payload = token_manager.validate_token(token)
if not payload:
    print("Token validation failed")
    exit(1)
    
print(f"Token validation successful: {json.dumps(payload, indent=2)}")
print(f"User ID in payload 'sub': {payload.get('sub')} (type: {type(payload.get('sub')).__name__})")

# Test token refresh
refreshed_token = token_manager.refresh_token(token)
if not refreshed_token:
    print("Token refresh failed")
    exit(1)
    
print(f"Token refresh successful: {refreshed_token[:50]}...")

# Validate refreshed token
refreshed_payload = token_manager.validate_token(refreshed_token)
if not refreshed_payload:
    print("Refreshed token validation failed")
    exit(1)
    
print(f"Refreshed token validation successful: {json.dumps(refreshed_payload, indent=2)}")
print(f"User ID in refreshed payload 'sub': {refreshed_payload.get('sub')} (type: {type(refreshed_payload.get('sub')).__name__})")

print("\nDmoriello token authentication test completed successfully!")
