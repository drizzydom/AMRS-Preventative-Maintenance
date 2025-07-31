#!/usr/bin/env python3
"""
Test script for bootstrap endpoint functionality.
This script tests the bootstrap endpoint to ensure it returns secrets correctly.
"""

import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_bootstrap_endpoint():
    """Test the bootstrap endpoint with the configured token."""
    
    bootstrap_url = os.environ.get('BOOTSTRAP_URL')
    bootstrap_token = os.environ.get('BOOTSTRAP_SECRET_TOKEN')
    
    if not bootstrap_url or not bootstrap_token:
        print("❌ Error: BOOTSTRAP_URL or BOOTSTRAP_SECRET_TOKEN not found in environment")
        print(f"BOOTSTRAP_URL: {'SET' if bootstrap_url else 'NOT SET'}")
        print(f"BOOTSTRAP_SECRET_TOKEN: {'SET' if bootstrap_token else 'NOT SET'}")
        return False
    
    print(f"🔄 Testing bootstrap endpoint: {bootstrap_url}")
    print(f"🔑 Using token: {bootstrap_token[:20]}..." if len(bootstrap_token) > 20 else bootstrap_token)
    
    try:
        headers = {"Authorization": f"Bearer {bootstrap_token}"}
        response = requests.post(bootstrap_url, headers=headers, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                secrets = response.json()
                print(f"✅ Success! Retrieved {len(secrets)} secrets:")
                for key, value in secrets.items():
                    status = "SET" if value else "NOT SET"
                    print(f"   • {key}: {status}")
                return True
            except json.JSONDecodeError as e:
                print(f"❌ Error: Invalid JSON response: {e}")
                print(f"Response text: {response.text}")
                return False
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response text: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Error: Request timed out")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Error: Connection failed")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_keyring_functionality():
    """Test keyring functionality for secret storage."""
    
    try:
        import keyring
        print("🔄 Testing keyring functionality...")
        
        # Test setting and getting a value
        test_service = "amrs-test"
        test_key = "test_key"
        test_value = "test_value_123"
        
        # Set value
        keyring.set_password(test_service, test_key, test_value)
        print("✅ Successfully stored test value in keyring")
        
        # Get value
        retrieved_value = keyring.get_password(test_service, test_key)
        if retrieved_value == test_value:
            print("✅ Successfully retrieved test value from keyring")
            
            # Clean up
            keyring.delete_password(test_service, test_key)
            print("✅ Successfully cleaned up test value from keyring")
            return True
        else:
            print(f"❌ Error: Retrieved value doesn't match. Expected: {test_value}, Got: {retrieved_value}")
            return False
            
    except ImportError:
        print("❌ Error: keyring package not installed")
        return False
    except Exception as e:
        print(f"❌ Error testing keyring: {e}")
        return False

def test_sync_script():
    """Test if sync_db.py script exists and can be imported."""
    
    print("🔄 Testing sync script availability...")
    
    if os.path.exists('sync_db.py'):
        print("✅ sync_db.py script found")
        return True
    else:
        print("❌ Error: sync_db.py script not found")
        return False

def main():
    """Run all bootstrap tests."""
    
    print("🚀 AMRS Bootstrap Functionality Test")
    print("=" * 50)
    
    tests = [
        ("Keyring Functionality", test_keyring_functionality),
        ("Sync Script Availability", test_sync_script), 
        ("Bootstrap Endpoint", test_bootstrap_endpoint),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        success = test_func()
        results.append((test_name, success))
        print(f"Result: {'✅ PASS' if success else '❌ FAIL'}")
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:10} {test_name}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Bootstrap system is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
