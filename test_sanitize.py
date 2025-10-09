#!/usr/bin/env python3
"""
Unit tests for sanitize_user_record function in models.py

Tests cover:
- Basic sanitization (password_hash removal)
- Decryption of username and email fields
- Edge cases (None values, missing fields, non-dict inputs)
- Error handling during decryption
"""

import sys
import os

# Add the project root to the path so we can import models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import sanitize_user_record, maybe_decrypt


def test_basic_password_removal():
    """Test that password_hash is always removed from sanitized records."""
    print("\n🧪 Test: Basic password_hash removal")
    
    # Test with password_hash present
    record = {
        'id': 1,
        'username': 'testuser',
        'email': 'test@example.com',
        'password_hash': 'secret_hash_value_12345'
    }
    
    result = sanitize_user_record(record)
    
    assert 'password_hash' not in result, "password_hash should be removed"
    assert result['id'] == 1, "Other fields should remain"
    assert result['username'] is not None, "username should still exist"
    assert result['email'] is not None, "email should still exist"
    
    print("✅ PASS: password_hash removed correctly")


def test_non_dict_input():
    """Test that non-dict inputs are returned unchanged."""
    print("\n🧪 Test: Non-dict input handling")
    
    # Test with None
    result = sanitize_user_record(None)
    assert result is None, "None should be returned as-is"
    
    # Test with string
    result = sanitize_user_record("not a dict")
    assert result == "not a dict", "String should be returned as-is"
    
    # Test with list
    result = sanitize_user_record([1, 2, 3])
    assert result == [1, 2, 3], "List should be returned as-is"
    
    print("✅ PASS: Non-dict inputs handled correctly")


def test_empty_dict():
    """Test sanitization of empty dict."""
    print("\n🧪 Test: Empty dict handling")
    
    record = {}
    result = sanitize_user_record(record)
    
    assert isinstance(result, dict), "Should return a dict"
    assert len(result) == 0, "Empty dict should remain empty"
    
    print("✅ PASS: Empty dict handled correctly")


def test_none_values_in_fields():
    """Test that None values in username/email don't cause errors."""
    print("\n🧪 Test: None values in fields")
    
    record = {
        'id': 1,
        'username': None,
        'email': None,
        'password_hash': 'should_be_removed'
    }
    
    result = sanitize_user_record(record)
    
    assert 'password_hash' not in result, "password_hash should be removed"
    assert result['username'] is None, "None username should remain None"
    assert result['email'] is None, "None email should remain None"
    
    print("✅ PASS: None values handled correctly")


def test_missing_fields():
    """Test that records with missing username/email/password_hash work fine."""
    print("\n🧪 Test: Missing fields")
    
    # No username or email
    record = {'id': 1, 'role': 'admin'}
    result = sanitize_user_record(record)
    assert result['id'] == 1, "id should be preserved"
    assert result['role'] == 'admin', "role should be preserved"
    
    # Only username
    record = {'username': 'testuser'}
    result = sanitize_user_record(record)
    assert 'username' in result, "username should be present"
    
    # Only email
    record = {'email': 'test@example.com'}
    result = sanitize_user_record(record)
    assert 'email' in result, "email should be present"
    
    print("✅ PASS: Missing fields handled correctly")


def test_decryption_attempt():
    """Test that maybe_decrypt is called on username and email."""
    print("\n🧪 Test: Decryption attempt on username/email")
    
    # Note: Since we don't have the actual encryption key in the test environment,
    # maybe_decrypt will likely just return the original value, but we verify
    # the function doesn't crash
    
    record = {
        'id': 1,
        'username': 'plaintext_user',
        'email': 'plaintext@example.com',
        'password_hash': 'secret'
    }
    
    result = sanitize_user_record(record)
    
    # The function should attempt decryption but not fail
    assert 'username' in result, "username should still exist"
    assert 'email' in result, "email should still exist"
    assert 'password_hash' not in result, "password_hash should be removed"
    
    # Values might be decrypted or remain plaintext depending on encryption state
    assert result['username'] is not None, "username should not be None"
    assert result['email'] is not None, "email should not be None"
    
    print("✅ PASS: Decryption attempt completed without errors")


def test_shallow_copy():
    """Test that sanitize_user_record returns a shallow copy, not the original."""
    print("\n🧪 Test: Shallow copy behavior")
    
    original = {
        'id': 1,
        'username': 'testuser',
        'password_hash': 'secret'
    }
    
    result = sanitize_user_record(original)
    
    # Modify the result
    result['id'] = 999
    
    # Original should be unchanged
    assert original['id'] == 1, "Original dict should not be modified"
    assert 'password_hash' in original, "Original password_hash should remain"
    assert 'password_hash' not in result, "Result should not have password_hash"
    
    print("✅ PASS: Shallow copy behavior correct")


def test_empty_string_fields():
    """Test handling of empty string values."""
    print("\n🧪 Test: Empty string fields")
    
    record = {
        'id': 1,
        'username': '',
        'email': '',
        'password_hash': 'secret'
    }
    
    result = sanitize_user_record(record)
    
    # Empty strings should be preserved (maybe_decrypt checks for truthy values)
    assert result['username'] == '', "Empty username should be preserved"
    assert result['email'] == '', "Empty email should be preserved"
    assert 'password_hash' not in result, "password_hash should be removed"
    
    print("✅ PASS: Empty string fields handled correctly")


def test_additional_fields_preserved():
    """Test that additional fields beyond username/email/password_hash are preserved."""
    print("\n🧪 Test: Additional fields preservation")
    
    record = {
        'id': 1,
        'username': 'testuser',
        'email': 'test@example.com',
        'password_hash': 'secret',
        'role': 'admin',
        'created_at': '2024-01-01',
        'is_active': True,
        'metadata': {'key': 'value'}
    }
    
    result = sanitize_user_record(record)
    
    assert result['id'] == 1, "id should be preserved"
    assert result['role'] == 'admin', "role should be preserved"
    assert result['created_at'] == '2024-01-01', "created_at should be preserved"
    assert result['is_active'] is True, "is_active should be preserved"
    assert result['metadata'] == {'key': 'value'}, "metadata should be preserved"
    assert 'password_hash' not in result, "password_hash should be removed"
    
    print("✅ PASS: Additional fields preserved correctly")


def run_all_tests():
    """Run all sanitizer tests."""
    print("=" * 60)
    print("🚀 Running sanitize_user_record test suite")
    print("=" * 60)
    
    tests = [
        test_basic_password_removal,
        test_non_dict_input,
        test_empty_dict,
        test_none_values_in_fields,
        test_missing_fields,
        test_decryption_attempt,
        test_shallow_copy,
        test_empty_string_fields,
        test_additional_fields_preserved,
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
