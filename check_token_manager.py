#!/usr/bin/env python3
"""
Simple test to verify the TokenManager is importable
"""
try:
    from token_manager import TokenManager
    tm = TokenManager()
    print("✅ TokenManager imported successfully")
    print(f"Token expiry days: {tm.token_expiry_days}")
    print(f"Token directory: {tm.token_dir}")
    
    # Try to generate a token
    token = tm.generate_token(1, "test_user")
    print(f"Generated token: {token[:20]}...")
    
    # Try to validate the token
    payload = tm.validate_token(token)
    print(f"Validated token payload: {payload}")

except Exception as e:
    print(f"❌ Error importing or using TokenManager: {e}")
