#!/usr/bin/env python3
"""
Database Reset Utility

This script clears out the database so that the admin user will be regenerated
on the next application launch. Use with caution - all data will be lost!
"""

import os
import sys
import sqlite3
import shutil
import datetime
import argparse

def get_db_path():
    """Get the path to the database file based on environment"""
    if os.environ.get('RENDER'):
        # Render production environment
        return '/var/data/maintenance.db'
    else:
        # Local development environment
        instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
        return os.path.join(instance_path, 'maintenance.db')

def backup_database(db_path):
    """Create a backup of the database before resetting"""
    if not os.path.exists(db_path):
        print(f"No database found at {db_path}, nothing to backup.")
        return None

    # Create backup directory if it doesn't exist
    backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    # Generate backup filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f'pre_reset_{timestamp}.db')
    
    # Copy database file
    try:
        shutil.copy2(db_path, backup_path)
        print(f"Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"Failed to create backup: {str(e)}")
        return None

def reset_database(db_path, method='delete'):
    """Reset the database using the specified method"""
    if method == 'delete':
        # Simple delete of the database file
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print(f"Database file deleted: {db_path}")
                return True
            except Exception as e:
                print(f"Error deleting database file: {str(e)}")
                return False
        else:
            print(f"No database file found at {db_path}. Nothing to delete.")
            return True
    elif method == 'truncate':
        # Drop all tables but keep the file
        if not os.path.exists(db_path):
            print(f"No database file found at {db_path}. Nothing to truncate.")
            return True
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            # Drop each table
            for table in tables:
                if table[0] != 'sqlite_sequence':  # Skip SQLite internal tables
                    cursor.execute(f"DROP TABLE IF EXISTS {table[0]};")
            
            conn.commit()
            conn.close()
            print(f"All tables dropped from database: {db_path}")
            return True
        except Exception as e:
            print(f"Error truncating database: {str(e)}")
            return False
    else:
        print(f"Unknown reset method: {method}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Reset the maintenance application database.')
    parser.add_argument('--method', choices=['delete', 'truncate'], default='delete',
                      help='Method to reset the database: delete=remove file, truncate=drop all tables')
    parser.add_argument('--no-backup', action='store_true',
                      help='Skip creating a backup before resetting')
    parser.add_argument('--force', action='store_true',
                      help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    print("===== Database Reset Utility =====")
    
    # Check if we're on Render
    if os.environ.get('RENDER'):
        print("Running in Render environment")
    else:
        print("Running in local environment")
    
    # Get database path
    db_path = get_db_path()
    print(f"Database path: {db_path}")
    
    # Confirm action unless --force is used
    if not args.force:
        confirm = input(f"WARNING: This will reset the database at {db_path}. All data will be lost! Continue? (y/N): ")
        if confirm.lower() != 'y':
            print("Operation cancelled.")
            return
    
    # Create backup unless --no-backup is used
    if not args.no_backup:
        backup_path = backup_database(db_path)
        if backup_path:
            print(f"Database backed up to: {backup_path}")
    
    # Reset database
    success = reset_database(db_path, args.method)
    
    if success:
        print("\nDatabase reset successfully!")
        print("On next application launch, a new admin user will be created.")
    else:
        print("\nFailed to reset database. Check the error messages above.")

if __name__ == "__main__":
    main()
