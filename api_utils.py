#!/usr/bin/env python3
"""
API utilities for safely handling user data in responses.

This module provides helper functions to ensure sensitive user data
(password hashes, encrypted fields) are never accidentally exposed
in API responses, logs, or templates.

SECURITY ARCHITECTURE:
- All API endpoints that return user data MUST use prepare_user_for_response()
  or prepare_users_list_for_response() to sanitize output.
- The sanitizer removes password_hash and decrypts username/email fields.
- EXCEPTION: /api/sync/data endpoint intentionally includes password_hash for
  offline authentication. This is the ONLY endpoint allowed to expose password_hash,
  and it is gated by check_sync_auth() requiring admin or sync service permissions.
- Template routes passing ORM User objects are safe because the model's property
  getters handle decryption, and templates should never access password_hash directly.

Usage:
    # In API endpoints
    from api_utils import prepare_user_for_response
    user = User.query.get(1)
    return jsonify(prepare_user_for_response(user, include_fields=['id', 'username', 'email']))
"""

from models import sanitize_user_record

# =============================================================================
# LOGGING REDACTION HELPERS
# =============================================================================

# Sensitive keys that should NEVER be logged in plaintext
SENSITIVE_KEYS = [
    'password',
    'password_hash',
    'api_key',
    'secret_key',
    'access_token',
    'refresh_token',
    'token',
    'key',
    'secret',
    'auth',
    'authorization',
]

def redact_dict_for_logging(data, sensitive_keys=None):
    """
    Redact sensitive fields from a dict before logging.
    
    Args:
        data: Dictionary to redact (will not be modified).
        sensitive_keys: Optional list of keys to redact. If None, uses SENSITIVE_KEYS.
    
    Returns:
        New dict with sensitive values replaced by '<REDACTED>'.
    """
    if not isinstance(data, dict):
        return data
    
    keys_to_redact = sensitive_keys or SENSITIVE_KEYS
    redacted = {}
    
    for key, value in data.items():
        key_lower = str(key).lower()
        # Check if key name contains any sensitive pattern
        if any(sensitive in key_lower for sensitive in keys_to_redact):
            redacted[key] = '<REDACTED>'
        elif isinstance(value, str) and len(value) > 500:
            # Truncate very long strings to prevent log bloat
            redacted[key] = f'<TRUNCATED:{len(value)} chars>'
        else:
            redacted[key] = value
    
    return redacted

# =============================================================================
# API RESPONSE SANITIZATION
# =============================================================================


def prepare_user_for_response(user, include_fields=None):
    """
    Prepare a user object for safe inclusion in API responses or templates.
    
    This function:
    1. Converts ORM User objects to dicts if needed
    2. Applies sanitize_user_record to remove password_hash and decrypt username/email
    3. Optionally filters to include only specified fields
    
    Args:
        user: A User ORM object, dict, or SQLite Row object
        include_fields: Optional list of field names to include in output.
                       If None, includes all sanitized fields.
                       Common fields: ['id', 'username', 'email', 'full_name', 'is_admin', 'role_id']
    
    Returns:
        A sanitized dict safe for JSON serialization or template rendering.
        Returns None if user is None.
    
    Examples:
        # With ORM object
        user = User.query.get(1)
        safe_user = prepare_user_for_response(user, include_fields=['id', 'username', 'email'])
        return jsonify(safe_user)
        
        # With dict from raw SQL
        cursor.execute('SELECT * FROM users WHERE id = ?', (1,))
        user_dict = dict(cursor.fetchone())
        safe_user = prepare_user_for_response(user_dict)
        return jsonify(safe_user)
    """
    if user is None:
        return None
    
    # Convert to dict if it's an ORM object or SQLite Row
    if hasattr(user, '__dict__') and hasattr(user, '_sa_instance_state'):
        # SQLAlchemy ORM object
        user_dict = {
            'id': user.id,
            'username': user.username,  # Property getter handles decryption
            'email': user.email,  # Property getter handles decryption
            'full_name': user.full_name,
            'role_id': user.role_id,
            'is_admin': user.is_admin,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
        }
    elif hasattr(user, 'keys'):
        # Dict-like object (dict or SQLite Row)
        user_dict = dict(user)
    else:
        # Unknown type, return empty dict
        return {}
    
    # Apply sanitizer to ensure password_hash is removed and fields are decrypted
    sanitized = sanitize_user_record(user_dict)
    
    # Filter to include only requested fields if specified
    if include_fields:
        sanitized = {k: v for k, v in sanitized.items() if k in include_fields}
    
    return sanitized


def prepare_users_list_for_response(users, include_fields=None):
    """
    Prepare a list of user objects for safe inclusion in API responses.
    
    Args:
        users: List of User ORM objects, dicts, or SQLite Row objects
        include_fields: Optional list of field names to include in each user dict
    
    Returns:
        List of sanitized user dicts safe for JSON serialization.
    
    Example:
        users = User.query.all()
        safe_users = prepare_users_list_for_response(users, include_fields=['id', 'username'])
        return jsonify({'users': safe_users})
    """
    if not users:
        return []
    
    return [prepare_user_for_response(user, include_fields) for user in users]


def sanitize_response_dict(data, sensitive_keys=None):
    """
    Remove sensitive keys from a response dict to prevent accidental exposure.
    
    Args:
        data: Dict to sanitize
        sensitive_keys: List of key names to remove. If None, uses default list.
    
    Returns:
        Sanitized copy of the dict with sensitive keys removed.
    
    Default sensitive keys:
        - password_hash
        - password
        - _password
        - password_reset_token
        - api_key
        - secret_key
        - access_token
        - refresh_token
    
    Example:
        response = {'id': 1, 'username': 'test', 'password_hash': 'secret'}
        safe_response = sanitize_response_dict(response)
        # Returns: {'id': 1, 'username': 'test'}
    """
    if data is None:
        return None
    
    if sensitive_keys is None:
        sensitive_keys = [
            'password_hash',
            'password',
            '_password',
            'password_reset_token',
            'api_key',
            'secret_key',
            'access_token',
            'refresh_token',
        ]
    
    # Create a shallow copy
    sanitized = data.copy() if isinstance(data, dict) else data
    
    if isinstance(sanitized, dict):
        # Remove sensitive keys
        for key in sensitive_keys:
            sanitized.pop(key, None)
    
    return sanitized


def safe_jsonify_user(user, status_code=200, include_fields=None):
    """
    Convenience function to jsonify a user object safely.
    
    Args:
        user: User object to jsonify
        status_code: HTTP status code (default 200)
        include_fields: Optional list of fields to include
    
    Returns:
        Flask jsonify response with sanitized user data
    
    Example:
        user = User.query.get(1)
        return safe_jsonify_user(user, include_fields=['id', 'username', 'email'])
    """
    from flask import jsonify
    
    safe_user = prepare_user_for_response(user, include_fields)
    return jsonify(safe_user), status_code


def safe_jsonify_users(users, status_code=200, include_fields=None):
    """
    Convenience function to jsonify a list of user objects safely.
    
    Args:
        users: List of user objects to jsonify
        status_code: HTTP status code (default 200)
        include_fields: Optional list of fields to include in each user
    
    Returns:
        Flask jsonify response with sanitized users list
    
    Example:
        users = User.query.all()
        return safe_jsonify_users(users, include_fields=['id', 'username'])
    """
    from flask import jsonify
    
    safe_users = prepare_users_list_for_response(users, include_fields)
    return jsonify({'users': safe_users}), status_code
