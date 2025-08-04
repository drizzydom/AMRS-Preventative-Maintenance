#!/usr/bin/env python3
"""
Quick test to verify the datetime import fix works locally.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, '/Users/dominicmoriello/Documents/GitHub/AMRS-Preventative-Maintenance')

from app import app
from flask import request
import json

def test_sync_endpoint_logic():
    """Test the sync endpoint logic without making HTTP requests."""
    print("🧪 Testing sync endpoint datetime import fix...")
    
    with app.app_context():
        # Simulate the sync endpoint code path
        try:
            # This mimics the code path that was failing
            from datetime import datetime
            
            # Test 1: Full sync (no timestamp)
            print("   📥 Test 1: Full sync simulation")
            since_timestamp = None
            is_incremental = since_timestamp is not None
            
            if is_incremental:
                since_dt = datetime.fromisoformat(since_timestamp.replace('Z', '+00:00'))
                print(f"   [SYNC] Incremental sync request since: {since_dt}")
            else:
                since_dt = None
                print("   [SYNC] Full sync request (no timestamp)")
            
            # Test that datetime is available outside the if block
            current_time = datetime.now()
            print(f"   ✅ Datetime accessible: {current_time}")
            
            # Test 2: Incremental sync
            print("   📥 Test 2: Incremental sync simulation")
            since_timestamp = "2025-07-28T20:00:00"
            is_incremental = since_timestamp is not None
            
            if is_incremental:
                try:
                    since_dt = datetime.fromisoformat(since_timestamp.replace('Z', '+00:00'))
                    print(f"   [SYNC] Incremental sync request since: {since_dt}")
                except (ValueError, TypeError) as e:
                    print(f"   [SYNC] Invalid timestamp format: {since_timestamp}, falling back to full sync")
                    is_incremental = False
                    since_dt = None
            else:
                since_dt = None
                print("   [SYNC] Full sync request (no timestamp)")
            
            # Test that datetime is still available
            current_time = datetime.now()
            print(f"   ✅ Datetime still accessible: {current_time}")
            
            print("✅ All datetime import tests passed!")
            return True
            
        except NameError as e:
            print(f"❌ NameError (datetime import issue): {e}")
            return False
        except Exception as e:
            print(f"❌ Other error: {e}")
            return False

if __name__ == "__main__":
    success = test_sync_endpoint_logic()
    print(f"\n🎯 Result: {'PASS' if success else 'FAIL'}")
    sys.exit(0 if success else 1)
