"""
Key Manager for AMRS Preventative Maintenance Application

This module handles secure retrieval of encryption keys
using environment variables (recommended) or Windows Credential Manager (optional).

*** DO NOT STORE ENCRYPTION KEYS IN THIS FILE OR IN THE REPOSITORY. ***
"""

import os
import logging
import platform

# Set up logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
APP_NAME = "AMRS-Preventative-Maintenance"
KEY_NAME = "EncryptionKey"
CREDENTIAL_TARGET = f"{APP_NAME}-{KEY_NAME}"

# Platform-specific imports
if platform.system() == "Windows":
    try:
        import win32cred
        import pywintypes
        WINDOWS_CRED_TYPE = 1  # CRED_TYPE_GENERIC
    except ImportError:
        logger.error("Required Windows modules not available. Install with: pip install pywin32")
        win32cred = None

def get_key_from_windows_credential_manager():
    """Retrieve the encryption key from Windows Credential Manager (optional fallback)"""
    if win32cred is None:
        return None
    try:
        credential = win32cred.CredRead(CREDENTIAL_TARGET, WINDOWS_CRED_TYPE)
        key = credential['CredentialBlob'].decode('utf-8')
        return key
    except Exception as e:
        logger.error(f"Error accessing Windows Credential Manager: {e}")
        return None

def get_or_create_encryption_key():
    """
    Get the encryption key from environment variable (required) or Windows Credential Manager (optional fallback).
    Returns the key as a string or raises an error if not found.
    """
    key = os.environ.get('USER_FIELD_ENCRYPTION_KEY')
    if key:
        return key
    # Optionally, try Windows Credential Manager as a fallback
    if platform.system() == "Windows" and win32cred is not None:
        key = get_key_from_windows_credential_manager()
        if key:
            logger.warning("Encryption key loaded from Windows Credential Manager. For best security, use environment variables.")
            return key
    logger.error("USER_FIELD_ENCRYPTION_KEY environment variable not set. Set this variable before starting the application.")
    raise RuntimeError("USER_FIELD_ENCRYPTION_KEY environment variable not set.")

def generate_new_key():
    """Generate a new Fernet key for initial setup (do not store in code!)"""
    from cryptography.fernet import Fernet
    new_key = Fernet.generate_key().decode()
    print(f"Generated new encryption key: {new_key}")
    print("Store this key securely and set it as USER_FIELD_ENCRYPTION_KEY in your environment.")
    return new_key

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Encryption Key Manager")
    parser.add_argument("--generate", action="store_true", help="Generate a new encryption key")
    parser.add_argument("--get", action="store_true", help="Retrieve the stored encryption key from Windows Credential Manager (if present)")
    args = parser.parse_args()
    if args.generate:
        generate_new_key()
    elif args.get:
        key = get_key_from_windows_credential_manager()
        if key:
            print(f"Retrieved key from Windows Credential Manager: {key}")
        else:
            print("No key found in Windows Credential Manager.")
    else:
        try:
            key = get_or_create_encryption_key()
            print("Encryption key obtained successfully.")
        except Exception as e:
            print(str(e))