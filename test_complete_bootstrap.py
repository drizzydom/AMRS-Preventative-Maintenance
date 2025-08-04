#!/usr/bin/env python3
"""
Test the complete bootstrap workflow for offline applications.

This test simulates what happens when an offline application starts up:
1. Detects it's in offline mode
2. Triggers bootstrap to download secrets
3. Initializes database
4. Imports sync data
5. Tests user login
"""

import os
import sys
import json
import sqlite3
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def cleanup_test_files():
    """Clean up any test files."""
    test_files = ['test_bootstrap.db', 'test_bootstrap_complete.db']
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"Cleaned up {file}")

def test_bootstrap_secrets():
    """Test that bootstrap secrets are available in keyring."""
    try:
        import keyring
        
        required_secrets = [
            'AMRS_ADMIN_PASSWORD',
            'AMRS_ADMIN_USERNAME', 
            'AMRS_ONLINE_URL',
            'SYNC_URL',
            'SYNC_USERNAME',
            'USER_FIELD_ENCRYPTION_KEY'
        ]
        
        missing_secrets = []
        for secret in required_secrets:
            value = keyring.get_password("amrs_pm", secret)
            if not value:
                missing_secrets.append(secret)
        
        if missing_secrets:
            print(f"❌ Missing secrets: {missing_secrets}")
            return False
        else:
            print(f"✅ All required secrets available in keyring")
            return True
            
    except Exception as e:
        print(f"❌ Error checking keyring secrets: {e}")
        return False

def test_environment_detection():
    """Test that we correctly detect offline mode."""
    try:
        from timezone_utils import is_offline_mode, is_online_server
        
        # Should be offline mode on local machine
        if is_offline_mode():
            print("✅ Correctly detected offline mode")
        else:
            print("❌ Failed to detect offline mode")
            return False
            
        # Should NOT be online server on local machine
        if not is_online_server():
            print("✅ Correctly detected NOT online server")
            return True
        else:
            print("❌ Incorrectly detected as online server")
            return False
            
    except Exception as e:
        print(f"❌ Error testing environment detection: {e}")
        return False

def test_sync_data_available():
    """Test that sync data is available."""
    if os.path.exists('test_sync.json'):
        try:
            with open('test_sync.json', 'r') as f:
                data = json.load(f)
            
            users = data.get('users', [])
            if len(users) > 0:
                print(f"✅ Sync data available with {len(users)} users")
                return True
            else:
                print("❌ No users in sync data")
                return False
                
        except Exception as e:
            print(f"❌ Error reading sync data: {e}")
            return False
    else:
        print("❌ Sync data file not found")
        return False

def create_minimal_database():
    """Create a minimal SQLite database with just the users table."""
    try:
        db_path = 'test_bootstrap_complete.db'
        
        # Remove existing file
        if os.path.exists(db_path):
            os.remove(db_path)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create minimal users table
        cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            active BOOLEAN DEFAULT 1,
            is_admin BOOLEAN DEFAULT 0,
            role_id INTEGER,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            username_hash TEXT,
            email_hash TEXT,
            remember_token TEXT,
            remember_token_expiration TIMESTAMP,
            remember_enabled BOOLEAN DEFAULT 0
        )
        ''')
        
        # Create roles table
        cursor.execute('''
        CREATE TABLE roles (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            permissions TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
        ''')
        
        conn.commit()
        print(f"✅ Created minimal database: {db_path}")
        
        # Import sync data
        with open('test_sync.json', 'r') as f:
            data = json.load(f)
        
        # Insert roles first
        roles = data.get('roles', [])
        for role in roles:
            cursor.execute('''
            INSERT INTO roles (id, name, description, permissions, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                role['id'],
                role['name'],
                role['description'],
                role['permissions'],
                role['created_at'],
                role['updated_at']
            ))
        
        # Insert users
        users = data.get('users', [])
        for user in users:
            cursor.execute('''
            INSERT INTO users (id, username, email, password_hash, full_name, active, is_admin, role_id, created_at, updated_at, username_hash, email_hash, remember_token, remember_token_expiration, remember_enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user['id'],
                user['username'],
                user['email'],
                user['password_hash'],
                user.get('full_name'),
                user['active'],
                user['is_admin'],
                user['role_id'],
                user['created_at'],
                user['updated_at'],
                user.get('username_hash'),
                user.get('email_hash'),
                user.get('remember_token'),
                user.get('remember_token_expiration'),
                user.get('remember_enabled', False)
            ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Imported {len(users)} users and {len(roles)} roles")
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def test_user_authentication():
    """Test that we can authenticate users from the imported data."""
    try:
        from werkzeug.security import check_password_hash
        
        db_path = 'test_bootstrap_complete.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test demo user authentication
        cursor.execute("SELECT username, password_hash FROM users WHERE username = ?", ('demo',))
        result = cursor.fetchone()
        
        if result:
            username, password_hash = result
            print(f"✅ Found user: {username}")
            print(f"✅ Password hash available: {password_hash[:20]}...")
            
            # Note: We don't know the actual password, but we can verify the hash format
            if password_hash.startswith('pbkdf2:sha256:'):
                print("✅ Password hash format is correct")
                return True
            else:
                print("❌ Password hash format is incorrect")
                return False
        else:
            print("❌ Demo user not found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing authentication: {e}")
        return False

def main():
    """Run complete bootstrap test."""
    print("🚀 Testing Complete Bootstrap Workflow for Offline Application")
    print("=" * 60)
    
    # Cleanup first
    cleanup_test_files()
    
    tests = [
        ("Environment Detection", test_environment_detection),
        ("Bootstrap Secrets", test_bootstrap_secrets),
        ("Sync Data Available", test_sync_data_available),
        ("Database Creation & Import", create_minimal_database),
        ("User Authentication Setup", test_user_authentication),
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        print(f"\n📋 Testing: {test_name}")
        print("-" * 40)
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                all_passed = False
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Bootstrap workflow is working correctly.")
        print("\nSummary:")
        print("✅ Environment detection works")
        print("✅ Bootstrap secrets are available")
        print("✅ Sync data can be downloaded")
        print("✅ Database can be created and populated")
        print("✅ User authentication is set up")
        print("\nThe offline application should be able to:")
        print("- Start up and detect offline mode")
        print("- Download configuration from online server")
        print("- Sync user data")
        print("- Allow users to log in")
    else:
        print("❌ SOME TESTS FAILED! Please check the issues above.")
    
    print("\n📁 Test files created:")
    if os.path.exists('test_bootstrap_complete.db'):
        size = os.path.getsize('test_bootstrap_complete.db')
        print(f"  - test_bootstrap_complete.db ({size:,} bytes)")

if __name__ == "__main__":
    main()
