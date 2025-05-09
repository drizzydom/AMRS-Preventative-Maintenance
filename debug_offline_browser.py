#!/usr/bin/env python3
"""
Debugging script for offline browser testing

This script helps diagnose issues with the offline mode browser testing.
It checks database connections, tables, and user authentication.
"""
import os
import sys
import logging
from pathlib import Path
import sqlite3
import traceback
from werkzeug.security import generate_password_hash

# Set up logging
logging.basicConfig(level=logging.INFO, format='[DEBUG] %(levelname)s - %(message)s')
logger = logging.getLogger("debug_offline_browser")

def check_database(db_filename="maintenance_test.db"):
    """Check if the database exists and is valid"""
    logger.info(f"Checking database: {db_filename}")
    
    # Determine database path
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    db_path = os.path.join(instance_dir, db_filename)
    
    # Check if the directory exists
    if not os.path.exists(instance_dir):
        logger.error(f"Instance directory doesn't exist: {instance_dir}")
        try:
            os.makedirs(instance_dir, exist_ok=True)
            logger.info(f"Created instance directory: {instance_dir}")
        except Exception as e:
            logger.error(f"Failed to create instance directory: {e}")
            return False
    
    # Check if the database exists
    if not os.path.exists(db_path):
        logger.error(f"Database file doesn't exist: {db_path}")
        return False
    
    # Check if it's a valid SQLite database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        if result and result[0] == 'ok':
            logger.info("Database integrity check passed")
        else:
            logger.error(f"Database integrity check failed: {result}")
            return False
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        logger.info(f"Tables in database: {', '.join([t[0] for t in tables])}")
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            logger.error("Users table doesn't exist")
            return False
        
        # Check for admin user
        try:
            cursor.execute("SELECT id, username, password_hash FROM users WHERE username='admin'")
            admin_user = cursor.fetchone()
            if not admin_user:
                logger.error("Admin user doesn't exist")
                return False
            else:
                logger.info(f"Admin user exists (ID: {admin_user[0]})")
        except sqlite3.OperationalError as e:
            logger.error(f"Error querying users table: {e}")
            return False
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Failed to open database: {e}")
        logger.error(traceback.format_exc())
        return False

def fix_admin_user(db_filename="maintenance_test.db"):
    """Fix or recreate the admin user"""
    logger.info(f"Fixing admin user in database: {db_filename}")
    
    # Determine database path
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    db_path = os.path.join(instance_dir, db_filename)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if roles table exists and has admin role
        cursor.execute("SELECT id FROM roles WHERE name='admin'")
        admin_role = cursor.fetchone()
        
        admin_role_id = None
        if admin_role:
            admin_role_id = admin_role[0]
        else:
            cursor.execute(
                "INSERT INTO roles (name, description, permissions) VALUES (?, ?, ?)",
                ('admin', 'Administrator', 'admin.full')
            )
            admin_role_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Created admin role with ID: {admin_role_id}")
        
        # Check if admin user exists
        cursor.execute("SELECT id FROM users WHERE username='admin'")
        admin_user = cursor.fetchone()
        
        if admin_user:
            # Update admin user
            cursor.execute(
                "UPDATE users SET password_hash=?, is_admin=1, role_id=? WHERE username='admin'",
                (generate_password_hash('admin'), admin_role_id)
            )
            logger.info(f"Updated admin user (ID: {admin_user[0]})")
        else:
            # Create admin user
            import uuid
            username_hash = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'admin'))
            email_hash = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'admin@example.com'))
            
            cursor.execute('''
                INSERT INTO users (
                    username, username_hash, email, email_hash, full_name, 
                    password_hash, is_admin, role_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (
                'admin', username_hash, 'admin@example.com', email_hash, 'Administrator',
                generate_password_hash('admin'), 1, admin_role_id
            ))
            admin_id = cursor.lastrowid
            logger.info(f"Created admin user with ID: {admin_id}")
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Failed to fix admin user: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """Main entry point for the debugging script"""
    print("=" * 60)
    print("AMRS Preventative Maintenance - Offline Browser Testing Debug")
    print("=" * 60)
    
    # Get database filename from command line or environment variable
    db_filename = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('DB_FILE', 'maintenance_test.db')
    
    if check_database(db_filename):
        print("\n✅ Database is valid and admin user exists")
    else:
        print("\n❌ Database check failed")
        
        # Ask user if they want to fix the database
        response = input("\nWould you like to fix the admin user? (y/n): ")
        if response.lower() == 'y':
            if fix_admin_user(db_filename):
                print("\n✅ Admin user fixed successfully")
                print("\nYou can now log in with the following credentials:")
                print("- Username: admin")
                print("- Password: admin")
            else:
                print("\n❌ Failed to fix admin user")
    
    print("\nTo run the offline app for browser testing, use one of these commands:")
    print("- ./test_offline_browser.sh")
    print("- python run_offline_app_test.py")
    print("- RECREATE_DB=true python run_offline_app_test.py (to recreate the database)")

if __name__ == "__main__":
    main()
