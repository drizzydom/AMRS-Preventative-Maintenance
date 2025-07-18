#!/usr/bin/env python3
"""
Script to fix user passwords in the local database after sync.
This script should be run after syncing from the online database
when the password hashes are not properly synced.
"""

import sqlite3
from werkzeug.security import generate_password_hash
from models import hash_value

def fix_user_passwords():
    """Fix user passwords in the local database."""
    # Common passwords for users - this would need to be updated based on actual user passwords
    # In a real scenario, you'd want to coordinate with users to set their passwords
    user_passwords = {
        'dmoriello': 'Sm@rty123',
        'demo': 'demo123',
        'admin': 'admin123',
        # Add other known user passwords here
    }
    
    conn = sqlite3.connect('maintenance.db')
    cursor = conn.cursor()
    
    print("Fixing user passwords...")
    
    for username, password in user_passwords.items():
        username_hash = hash_value(username)
        password_hash = generate_password_hash(password)
        
        # Update the user's password hash
        cursor.execute("""
            UPDATE users 
            SET password_hash = ? 
            WHERE username_hash = ?
        """, (password_hash, username_hash))
        
        if cursor.rowcount > 0:
            print(f"Updated password for user: {username}")
        else:
            print(f"User not found: {username}")
    
    # For users without known passwords, set them to require password reset
    cursor.execute("""
        SELECT id, username_hash 
        FROM users 
        WHERE password_hash LIKE '%temp_password_needs_reset%'
    """)
    
    temp_users = cursor.fetchall()
    for user_id, _ in temp_users:
        reset_password = f"reset_required_{user_id}"
        reset_hash = generate_password_hash(reset_password)
        cursor.execute("""
            UPDATE users 
            SET password_hash = ? 
            WHERE id = ?
        """, (reset_hash, user_id))
        print(f"Set password reset required for user ID: {user_id}")
    
    conn.commit()
    conn.close()
    print("Password fix completed!")

if __name__ == "__main__":
    fix_user_passwords()
