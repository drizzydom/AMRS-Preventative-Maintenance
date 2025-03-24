#!/usr/bin/env python3
"""
Script to add password reset columns to the User table.
Run this script to fix the "no such column: user.reset_token" error.
"""

import sqlite3
import os
import sys

def add_password_reset_columns():
    """Add reset_token and reset_token_expiration columns to the user table."""
    # Path to the SQLite database
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'maintenance.db')
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return False
        
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(user)")
        columns = [col[1] for col in cursor.fetchall()]
        
        columns_added = False
        
        # Add reset_token column if it doesn't exist
        if 'reset_token' not in columns:
            print("Adding reset_token column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN reset_token VARCHAR(100)")
            columns_added = True
        else:
            print("reset_token column already exists")
            
        # Add reset_token_expiration if it doesn't exist
        if 'reset_token_expiration' not in columns:
            print("Adding reset_token_expiration column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN reset_token_expiration DATETIME")
            columns_added = True
        else:
            print("reset_token_expiration column already exists")
            
        conn.commit()
        conn.close()
        
        if columns_added:
            print("Password reset columns added successfully!")
        else:
            print("No changes needed. Password reset columns already exist.")
        
        return True
    except Exception as e:
        print(f"Error adding password reset columns: {str(e)}")
        return False

if __name__ == "__main__":
    success = add_password_reset_columns()
    sys.exit(0 if success else 1)
