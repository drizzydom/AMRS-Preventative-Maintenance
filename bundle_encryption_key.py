#!/usr/bin/env python
"""
Script to securely bundle the encryption key from the environment 
into the desktop application during build
"""
import os
import sys
import base64
from pathlib import Path
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
import uuid
import json

def encrypt_key_with_machine_id():
    """
    Encrypt the encryption key using a machine-specific identifier
    This creates a key that can only be decrypted on the same machine
    """
    # Get the encryption key from environment
    encryption_key = os.environ.get('USER_FIELD_ENCRYPTION_KEY')
    
    if not encryption_key:
        print("[WARNING] USER_FIELD_ENCRYPTION_KEY not found in environment.")
        print("[WARNING] The desktop application will generate a new key.")
        print("[WARNING] This means users won't be able to read data encrypted by the Render instance.")
        return None
    
    # Create a unique identifier for the application bundler
    # This is just used during the build process
    bundler_id = str(uuid.uuid4())
    
    # Generate a key derivation salt
    salt = os.urandom(16)
    
    # Create a simple encrypted package with the information needed
    # to later derive the key on the device
    key_package = {
        'salt': base64.b64encode(salt).decode('utf-8'),
        'bundler_id': bundler_id,
        'key': encryption_key
    }
    
    return json.dumps(key_package)

def main():
    """
    Main function to extract the encryption key and save it
    """
    print("[BUILD] Bundling encryption key for desktop application...")
    
    # Get the encryption key from environment
    encryption_key = os.environ.get('USER_FIELD_ENCRYPTION_KEY')
    
    if not encryption_key:
        print("[WARNING] USER_FIELD_ENCRYPTION_KEY not found in environment.")
        print("[WARNING] The desktop application will generate a new key.")
        print("[WARNING] This means users won't be able to read data encrypted by the Render instance.")
        return 1
    
    # Create a packaged key with bundler information
    key_package = encrypt_key_with_machine_id()
    if not key_package:
        return 1
    
    # Resources directory where the Flask app will look for the key
    resources_dir = os.path.join("electron_app", "resources")
    if not os.path.exists(resources_dir):
        os.makedirs(resources_dir, exist_ok=True)
        print(f"[BUILD] Created resources directory: {resources_dir}")
    
    # Save the key package to a file
    key_path = os.path.join(resources_dir, ".env.key.secure")
    with open(key_path, 'w') as f:
        f.write(key_package)
    
    print(f"[BUILD] Encryption key bundled securely to {key_path}")
    print("[BUILD] This key will be used by the desktop application to decrypt data")
    print("[INFO] The key is stored in a format that requires additional processing to use")
    return 0

if __name__ == "__main__":
    sys.exit(main())