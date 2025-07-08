#!/usr/bin/env python3
"""
Migration script to add remember token fields to users table.
This adds support for "Remember Me" functionality.
"""

import sqlite3
import os
import sys
from datetime import datetime

def add_remember_me_fields():
    """Add remember token fields to the users table"""
    
    # Database path
    db_path = 'maintenance.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found. Creating new database...")
        # If database doesn't exist, the app will create it with all fields
        return True
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if remember token fields already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        fields_to_add = []
        
        if 'remember_token' not in columns:
            fields_to_add.append('remember_token TEXT DEFAULT NULL')
        
        if 'remember_token_expiration' not in columns:
            fields_to_add.append('remember_token_expiration DATETIME DEFAULT NULL')
        
        if 'remember_enabled' not in columns:
            fields_to_add.append('remember_enabled BOOLEAN DEFAULT 0')
        
        # Add missing fields
        for field in fields_to_add:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {field}")
                print(f"Added field: {field}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    raise e
                print(f"Field already exists: {field}")
        
        conn.commit()
        print("Remember me fields migration completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"Error during migration: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Adding remember me fields to users table...")
    success = add_remember_me_fields()
    if success:
        print("Migration completed successfully!")
        sys.exit(0)
    else:
        print("Migration failed!")
        sys.exit(1)
