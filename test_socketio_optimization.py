#!/usr/bin/env python3
"""
SocketIO Memory Optimization Test Suite
Tests the memory-optimized SocketIO implementation
"""

import requests
import json
import time
import threading
from datetime import datetime

def test_memory_monitoring():
    """Test the memory monitoring endpoint"""
    try:
        print("[TEST] Testing memory monitoring endpoint...")
        response = requests.get('http://localhost:10000/api/memory-status', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"[TEST] ✓ Memory Status Response:")
            print(f"  - Active SocketIO connections: {data.get('socketio', {}).get('active_connections', 'N/A')}")
            if 'memory' in data:
                print(f"  - Memory RSS: {data['memory']['rss_mb']} MB")
                print(f"  - Memory %: {data['memory']['percent']}%")
            print(f"  - Timestamp: {data.get('timestamp', 'N/A')}")
            return True
        else:
            print(f"[TEST] ✗ Memory monitoring failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[TEST] ✗ Memory monitoring error: {e}")
        return False

def test_socketio_connection():
    """Test SocketIO client connection simulation"""
    try:
        print("[TEST] Testing SocketIO connection simulation...")
        
        # Import socketio client
        import socketio
        
        # Create test client
        sio = socketio.Client()
        connected = False
        
        @sio.event
        def connect():
            nonlocal connected
            connected = True
            print("[TEST] ✓ SocketIO client connected")
        
        @sio.event
        def connected_event(data):
            print(f"[TEST] ✓ Server confirmation: {data}")
        
        @sio.event
        def disconnect():
            print("[TEST] SocketIO client disconnected")
        
        # Connect to server
        sio.connect('http://localhost:10000', transports=['websocket', 'polling'])
        
        # Wait for connection
        timeout = 10
        while not connected and timeout > 0:
            time.sleep(0.5)
            timeout -= 0.5
        
        if connected:
            print("[TEST] ✓ SocketIO connection successful")
            
            # Test sync event
            sio.emit('ping')
            time.sleep(1)
            
            # Disconnect
            sio.disconnect()
            print("[TEST] ✓ SocketIO disconnect successful")
            return True
        else:
            print("[TEST] ✗ SocketIO connection timeout")
            return False
            
    except Exception as e:
        print(f"[TEST] ✗ SocketIO connection error: {e}")
        return False

def test_sync_endpoint():
    """Test the sync data endpoint"""
    try:
        print("[TEST] Testing sync endpoint...")
        response = requests.get('http://localhost:10000/api/sync/data', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"[TEST] ✓ Sync endpoint responded with {len(data)} tables")
            return True
        else:
            print(f"[TEST] ✗ Sync endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[TEST] ✗ Sync endpoint error: {e}")
        return False

def run_memory_stress_test():
    """Run a brief memory stress test"""
    print("[TEST] Running memory stress test...")
    
    # Get initial memory
    initial_memory = test_memory_monitoring()
    
    # Create multiple connections
    connections = []
    try:
        import socketio
        
        for i in range(5):
            sio = socketio.Client()
            
            @sio.event
            def connect():
                pass
            
            sio.connect('http://localhost:10000', transports=['websocket'])
            connections.append(sio)
            time.sleep(0.5)
        
        print(f"[TEST] Created {len(connections)} test connections")
        
        # Check memory after connections
        test_memory_monitoring()
        
        # Disconnect all
        for sio in connections:
            sio.disconnect()
        
        # Wait for cleanup
        time.sleep(2)
        
        # Check memory after cleanup
        print("[TEST] After cleanup:")
        test_memory_monitoring()
        
        print("[TEST] ✓ Memory stress test completed")
        return True
        
    except Exception as e:
        print(f"[TEST] ✗ Memory stress test error: {e}")
        return False

def main():
    """Run all SocketIO optimization tests"""
    print("=" * 60)
    print("SOCKETIO MEMORY OPTIMIZATION TEST SUITE")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")
    print()
    
    tests = [
        ("Memory Monitoring", test_memory_monitoring),
        ("Sync Endpoint", test_sync_endpoint),
        ("SocketIO Connection", test_socketio_connection),
        ("Memory Stress Test", run_memory_stress_test),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        results[test_name] = test_func()
        print()
    
    print("=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:.<40} {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! SocketIO optimization is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
    
    print(f"Test completed at: {datetime.now()}")

if __name__ == "__main__":
    main()
