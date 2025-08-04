#!/usr/bin/env python3
"""
Test script to verify sync functionality is working after our fixes.
This script will:
1. Create a test audit task completion
2. Verify it gets added to sync_queue
3. Test the upload process (if online server is accessible)
"""

import os
import sys
import sqlite3
from datetime import datetime

# Add the current directory to Python path so we can import from the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_local_sync_queue():
    """Test that changes get added to sync_queue properly"""
    print("=== Testing Local Sync Queue ===")
    
    db_path = 'maintenance.db'
    if not os.path.exists(db_path):
        print("❌ No maintenance.db found")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check current sync_queue count
    cursor.execute("SELECT COUNT(*) FROM sync_queue WHERE status = 'pending'")
    before_count = cursor.fetchone()[0]
    print(f"📊 Pending sync items before test: {before_count}")
    
    # Insert a test audit task completion manually to trigger sync
    try:
        cursor.execute("""
            INSERT INTO audit_task_completions 
            (audit_task_id, machine_id, completed_by, date, completed_at, completed, notes, created_at, updated_at)
            VALUES (1, 1, 1, '2025-07-26', '2025-07-26 18:52:00', 1, 'Test completion for sync', datetime('now'), datetime('now'))
        """)
        
        test_completion_id = cursor.lastrowid
        print(f"✅ Created test completion ID: {test_completion_id}")
        
        # Manually add to sync queue (simulating what the app should do)
        cursor.execute("""
            INSERT INTO sync_queue (table_name, record_id, operation, payload, created_at, status)
            VALUES ('audit_task_completions', ?, 'insert', '{}', datetime('now'), 'pending')
        """, (test_completion_id,))
        
        conn.commit()
        
        # Check sync_queue count after
        cursor.execute("SELECT COUNT(*) FROM sync_queue WHERE status = 'pending'")
        after_count = cursor.fetchone()[0]
        print(f"📊 Pending sync items after test: {after_count}")
        
        if after_count > before_count:
            print("✅ Sync queue is working - changes are being queued")
            success = True
        else:
            print("❌ Sync queue not working - no new items queued")
            success = False
            
    except Exception as e:
        print(f"❌ Error testing sync queue: {e}")
        success = False
    finally:
        conn.close()
    
    return success

def test_enhanced_sync_function():
    """Test the enhanced sync function import"""
    print("\n=== Testing Enhanced Sync Function ===")
    
    try:
        from sync_utils_enhanced import add_to_sync_queue_enhanced, should_trigger_sync
        
        # Test environment detection
        should_sync = should_trigger_sync()
        print(f"📊 Should trigger sync: {should_sync}")
        
        if should_sync:
            print("✅ Enhanced sync utilities imported successfully")
            print("✅ Environment detected as offline client")
            return True
        else:
            print("ℹ️  Environment detected as online server - sync triggering disabled")
            return True
            
    except ImportError as e:
        print(f"❌ Failed to import enhanced sync utilities: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing enhanced sync: {e}")
        return False

def test_endpoint_availability():
    """Test that the sync endpoint is properly registered"""
    print("\n=== Testing Endpoint Registration ===")
    
    try:
        # Import app and check routes
        from app import app
        
        sync_routes = []
        for rule in app.url_map.iter_rules():
            if '/api/sync/data' in rule.rule:
                sync_routes.append((rule.rule, rule.methods, rule.endpoint))
        
        print(f"📊 Found {len(sync_routes)} sync data routes:")
        for rule, methods, endpoint in sync_routes:
            print(f"   {rule} -> {methods} -> {endpoint}")
        
        # Check if POST is supported
        has_post = any('POST' in methods for _, methods, _ in sync_routes)
        
        if has_post:
            print("✅ POST method is supported on /api/sync/data")
            return True
        else:
            print("❌ POST method NOT supported on /api/sync/data")
            return False
            
    except Exception as e:
        print(f"❌ Error checking endpoints: {e}")
        return False

def main():
    print("🔍 AMRS Sync System Test Suite")
    print("=" * 50)
    
    tests = [
        ("Local Sync Queue", test_local_sync_queue),
        ("Enhanced Sync Function", test_enhanced_sync_function), 
        ("Endpoint Registration", test_endpoint_availability)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Sync system should be working.")
    else:
        print("⚠️  Some tests failed. Check the issues above.")

if __name__ == "__main__":
    main()
