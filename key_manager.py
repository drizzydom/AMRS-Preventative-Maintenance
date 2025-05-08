"""
Key Manager for AMRS Preventative Maintenance Application

This module handles secure storage and retrieval of encryption keys
using Windows Credential Manager when on Windows, or other secure
storage mechanisms on other platforms.
"""

import os
import sys
import base64
import logging
from cryptography.fernet import Fernet
import platform

# Set up logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
APP_NAME = "AMRS-Preventative-Maintenance"
KEY_NAME = "EncryptionKey"
CREDENTIAL_TARGET = f"{APP_NAME}-{KEY_NAME}"

# The static encryption key to use for this application
# This is stored in Windows Credential Manager to prevent tampering
STATIC_ENCRYPTION_KEY = "_CY9_bO9vrX2CEUNmFqD1ETx-CluNejbidXFGMYapis="

# Platform-specific imports
if platform.system() == "Windows":
    try:
        import win32cred
        import win32credui
        import pywintypes
        WINDOWS_CRED_TYPE = 1  # CRED_TYPE_GENERIC
    except ImportError:
        logger.error("Required Windows modules not available. Install with: pip install pywin32")
        logger.info("Falling back to file-based storage")
        win32cred = None

def get_key_from_windows_credential_manager():
    """Retrieve the encryption key from Windows Credential Manager"""
    if win32cred is None:
        return None
    
    try:
        credential = win32cred.CredRead(CREDENTIAL_TARGET, WINDOWS_CRED_TYPE)
        key = credential['CredentialBlob'].decode('utf-8')
        return key
    except pywintypes.error as e:
        if e.winerror == 1168:  # ERROR_NOT_FOUND
            return None
        logger.error(f"Error accessing Windows Credential Manager: {e}")
        return None

def store_key_in_windows_credential_manager(key):
    """Store the encryption key in Windows Credential Manager"""
    if win32cred is None:
        return False
    
    try:
        credential = {
            'Type': WINDOWS_CRED_TYPE,
            'TargetName': CREDENTIAL_TARGET,
            'UserName': os.getlogin(),
            'CredentialBlob': key,
            'Persist': 2  # CRED_PERSIST_LOCAL_MACHINE
        }
        win32cred.CredWrite(credential, 0)
        return True
    except Exception as e:
        logger.error(f"Error storing key in Windows Credential Manager: {e}")
        return False

def get_or_create_encryption_key():
    """
    Get the encryption key from secure storage or automatically set the static key.
    Returns the key as a string or None if it couldn't be obtained.
    """
    # First, check if the key is in environment variables
    key = os.environ.get('USER_FIELD_ENCRYPTION_KEY')
    if key:
        return key
    
    # Then, check secure storage based on platform
    if platform.system() == "Windows" and win32cred is not None:
        key = get_key_from_windows_credential_manager()
        if key:
            return key
    
    # If we don't have a key yet, use the static key and store it
    logger.info("No encryption key found in storage, using the static key")
    key = STATIC_ENCRYPTION_KEY
    
    # Store the static key securely
    if platform.system() == "Windows" and win32cred is not None:
        stored = store_key_in_windows_credential_manager(key)
        if stored:
            logger.info("Encryption key successfully stored in Windows Credential Manager")
        else:
            logger.warning("Failed to store encryption key securely")
    
    return key

def generate_new_key():
    """Generate a new Fernet key for testing or initial setup"""
    new_key = Fernet.generate_key().decode()
    print(f"Generated new encryption key: {new_key}")
    print("Store this key securely and use it for your deployment.")
    return new_key

if __name__ == "__main__":
    # When run directly, this module can generate a new key or test key storage
    import argparse
    
    parser = argparse.ArgumentParser(description="Encryption Key Manager")
    parser.add_argument("--generate", action="store_true", help="Generate a new encryption key")
    parser.add_argument("--store", type=str, help="Store a specific key in secure storage")
    parser.add_argument("--get", action="store_true", help="Retrieve the stored encryption key")
    parser.add_argument("--reset", action="store_true", help="Reset to use the default static key")
    args = parser.parse_args()
    
    if args.generate:
        key = generate_new_key()
        store = input("Do you want to store this key securely? (y/n): ")
        if store.lower() == 'y':
            if store_key_in_windows_credential_manager(key):
                print("Key stored successfully!")
    elif args.store:
        if store_key_in_windows_credential_manager(args.store):
            print("Key stored successfully!")
        else:
            print("Failed to store key")
    elif args.get:
        key = get_key_from_windows_credential_manager()
        if key:
            print(f"Retrieved key: {key}")
        else:
            print("No key found in secure storage")
    elif args.reset:
        if store_key_in_windows_credential_manager(STATIC_ENCRYPTION_KEY):
            print("Static key stored successfully!")
        else:
            print("Failed to store static key")
    else:
        # Default behavior - just get or create the key (no prompting)
        key = get_or_create_encryption_key()
        if key:
            print("Encryption key obtained successfully")
        else:
            print("Failed to obtain encryption key")