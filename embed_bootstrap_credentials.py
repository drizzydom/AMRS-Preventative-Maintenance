#!/usr/bin/env python3
"""
Embed bootstrap credentials for Windows offline application builds.
This script should be run before building to embed necessary credentials.
"""

import os
import base64
import json
import sys
from pathlib import Path

def embed_credentials():
    """Embed bootstrap credentials as encoded data in a Python file."""
    
    # Required credentials for bootstrap
    required_credentials = {
        'AMRS_ADMIN_USERNAME': os.getenv('AMRS_ADMIN_USERNAME'),
        'AMRS_ADMIN_PASSWORD': os.getenv('AMRS_ADMIN_PASSWORD'), 
        'USER_FIELD_ENCRYPTION_KEY': os.getenv('USER_FIELD_ENCRYPTION_KEY'),
        'SYNC_URL': os.getenv('SYNC_URL'),
        'SYNC_USERNAME': os.getenv('SYNC_USERNAME'),
        'AMRS_ONLINE_URL': os.getenv('AMRS_ONLINE_URL'),
        'BOOTSTRAP_SECRET_TOKEN': os.getenv('BOOTSTRAP_SECRET_TOKEN')
    }
    
    # Check if any credentials are available
    available_credentials = {k: v for k, v in required_credentials.items() if v}
    
    if not available_credentials:
        print("[EMBED] Warning: No bootstrap credentials found in environment variables")
        print("[EMBED] The built application will need to bootstrap from server")
        # Create empty bootstrap file
        bootstrap_content = '''"""
Embedded bootstrap credentials for offline application.
No credentials were available during build time.
"""

EMBEDDED_CREDENTIALS = {}

def get_embedded_credentials():
    """Return embedded credentials for bootstrap."""
    return EMBEDDED_CREDENTIALS.copy()

def has_embedded_credentials():
    """Check if any credentials are embedded."""
    return len(EMBEDDED_CREDENTIALS) > 0
'''
    else:
        print(f"[EMBED] Found {len(available_credentials)} bootstrap credentials")
        for key in available_credentials.keys():
            print(f"[EMBED] - {key}")
        
        # Encode credentials
        credentials_json = json.dumps(available_credentials)
        encoded_credentials = base64.b64encode(credentials_json.encode('utf-8')).decode('ascii')
        
        bootstrap_content = f'''"""
Embedded bootstrap credentials for offline application.
Generated automatically during build process.
"""

import base64
import json

# Encoded credentials (base64 encoded JSON)
_ENCODED_DATA = """{encoded_credentials}"""

def get_embedded_credentials():
    """Return embedded credentials for bootstrap."""
    try:
        decoded_data = base64.b64decode(_ENCODED_DATA.encode('ascii')).decode('utf-8')
        return json.loads(decoded_data)
    except Exception as e:
        print(f"[BOOTSTRAP] Error decoding embedded credentials: {{e}}")
        return {{}}

def has_embedded_credentials():
    """Check if any credentials are embedded."""
    return len(get_embedded_credentials()) > 0

# For compatibility, also expose as module-level dict
try:
    EMBEDDED_CREDENTIALS = get_embedded_credentials()
except:
    EMBEDDED_CREDENTIALS = {{}}
'''
    
    # Write the bootstrap credentials file
    bootstrap_file = Path(__file__).parent / 'embedded_bootstrap_credentials.py'
    with open(bootstrap_file, 'w', encoding='utf-8') as f:
        f.write(bootstrap_content)
    
    print(f"[EMBED] Created {bootstrap_file}")
    return len(available_credentials) > 0

if __name__ == '__main__':
    success = embed_credentials()
    if success:
        print("[EMBED] Bootstrap credentials embedded successfully")
        sys.exit(0)
    else:
        print("[EMBED] No credentials embedded - application will need server bootstrap")
        sys.exit(0)  # Not an error - just no credentials available
