#!/usr/bin/env python3
"""
Direct test for token functionality.
"""
import os
import sys

# Direct output to file for easier debugging
output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "token_test_output.log")

with open(output_file, "w") as f:
    f.write("Starting token direct test\n")
    
    try:
        f.write("Importing TokenManager...\n")
        from token_manager import TokenManager
        
        f.write("Creating token manager instance...\n")
        tm = TokenManager()
        
        f.write(f"Token expiry days: {tm.token_expiry_days}\n")
        
        f.write("Generating token...\n")
        token = tm.generate_token(1, "direct_test_user")
        
        f.write(f"Generated token (first 20 chars): {token[:20]}\n")
        
        f.write("Validating token...\n")
        payload = tm.validate_token(token)
        
        f.write(f"Validation result: {payload}\n")
        
        f.write("✅ DIRECT TOKEN TEST PASSED!\n")
        
    except Exception as e:
        f.write(f"❌ ERROR: {type(e).__name__}: {str(e)}\n")
        import traceback
        f.write(traceback.format_exc())

print(f"Test completed. Results written to {output_file}")
