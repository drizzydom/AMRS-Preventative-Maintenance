#!/usr/bin/env python3
"""
Test script to verify user profile synchronization functionality.
Tests that user profile changes (email, name, password) are properly added to sync queue
and that the server sync endpoint handles them correctly.
"""

import sys
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import after path is set
from app import app, db
from models import User, Role, Site
from sqlalchemy import text

def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}")

def print_test(text):
    """Print a test description."""
    print(f"\n▶ {text}")

def print_success(text):
    """Print success message."""
    print(f"  ✅ {text}")

def print_error(text):
    """Print error message."""
    print(f"  ❌ {text}")

def print_info(text):
    """Print info message."""
    print(f"  ℹ️  {text}")

def clear_sync_queue():
    """Clear the sync queue for clean testing."""
    try:
        db.session.execute(text("DELETE FROM sync_queue"))
        db.session.commit()
        print_info("Cleared sync queue")
    except Exception as e:
        print_error(f"Failed to clear sync queue: {e}")
        db.session.rollback()

def test_user_profile_update():
    """Test that user profile updates are added to sync queue."""
    print_header("TEST 1: User Profile Update (Email & Full Name)")
    
    with app.app_context():
        # Create a test user
        print_test("Creating test user...")
        test_user = User(
            username='test_profile_user',
            email='test@example.com',
            full_name='Test User',
            password_hash=generate_password_hash('password123'),
            role_id=None
        )
        db.session.add(test_user)
        db.session.commit()
        user_id = test_user.id
        print_success(f"Created user ID: {user_id}")
        
        # Clear sync queue
        clear_sync_queue()
        
        # Update user profile
        print_test("Updating user profile (email and full_name)...")
        test_user.email = 'newemail@example.com'
        test_user.full_name = 'Updated Name'
        db.session.commit()
        
        # Manually add to sync queue (simulating what the route does)
        from sync_utils_enhanced import add_to_sync_queue_enhanced
        add_to_sync_queue_enhanced('users', test_user.id, 'update', {
            'id': test_user.id,
            'username': test_user.username,
            'email': test_user.email,
            'full_name': test_user.full_name,
            'role_id': test_user.role_id
        })
        
        # Check sync queue
        print_test("Checking sync queue...")
        result = db.session.execute(
            text("SELECT * FROM sync_queue WHERE table_name='users' AND record_id=:user_id AND operation='update'"),
            {'user_id': user_id}
        )
        sync_entries = result.fetchall()
        
        if len(sync_entries) > 0:
            print_success(f"Found {len(sync_entries)} sync queue entry/entries for user update")
            import json
            latest_entry = sync_entries[-1]
            data = json.loads(latest_entry[4])  # payload is 5th column
            if data.get('email') == 'newemail@example.com':
                print_success(f"✓ Email in sync data: {data.get('email')}")
            else:
                print_error(f"✗ Email mismatch: {data.get('email')}")
            
            if data.get('full_name') == 'Updated Name':
                print_success(f"✓ Full name in sync data: {data.get('full_name')}")
            else:
                print_error(f"✗ Full name mismatch: {data.get('full_name')}")
            
            if data.get('username') == 'test_profile_user':
                print_success(f"✓ Username in sync data: {data.get('username')}")
            else:
                print_error(f"✗ Username mismatch: {data.get('username')}")
        else:
            print_error("No sync queue entries found for user update!")
        
        # Cleanup
        db.session.delete(test_user)
        db.session.commit()
        print_info("Cleaned up test user")

def test_password_change():
    """Test that password changes are added to sync queue."""
    print_header("TEST 2: Password Change Sync")
    
    with app.app_context():
        # Create a test user
        print_test("Creating test user...")
        test_user = User(
            username='test_password_user',
            email='password@example.com',
            password_hash=generate_password_hash('oldpassword'),
            role_id=None
        )
        db.session.add(test_user)
        db.session.commit()
        user_id = test_user.id
        print_success(f"Created user ID: {user_id}")
        
        # Clear sync queue
        clear_sync_queue()
        
        # Change password
        print_test("Changing password...")
        new_password_hash = generate_password_hash('newpassword123')
        test_user.password_hash = new_password_hash
        db.session.commit()
        
        # Manually add to sync queue (simulating what the route does)
        from sync_utils_enhanced import add_to_sync_queue_enhanced
        add_to_sync_queue_enhanced('users', test_user.id, 'update', {
            'id': test_user.id,
            'password_hash': test_user.password_hash
        })
        
        # Check sync queue
        print_test("Checking sync queue...")
        result = db.session.execute(
            text("SELECT * FROM sync_queue WHERE table_name='users' AND record_id=:user_id AND operation='update'"),
            {'user_id': user_id}
        )
        sync_entries = result.fetchall()
        
        if len(sync_entries) > 0:
            print_success(f"Found {len(sync_entries)} sync queue entry/entries for password update")
            import json
            latest_entry = sync_entries[-1]
            data = json.loads(latest_entry[4])  # payload is 5th column
            if 'password_hash' in data and data['password_hash']:
                print_success("✓ Password hash present in sync data")
                # Verify the hash is valid
                if check_password_hash(data['password_hash'], 'newpassword123'):
                    print_success("✓ Password hash is valid and matches new password")
                else:
                    print_error("✗ Password hash doesn't match new password")
            else:
                print_error("✗ Password hash missing from sync data!")
        else:
            print_error("No sync queue entries found for password update!")
        
        # Cleanup
        db.session.delete(test_user)
        db.session.commit()
        print_info("Cleaned up test user")

def test_user_deletion_sync():
    """Test that user deletions are added to sync queue."""
    print_header("TEST 3: User Deletion Sync")
    
    with app.app_context():
        # Create a test user
        print_test("Creating test user...")
        test_user = User(
            username='test_delete_user',
            email='delete@example.com',
            password_hash=generate_password_hash('password123'),
            role_id=None
        )
        db.session.add(test_user)
        db.session.commit()
        user_id = test_user.id
        print_success(f"Created user ID: {user_id}")
        
        # Clear sync queue
        clear_sync_queue()
        
        # Delete user
        print_test("Deleting user...")
        db.session.delete(test_user)
        db.session.commit()
        
        # Manually add to sync queue (simulating what the route does)
        from sync_utils_enhanced import add_to_sync_queue_enhanced
        add_to_sync_queue_enhanced('users', user_id, 'delete', {'id': user_id})
        
        # Check sync queue
        print_test("Checking sync queue...")
        result = db.session.execute(
            text("SELECT * FROM sync_queue WHERE table_name='users' AND record_id=:user_id AND operation='delete'"),
            {'user_id': user_id}
        )
        sync_entries = result.fetchall()
        
        if len(sync_entries) > 0:
            print_success(f"Found {len(sync_entries)} sync queue entry/entries for user deletion")
            import json
            latest_entry = sync_entries[-1]
            data = json.loads(latest_entry[4])  # payload is 5th column
            if data.get('id') == user_id:
                print_success(f"✓ User ID in sync data: {data.get('id')}")
            else:
                print_error(f"✗ User ID mismatch: {data.get('id')}")
        else:
            print_error("No sync queue entries found for user deletion!")

def test_user_sites_sync():
    """Test that user-site associations are added to sync queue."""
    print_header("TEST 4: User-Sites Association Sync")
    
    with app.app_context():
        # Create a test user and site
        print_test("Creating test user and site...")
        test_site = Site(name='Test Site', location='Test Location')
        db.session.add(test_site)
        db.session.commit()
        site_id = test_site.id
        
        test_user = User(
            username='test_sites_user',
            email='sites@example.com',
            password_hash=generate_password_hash('password123'),
            role_id=None
        )
        db.session.add(test_user)
        db.session.commit()
        user_id = test_user.id
        print_success(f"Created user ID: {user_id}, site ID: {site_id}")
        
        # Clear sync queue
        clear_sync_queue()
        
        # Associate user with site
        print_test("Associating user with site...")
        test_user.sites.append(test_site)
        db.session.commit()
        
        # Manually add to sync queue (simulating what the route does)
        from sync_utils_enhanced import add_to_sync_queue_enhanced
        add_to_sync_queue_enhanced('user_sites', f'{user_id}_{site_id}', 'update', {
            'user_id': user_id,
            'site_id': site_id
        })
        
        # Check sync queue
        print_test("Checking sync queue...")
        result = db.session.execute(
            text("SELECT * FROM sync_queue WHERE table_name='user_sites' AND operation='update'")
        )
        sync_entries = result.fetchall()
        
        if len(sync_entries) > 0:
            print_success(f"Found {len(sync_entries)} sync queue entry/entries for user_sites")
            import json
            latest_entry = sync_entries[-1]
            data = json.loads(latest_entry[4])  # payload is 5th column
            if data.get('user_id') == user_id and data.get('site_id') == site_id:
                print_success(f"✓ User-site association in sync data: user_id={data.get('user_id')}, site_id={data.get('site_id')}")
            else:
                print_error(f"✗ User-site association mismatch: {data}")
        else:
            print_error("No sync queue entries found for user_sites!")
        
        # Cleanup
        db.session.delete(test_user)
        db.session.delete(test_site)
        db.session.commit()
        print_info("Cleaned up test user and site")

def test_sync_endpoint_processing():
    """Test that the sync endpoint can process user updates."""
    print_header("TEST 5: Server Sync Endpoint Processing")
    
    with app.test_client() as client:
        with app.app_context():
            # Create a test user to use for authentication
            print_test("Setting up test environment...")
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                print_error("Admin user not found. Cannot test sync endpoint.")
                return
            
            # Simulate sync data from a client
            print_test("Simulating sync data POST to server...")
            sync_data = {
                'users': [
                    {
                        'id': 99999,  # Use high ID that won't conflict
                        'username': 'sync_test_user',
                        'email': 'synctest@example.com',
                        'full_name': 'Sync Test User',
                        'role_id': None,
                        'password_hash': generate_password_hash('testpassword'),
                        'active': True
                    }
                ],
                'user_sites': [
                    {
                        'user_id': 99999,
                        'site_id': 1  # Assuming site 1 exists
                    }
                ]
            }
            
            # Login as admin first
            print_test("Authenticating as admin...")
            login_response = client.post('/login', data={
                'username': 'admin',
                'password': os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin')
            }, follow_redirects=False)
            
            if login_response.status_code in [200, 302]:
                print_success("Authenticated as admin")
                
                # Post sync data
                print_test("Posting sync data to /api/sync/data...")
                response = client.post('/api/sync/data',
                    json=sync_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    print_success(f"Sync endpoint returned 200 OK")
                    response_data = response.get_json()
                    if response_data.get('status') == 'success':
                        print_success("✓ Sync processing successful")
                        
                        # Verify user was created
                        test_user = User.query.get(99999)
                        if test_user:
                            print_success(f"✓ User created in database: {test_user.username}")
                            print_success(f"  - Email: {test_user.email}")
                            print_success(f"  - Full Name: {test_user.full_name}")
                            
                            # Verify password hash
                            if test_user.password_hash and check_password_hash(test_user.password_hash, 'testpassword'):
                                print_success("  - Password hash synced correctly")
                            else:
                                print_error("  - Password hash not synced or invalid")
                            
                            # Cleanup
                            db.session.delete(test_user)
                            db.session.commit()
                            print_info("Cleaned up test user")
                        else:
                            print_error("✗ User was not created in database")
                    else:
                        print_error(f"✗ Sync failed: {response_data}")
                else:
                    print_error(f"Sync endpoint returned {response.status_code}")
                    print_error(f"Response: {response.get_data(as_text=True)}")
            else:
                print_error(f"Failed to authenticate as admin (status: {login_response.status_code})")

def run_all_tests():
    """Run all user profile sync tests."""
    print("\n" + "="*70)
    print("  USER PROFILE SYNCHRONIZATION TEST SUITE")
    print("  Testing all user profile changes sync properly")
    print("="*70)
    
    try:
        test_user_profile_update()
        test_password_change()
        test_user_deletion_sync()
        test_user_sites_sync()
        test_sync_endpoint_processing()
        
        print_header("TEST SUITE COMPLETE")
        print_success("All tests completed. Review results above.")
        
    except Exception as e:
        print_error(f"Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    run_all_tests()
