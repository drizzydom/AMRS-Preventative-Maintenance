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

def load_temporary_bootstrap_env():
    """Load bootstrap credentials from temporary .env.bootstrap file."""
    try:
        from dotenv import load_dotenv
        
        # Try multiple paths for .env.bootstrap file
        base_dir = os.path.dirname(__file__)
        bootstrap_paths = [
            os.path.join(base_dir, '.env.bootstrap'),  # Same directory as this file
            os.path.join(os.getcwd(), '.env.bootstrap'),  # Current working directory
            '.env.bootstrap'  # Relative to working directory
        ]
        
        bootstrap_env_path = None
        for path in bootstrap_paths:
            if os.path.exists(path):
                bootstrap_env_path = path
                break
        
        if bootstrap_env_path:
            print(f"[BOOTSTRAP ENV] Found temporary bootstrap file: {bootstrap_env_path}")
            load_dotenv(bootstrap_env_path)
            
            # Check what was loaded
            bootstrap_keys = ['BOOTSTRAP_URL', 'BOOTSTRAP_SECRET_TOKEN', 'AMRS_ADMIN_USERNAME', 'AMRS_ADMIN_PASSWORD', 'AMRS_ONLINE_URL']
            loaded_keys = []
            
            for key in bootstrap_keys:
                if os.getenv(key):
                    loaded_keys.append(key)
            
            if loaded_keys:
                print(f"[BOOTSTRAP ENV] SUCCESS: Loaded {len(loaded_keys)} bootstrap variables from temporary file")
                for key in loaded_keys:
                    print(f"[BOOTSTRAP ENV] - {key}")
                return True, bootstrap_env_path
            else:
                print("[BOOTSTRAP ENV] WARNING: Temporary bootstrap file found but no variables loaded")
                return False, bootstrap_env_path
        else:
            print(f"[BOOTSTRAP ENV] No temporary bootstrap file found at any of these paths:")
            for path in bootstrap_paths:
                print(f"[BOOTSTRAP ENV] - {path} (exists: {os.path.exists(path)})")
            return False, None
            
    except ImportError:
        print("[BOOTSTRAP ENV] WARNING: python-dotenv not available, cannot load .env.bootstrap")
        return False, None
    except Exception as e:
        print(f"[BOOTSTRAP ENV] ERROR: Failed to load temporary bootstrap file: {e}")
        return False, None

def delete_bootstrap_file(file_path):
    """Safely delete the temporary bootstrap file."""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            print(f"[BOOTSTRAP ENV] SUCCESS: Deleted temporary bootstrap file: {file_path}")
            return True
        else:
            print("[BOOTSTRAP ENV] INFO: No temporary bootstrap file to delete")
            return False
    except Exception as e:
        print(f"[BOOTSTRAP ENV] WARNING: Could not delete temporary bootstrap file: {e}")
        return False

def load_bootstrap_env():
    """Load environment variables from secure keyring storage, embedded credentials, or temporary bootstrap file."""
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
            'RENDER_EXTERNAL_URL',
            'BOOTSTRAP_URL',
            'BOOTSTRAP_SECRET_TOKEN'
        ]
        
        loaded_count = 0
        
        # First try to load from keyring
        for key in bootstrap_keys:
            try:
                value = keyring.get_password(service, key)
                if value:
                    os.environ[key] = value
                    loaded_count += 1
                    if key in ['USER_FIELD_ENCRYPTION_KEY', 'BOOTSTRAP_SECRET_TOKEN']:
                        print(f"[BOOTSTRAP ENV] SUCCESS: Loaded {key} from keyring")
                    else:
                        print(f"[BOOTSTRAP ENV] SUCCESS: Loaded {key} from keyring")
            except Exception as e:
                # Skip keys that don't exist or can't be accessed
                pass
        
        # If no keyring credentials found, try temporary bootstrap file
        bootstrap_file_path = None
        if loaded_count == 0:
            try:
                bootstrap_loaded, bootstrap_file_path = load_temporary_bootstrap_env()
                if bootstrap_loaded:
                    loaded_count += len([k for k in bootstrap_keys if os.getenv(k)])
                    
                    # Store the file path for later deletion
                    os.environ['_BOOTSTRAP_FILE_PATH'] = bootstrap_file_path or ''
                
            except Exception as e:
                print(f"[BOOTSTRAP ENV] WARNING: Error loading temporary bootstrap file: {e}")
        
        # If still no credentials, try embedded credentials as final fallback
        if loaded_count == 0:
            try:
                from embedded_bootstrap_credentials import get_embedded_credentials, has_embedded_credentials, create_bootstrap_env_file
                
                if has_embedded_credentials():
                    print("[BOOTSTRAP ENV] INFO: No keyring or bootstrap file credentials found, using embedded credentials...")
                    
                    # Try to create .env.bootstrap file from embedded credentials
                    try:
                        bootstrap_file_path = create_bootstrap_env_file()
                        if bootstrap_file_path:
                            bootstrap_loaded, _ = load_temporary_bootstrap_env()
                            if bootstrap_loaded:
                                loaded_count += len([k for k in bootstrap_keys if os.getenv(k)])
                                print("[BOOTSTRAP ENV] SUCCESS: Loaded credentials from embedded source")
                                os.environ['_BOOTSTRAP_FILE_PATH'] = bootstrap_file_path
                            else:
                                # Fallback: set environment variables directly
                                embedded_creds = get_embedded_credentials()
                                for key, value in embedded_creds.items():
                                    if value and key in bootstrap_keys:
                                        os.environ[key] = value
                                        loaded_count += 1
                                        print(f"[BOOTSTRAP ENV] Set {key} from embedded credentials")
                        else:
                            # Direct environment variable setting
                            embedded_creds = get_embedded_credentials()
                            for key, value in embedded_creds.items():
                                if value and key in bootstrap_keys:
                                    os.environ[key] = value
                                    loaded_count += 1
                                    print(f"[BOOTSTRAP ENV] Set {key} from embedded credentials")
                    except Exception as create_err:
                        print(f"[BOOTSTRAP ENV] WARNING: Could not create bootstrap file, setting environment variables directly: {create_err}")
                        # Direct environment variable setting as final fallback
                        embedded_creds = get_embedded_credentials()
                        for key, value in embedded_creds.items():
                            if value and key in bootstrap_keys:
                                os.environ[key] = value
                                loaded_count += 1
                                print(f"[BOOTSTRAP ENV] Set {key} from embedded credentials")
                            os.environ[key] = value
                            loaded_count += 1
                            print(f"[BOOTSTRAP ENV] SUCCESS: Loaded {key} from embedded credentials")
                    
            except ImportError:
                print("[BOOTSTRAP ENV] INFO: No embedded credentials file found")
            except Exception as e:
                print(f"[BOOTSTRAP ENV] WARNING: Error loading embedded credentials: {e}")
        
        if loaded_count > 0:
            print(f"[BOOTSTRAP ENV] SUCCESS: Loaded {loaded_count} environment variables")
            return True
        else:
            print("[BOOTSTRAP ENV] INFO: No environment variables found in any source")
            return False
            
    except Exception as e:
        print(f"[BOOTSTRAP ENV] WARNING: Error loading bootstrap environment: {e}")
        return False

def cleanup_bootstrap_file():
    """Clean up temporary bootstrap file after successful bootstrap."""
    bootstrap_file_path = os.getenv('_BOOTSTRAP_FILE_PATH')
    if bootstrap_file_path:
        success = delete_bootstrap_file(bootstrap_file_path)
        if success:
            # Remove the environment variable
            os.environ.pop('_BOOTSTRAP_FILE_PATH', None)
        return success
    return False

if __name__ == "__main__":
    load_bootstrap_env()
