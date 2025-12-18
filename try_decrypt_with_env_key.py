
import os
import sys
import base64
from cryptography.fernet import Fernet, InvalidToken
from models import db, User
from app import app

# Keys to try
KEYS = {
    "ENV_KEY": "_CY9_bO9vrX2CEUNmFqD1ETx-CluNejbidXFGMYapis=",
    "SECRET_CONFIG_KEY": "M12CG_hV5Vw9MAaJ-s7vzQeSyOD_8HXKgEsKZ_FJSLs=",
    "TEST_KEY": base64.urlsafe_b64encode(b"0123456789ABCDEF0123456789ABCDEF").decode()
}

def try_decrypt():
    with app.app_context():
        users = User.query.all()
        
        for user in users:
            if not user._username or not user._username.startswith('gAAAAA'):
                continue
                
            print(f"\nUser {user.id} ({user.role.name if user.role else 'No Role'}):")
            
            success = False
            for key_name, key in KEYS.items():
                try:
                    f = Fernet(key)
                    decrypted = f.decrypt(user._username.encode()).decode()
                    print(f"  SUCCESS with {key_name}: {decrypted}")
                    success = True
                    break # Stop after first success
                except InvalidToken:
                    pass
                except Exception as e:
                    print(f"  Error with {key_name}: {e}")
            
            if not success:
                print(f"  FAILURE: Could not decrypt with any known key")

if __name__ == "__main__":
    try_decrypt()
