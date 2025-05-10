#!/usr/bin/env python3
"""
Debugging script for offline browser testing

This script helps diagnose issues with the offline mode browser testing.
It checks database connections, tables, and user authentication.
It also provides utilities for token-based authentication testing.
"""
import os
import sys
import logging
import json
import argparse
from pathlib import Path
import sqlite3
import traceback
import uuid
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Add token manager if available
try:
    from token_manager import TokenManager
    has_token_manager = True
except ImportError:
    has_token_manager = False

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
    parser = argparse.ArgumentParser(description='Debug offline browser and token authentication')
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Database check command
    db_parser = subparsers.add_parser('check', help='Check database and admin user')
    db_parser.add_argument('--db', type=str, default=os.environ.get('DB_FILE', 'maintenance_test.db'),
                          help='Database filename')
    
    # Fix admin user command
    fix_parser = subparsers.add_parser('fix', help='Fix admin user')
    fix_parser.add_argument('--db', type=str, default=os.environ.get('DB_FILE', 'maintenance_test.db'),
                           help='Database filename')
    
    # Token commands (only if token_manager is available)
    if has_token_manager:
        # Create token command
        create_token_parser = subparsers.add_parser('create-token', help='Create a test token')
        create_token_parser.add_argument('--user-id', type=int, required=True, help='User ID')
        create_token_parser.add_argument('--username', type=str, required=True, help='Username')
        create_token_parser.add_argument('--expiry', type=int, default=30, help='Token expiry in days')
        
        # Validate token command
        validate_token_parser = subparsers.add_parser('validate-token', help='Validate a token')
        validate_token_parser.add_argument('--token', type=str, required=True, help='Token to validate')
        
        # List tokens command
        list_parser = subparsers.add_parser('list-tokens', help='List all stored tokens')
        
        # Delete token command
        delete_parser = subparsers.add_parser('delete-token', help='Delete a stored token')
        delete_parser.add_argument('--user-id', type=int, required=True, help='User ID')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("AMRS Preventative Maintenance - Offline Browser Testing Debug")
    print("=" * 60)
    
    # Handle commands
    if not args.command or args.command == 'check':
        db_filename = args.db if hasattr(args, 'db') else os.environ.get('DB_FILE', 'maintenance_test.db')
        
        if check_database(db_filename):
            print("\n✅ Database is valid and admin user exists")
        else:
            print("\n❌ Database check failed")
            print("\nTo fix the database, run: python debug_offline_browser.py fix")
    
    elif args.command == 'fix':
        db_filename = args.db
        if fix_admin_user(db_filename):
            print("\n✅ Admin user fixed successfully")
            print("\nYou can now log in with the following credentials:")
            print("- Username: admin")
            print("- Password: admin")
        else:
            print("\n❌ Failed to fix admin user")
    
    # Token management commands (only if token_manager is available)
    elif has_token_manager and args.command == 'create-token':
        create_test_token(args.user_id, args.username, args.expiry)
    
    elif has_token_manager and args.command == 'validate-token':
        validate_token(args.token)
    
    elif has_token_manager and args.command == 'list-tokens':
        list_stored_tokens()
    
    elif has_token_manager and args.command == 'delete-token':
        delete_token(args.user_id)
    
    else:
        parser.print_help()
    
    if args.command in ['check', 'fix', None]:
        print("\nTo run the offline app for browser testing, use one of these commands:")
        print("- ./test_offline_browser.sh")
        print("- python run_offline_app_test.py")
        print("- RECREATE_DB=true python run_offline_app_test.py (to recreate the database)")
        
        if has_token_manager:
            print("\nToken management commands available:")
            print("- python debug_offline_browser.py create-token --user-id 1 --username admin")
            print("- python debug_offline_browser.py validate-token --token <token>")
            print("- python debug_offline_browser.py list-tokens")
            print("- python debug_offline_browser.py delete-token --user-id 1")

if __name__ == "__main__":
    main()
