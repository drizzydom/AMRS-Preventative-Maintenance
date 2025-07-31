#!/usr/bin/env python3
"""
Load environment variables from bootstrap keyring before app initialization.
This prevents the encryption key error by ensuring the USER_FIELD_ENCRYPTION_KEY
is available in the environment before models.py is imported.
"""

import os
import keyring
import platform

def get_secure_storage_service():
    """Get the appropriate secure storage service name based on OS."""
    os_name = platform.system().lower()
    
    if os_name == "windows":
        return "amrs_pm_windows"
    elif os_name == "darwin":  # macOS
        return "amrs_pm_macos"
    elif os_name == "linux":
        return "amrs_pm_linux"
    else:
        return "amrs_pm_unknown"

def load_bootstrap_env():
    """Load environment variables from secure keyring storage."""
    try:
        service = get_secure_storage_service()
        
        # List of keys that might be stored in keyring
        bootstrap_keys = [
            'AMRS_ADMIN_USERNAME',
            'AMRS_ADMIN_PASSWORD', 
            'USER_FIELD_ENCRYPTION_KEY',
            'SYNC_URL',
            'SYNC_USERNAME',
            'AMRS_ONLINE_URL',
            'RENDER_EXTERNAL_URL'
        ]
        
        loaded_count = 0
        for key in bootstrap_keys:
            try:
                value = keyring.get_password(service, key)
                if value:
                    os.environ[key] = value
                    loaded_count += 1
                    if key == 'USER_FIELD_ENCRYPTION_KEY':
                        print(f"[BOOTSTRAP ENV] ✅ Loaded {key} from keyring")
                    else:
                        print(f"[BOOTSTRAP ENV] ✅ Loaded {key} from keyring")
            except Exception as e:
                # Skip keys that don't exist or can't be accessed
                pass
        
        if loaded_count > 0:
            print(f"[BOOTSTRAP ENV] ✅ Loaded {loaded_count} environment variables from keyring")
            return True
        else:
            print("[BOOTSTRAP ENV] ℹ️  No environment variables found in keyring")
            return False
            
    except Exception as e:
        print(f"[BOOTSTRAP ENV] ⚠️  Error loading from keyring: {e}")
        return False

if __name__ == "__main__":
    load_bootstrap_env()
