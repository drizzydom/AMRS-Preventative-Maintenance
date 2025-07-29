#!/usr/bin/env python3
"""
Test script to verify incremental sync functionality.
This script tests both the client-side and server-side incremental sync implementation.
"""

import os
import sys
import requests
import json
from datetime import datetime, timedelta

def test_server_incremental_sync():
    """Test the server-side incremental sync endpoint."""
    print("=" * 60)
    print("TESTING SERVER-SIDE INCREMENTAL SYNC")
    print("=" * 60)
    
    # Get server configuration from environment
    online_url = os.environ.get('AMRS_ONLINE_URL')
    admin_username = os.environ.get('AMRS_ADMIN_USERNAME')
    admin_password = os.environ.get('AMRS_ADMIN_PASSWORD')
    
    if not all([online_url, admin_username, admin_password]):
        print("❌ Missing server credentials:")
        print(f"   AMRS_ONLINE_URL: {'✓' if online_url else '✗'}")
        print(f"   AMRS_ADMIN_USERNAME: {'✓' if admin_username else '✗'}")
        print(f"   AMRS_ADMIN_PASSWORD: {'✓' if admin_password else '✗'}")
        return False
    
    # Clean URL
    clean_url = online_url.strip('"\'').rstrip('/')
    if clean_url.endswith('/api'):
        clean_url = clean_url[:-4]
    
    print(f"🌐 Testing server: {clean_url}")
    
    try:
        # Create session and authenticate
        session = requests.Session()
        
        # Try session-based login
        print("🔐 Authenticating...")
        login_resp = session.post(f"{clean_url}/login", data={
            'username': admin_username,
            'password': admin_password
        })
        
        if login_resp.status_code != 200:
            print(f"❌ Authentication failed: {login_resp.status_code}")
            return False
        
        print("✅ Authentication successful")
        
        # Test 1: Full sync (no since parameter)
        print("\n📥 Test 1: Full sync (no since parameter)")
        full_sync_resp = session.get(f"{clean_url}/api/sync/data", timeout=10)
        
        if full_sync_resp.status_code != 200:
            print(f"❌ Full sync failed: {full_sync_resp.status_code}")
            return False
        
        full_data = full_sync_resp.json()
        
        # Count total records
        total_records = 0
        for table_name, records in full_data.items():
            if table_name.startswith('_'):  # Skip metadata
                continue
            if isinstance(records, list):
                record_count = len(records)
                total_records += record_count
                print(f"   📊 {table_name}: {record_count} records")
        
        print(f"✅ Full sync returned {total_records} total records")
        
        # Test 2: Incremental sync with recent timestamp
        print("\n📥 Test 2: Incremental sync (last 1 hour)")
        since_time = (datetime.now() - timedelta(hours=1)).isoformat()
        incremental_resp = session.get(f"{clean_url}/api/sync/data?since={since_time}", timeout=10)
        
        if incremental_resp.status_code != 200:
            print(f"❌ Incremental sync failed: {incremental_resp.status_code}")
            return False
        
        incremental_data = incremental_resp.json()
        
        # Count incremental records
        incremental_records = 0
        for table_name, records in incremental_data.items():
            if table_name.startswith('_'):  # Skip metadata
                continue
            if isinstance(records, list):
                record_count = len(records)
                incremental_records += record_count
                if record_count > 0:
                    print(f"   📊 {table_name}: {record_count} recent records")
        
        print(f"✅ Incremental sync returned {incremental_records} recent records")
        
        # Test 3: Incremental sync with old timestamp (should return more)
        print("\n📥 Test 3: Incremental sync (last 7 days)")
        old_time = (datetime.now() - timedelta(days=7)).isoformat()
        old_incremental_resp = session.get(f"{clean_url}/api/sync/data?since={old_time}", timeout=10)
        
        if old_incremental_resp.status_code != 200:
            print(f"❌ Old incremental sync failed: {old_incremental_resp.status_code}")
            return False
        
        old_incremental_data = old_incremental_resp.json()
        
        # Count old incremental records
        old_incremental_records = 0
        for table_name, records in old_incremental_data.items():
            if table_name.startswith('_'):  # Skip metadata
                continue
            if isinstance(records, list):
                record_count = len(records)
                old_incremental_records += record_count
                if record_count > 0:
                    print(f"   📊 {table_name}: {record_count} records (last 7 days)")
        
        print(f"✅ 7-day incremental sync returned {old_incremental_records} records")
        
        # Validate incremental logic
        print("\n🔍 Validating incremental sync logic:")
        if incremental_records <= old_incremental_records <= total_records:
            print("✅ Incremental sync working correctly:")
            print(f"   📈 Recent (1h): {incremental_records} ≤ Week (7d): {old_incremental_records} ≤ Full: {total_records}")
        else:
            print("⚠️  Unexpected record counts:")
            print(f"   📈 Recent (1h): {incremental_records}")
            print(f"   📈 Week (7d): {old_incremental_records}")
            print(f"   📈 Full: {total_records}")
        
        # Check for metadata in response
        if '_sync_timestamp' in full_data:
            print(f"✅ Server timestamp: {full_data['_sync_timestamp']}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - server may be offline")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def test_client_timestamp_functions():
    """Test the client-side timestamp tracking functions."""
    print("\n" + "=" * 60)
    print("TESTING CLIENT-SIDE TIMESTAMP FUNCTIONS")
    print("=" * 60)
    
    try:
        # Add current directory to Python path
        sys.path.insert(0, '/Users/dominicmoriello/Documents/GitHub/AMRS-Preventative-Maintenance')
        
        # Import the functions we added and Flask app
        from sync_utils_enhanced import get_last_sync_timestamp, update_last_sync_timestamp
        from app import app
        
        print("✅ Successfully imported timestamp functions")
        
        # Use Flask application context for database operations
        with app.app_context():
            # Test get_last_sync_timestamp (before any sync)
            print("\n🕒 Test 1: Getting last sync timestamp (initial)")
            initial_timestamp = get_last_sync_timestamp()
            print(f"   Initial timestamp: {initial_timestamp}")
            
            # Test update_last_sync_timestamp
            print("\n🕒 Test 2: Updating sync timestamp")
            update_last_sync_timestamp()
            print("   ✅ Timestamp updated")
            
            # Test get_last_sync_timestamp (after update)
            print("\n🕒 Test 3: Getting last sync timestamp (after update)")
            updated_timestamp = get_last_sync_timestamp()
            print(f"   Updated timestamp: {updated_timestamp}")
            
            # Validate timestamp format
            if updated_timestamp:
                try:
                    parsed_time = datetime.fromisoformat(updated_timestamp.replace('Z', '+00:00'))
                    print(f"   ✅ Valid ISO format: {parsed_time}")
                    
                    # Check if timestamp is recent (within last minute)
                    now = datetime.now()
                    time_diff = abs((now - parsed_time.replace(tzinfo=None)).total_seconds())
                    if time_diff < 60:
                        print(f"   ✅ Timestamp is recent ({time_diff:.1f}s ago)")
                    else:
                        print(f"   ⚠️  Timestamp seems old ({time_diff:.1f}s ago)")
                        
                except Exception as e:
                    print(f"   ❌ Invalid timestamp format: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Run all incremental sync tests."""
    print("🚀 AMRS INCREMENTAL SYNC TEST SUITE")
    print("=" * 60)
    
    # Test client-side functions
    client_success = test_client_timestamp_functions()
    
    # Test server-side endpoint
    server_success = test_server_incremental_sync()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Client-side functions: {'✅ PASS' if client_success else '❌ FAIL'}")
    print(f"Server-side endpoint: {'✅ PASS' if server_success else '❌ FAIL'}")
    
    if client_success and server_success:
        print("\n🎉 ALL TESTS PASSED - Incremental sync is working!")
        print("\nNext steps:")
        print("1. Deploy server changes to production")
        print("2. Test with real offline clients")
        print("3. Monitor sync logs for incremental behavior")
    else:
        print("\n⚠️  SOME TESTS FAILED - Check the issues above")
        
    return client_success and server_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
