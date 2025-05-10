#!/usr/bin/env python3
"""
List all users in the database and test authentication
"""

from db_controller import DatabaseController
from werkzeug.security import generate_password_hash, check_password_hash

# Create database controller
db = DatabaseController(use_encryption=False)

# List all users
print("=== All Users in Database ===")
users = db.fetch_all('SELECT id, username, password_hash FROM users')
for user in users:
    print(f"ID: {user['id']}, Username: '{user['username']}'")
    has_password = bool(user['password_hash'])
    print(f"  Has password hash: {has_password}")

# Test dmoriello specifically
print("\n=== Testing dmoriello authentication ===")
test_user = db.fetch_one('SELECT * FROM users WHERE username = ?', ('dmoriello',))
if test_user:
    print(f"Found user 'dmoriello' with ID: {test_user['id']}")
    print(f"Password hash: {test_user['password_hash'][:20]}...")
    
    # Test authentication
    auth_result = db.authenticate_user('dmoriello', 'password123')
    print(f"Authentication result: {auth_result}")

# Test with non-exact username case
print("\n=== Testing case-insensitive usernames ===")
variations = ['Dmoriello', 'DMORIELLO', 'DMoriello', 'dmoriello']
for variation in variations:
    auth_result = db.authenticate_user(variation, 'password123')
    print(f"Authentication with '{variation}': {auth_result is not None}")

# Fix the password one more time
print("\n=== Updating password for dmoriello ===")
user = db.fetch_one('SELECT id FROM users WHERE username = ?', ('dmoriello',))
if user:
    password_hash = generate_password_hash('password123')
    db.execute_query(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (password_hash, user['id'])
    )
    print(f"Password updated for user ID {user['id']}")
    
    # Test authentication again
    auth_result = db.authenticate_user('dmoriello', 'password123')
    print(f"Authentication after update: {auth_result is not None}")
else:
    print("User 'dmoriello' not found")

print("\nDone!")
