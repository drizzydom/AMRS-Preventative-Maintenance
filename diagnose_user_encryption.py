#!/usr/bin/env python3
"""
Diagnostic script to check user data encryption status
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, User, decrypt_value, get_fernet
from app import app

def check_user_encryption():
    """Check the encryption status of user data"""
    with app.app_context():
        print("=" * 60)
        print("USER DATA ENCRYPTION DIAGNOSTIC")
        print("=" * 60)
        
        # Check if encryption key is available
        try:
            fernet = get_fernet()
            print("✓ Encryption key loaded successfully")
        except Exception as e:
            print(f"✗ Failed to load encryption key: {e}")
            return
        
        # Get all users
        users = User.query.all()
        print(f"\nFound {len(users)} users in database")
        print("=" * 60)
        
        for user in users:
            print(f"\nUser ID: {user.id}")
            print(f"  Role: {user.role.name if user.role else 'None'}")
            print(f"  Is Admin: {user.is_admin}")
            
            # Check raw username value
            print(f"\n  Raw _username column value:")
            print(f"    Length: {len(user._username) if user._username else 0}")
            print(f"    First 50 chars: {user._username[:50] if user._username else 'None'}...")
            
            # Try to decrypt username
            try:
                decrypted_username = user.username  # This calls the @property
                print(f"  ✓ Decrypted username: {decrypted_username}")
            except Exception as e:
                print(f"  ✗ Failed to decrypt username: {e}")
                # Try manual decryption
                try:
                    manual_decrypt = decrypt_value(user._username)
                    print(f"  Manual decrypt result: {manual_decrypt}")
                except Exception as e2:
                    print(f"  ✗ Manual decrypt also failed: {e2}")
            
            # Check raw email value
            print(f"\n  Raw _email column value:")
            print(f"    Length: {len(user._email) if user._email else 0}")
            print(f"    First 50 chars: {user._email[:50] if user._email else 'None'}...")
            
            # Try to decrypt email
            try:
                decrypted_email = user.email  # This calls the @property
                print(f"  ✓ Decrypted email: {decrypted_email}")
            except Exception as e:
                print(f"  ✗ Failed to decrypt email: {e}")
                # Try manual decryption
                try:
                    manual_decrypt = decrypt_value(user._email)
                    print(f"  Manual decrypt result: {manual_decrypt}")
                except Exception as e2:
                    print(f"  ✗ Manual decrypt also failed: {e2}")
            
            print("-" * 60)

if __name__ == '__main__':
    check_user_encryption()
