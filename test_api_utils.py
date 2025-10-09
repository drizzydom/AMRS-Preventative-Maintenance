#!/usr/bin/env python3
"""
Unit tests for api_utils.py helpers

Tests cover:
- prepare_user_for_response with ORM objects and dicts
- prepare_users_list_for_response
- sanitize_response_dict
- Field filtering with include_fields parameter
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api_utils import (
    prepare_user_for_response,
    prepare_users_list_for_response,
    sanitize_response_dict
)


def test_prepare_user_dict():
    """Test preparing a user dict for response."""
    print("\n🧪 Test: Prepare user dict with password_hash")
    
    user_dict = {
        'id': 1,
        'username': 'testuser',
        'email': 'test@example.com',
        'password_hash': 'secret_hash_should_be_removed',
        'full_name': 'Test User',
        'role_id': 1,
        'is_admin': False
    }
    
    result = prepare_user_for_response(user_dict)
    
    assert 'password_hash' not in result, "password_hash should be removed"
    assert result['username'] == 'testuser', "username should be present"
    assert result['email'] == 'test@example.com', "email should be present"
    assert result['id'] == 1, "id should be preserved"
    
    print("✅ PASS: User dict sanitized correctly")


def test_prepare_user_with_field_filtering():
    """Test preparing a user with field filtering."""
    print("\n🧪 Test: Prepare user with include_fields")
    
    user_dict = {
        'id': 1,
        'username': 'testuser',
        'email': 'test@example.com',
        'password_hash': 'secret',
        'full_name': 'Test User',
        'role_id': 1,
        'is_admin': False
    }
    
    result = prepare_user_for_response(user_dict, include_fields=['id', 'username'])
    
    assert 'id' in result, "id should be included"
    assert 'username' in result, "username should be included"
    assert 'email' not in result, "email should be filtered out"
    assert 'password_hash' not in result, "password_hash should be removed"
    assert 'full_name' not in result, "full_name should be filtered out"
    
    print("✅ PASS: Field filtering works correctly")


def test_prepare_users_list():
    """Test preparing a list of users."""
    print("\n🧪 Test: Prepare users list")
    
    users = [
        {'id': 1, 'username': 'user1', 'email': 'user1@example.com', 'password_hash': 'secret1'},
        {'id': 2, 'username': 'user2', 'email': 'user2@example.com', 'password_hash': 'secret2'},
        {'id': 3, 'username': 'user3', 'email': 'user3@example.com', 'password_hash': 'secret3'},
    ]
    
    result = prepare_users_list_for_response(users, include_fields=['id', 'username'])
    
    assert len(result) == 3, "Should return 3 users"
    for user in result:
        assert 'password_hash' not in user, "password_hash should be removed from all users"
        assert 'id' in user, "id should be present"
        assert 'username' in user, "username should be present"
        assert 'email' not in user, "email should be filtered out"
    
    print("✅ PASS: Users list sanitized correctly")


def test_prepare_user_none():
    """Test preparing None user."""
    print("\n🧪 Test: Prepare None user")
    
    result = prepare_user_for_response(None)
    
    assert result is None, "None should return None"
    
    print("✅ PASS: None handled correctly")


def test_sanitize_response_dict():
    """Test sanitizing a generic response dict."""
    print("\n🧪 Test: Sanitize response dict")
    
    response = {
        'id': 1,
        'username': 'testuser',
        'password': 'plain_password',
        'password_hash': 'hashed_password',
        'api_key': 'secret_key',
        'data': 'public_data'
    }
    
    result = sanitize_response_dict(response)
    
    assert 'password' not in result, "password should be removed"
    assert 'password_hash' not in result, "password_hash should be removed"
    assert 'api_key' not in result, "api_key should be removed"
    assert result['username'] == 'testuser', "username should be preserved"
    assert result['data'] == 'public_data', "data should be preserved"
    
    print("✅ PASS: Response dict sanitized correctly")


def test_sanitize_custom_sensitive_keys():
    """Test sanitizing with custom sensitive keys."""
    print("\n🧪 Test: Sanitize with custom sensitive keys")
    
    response = {
        'id': 1,
        'username': 'testuser',
        'internal_token': 'should_be_removed',
        'public_data': 'keep_this'
    }
    
    result = sanitize_response_dict(response, sensitive_keys=['internal_token'])
    
    assert 'internal_token' not in result, "custom sensitive key should be removed"
    assert result['username'] == 'testuser', "username should be preserved"
    assert result['public_data'] == 'keep_this', "public data should be preserved"
    
    print("✅ PASS: Custom sensitive keys handled correctly")


def test_empty_users_list():
    """Test preparing empty users list."""
    print("\n🧪 Test: Prepare empty users list")
    
    result = prepare_users_list_for_response([])
    
    assert result == [], "Empty list should return empty list"
    
    print("✅ PASS: Empty users list handled correctly")


def run_all_tests():
    """Run all API utils tests."""
    print("=" * 60)
    print("🚀 Running api_utils test suite")
    print("=" * 60)
    
    tests = [
        test_prepare_user_dict,
        test_prepare_user_with_field_filtering,
        test_prepare_users_list,
        test_prepare_user_none,
        test_sanitize_response_dict,
        test_sanitize_custom_sensitive_keys,
        test_empty_users_list,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {test.__name__}")
            print(f"   Error: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR in {test.__name__}: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed out of {len(tests)} total")
    print("=" * 60)
    
    if failed == 0:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
