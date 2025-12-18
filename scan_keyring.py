
import keyring
import sys
import base64
from cryptography.fernet import Fernet, InvalidToken

# Service names to check
SERVICES = [
    "amrs_pm",
    "amrs_pm_windows",
    "amrs_pm_macos",
    "amrs_pm_linux",
    "amrs",
    "AMRS_PM",
    "system",
    "login"
]

# Usernames to check
USERNAMES = [
    "USER_FIELD_ENCRYPTION_KEY",
    "AMRS_ENCRYPTION_KEY",
    "ENCRYPTION_KEY",
    "FERNET_KEY",
    "SECRET_KEY"
]

# The token we want to decrypt (User 324)
TARGET_TOKEN = "gAAAAABoxdcQ8NypGnat1kN-Ep_9eYpfklP0EzTSx8YwPgky2XZVks800ZPBhbIQnlGjj0zxcDptt-kQ8u50czerota5YH9ong=="

print("Scanning keyring for keys...")

found_keys = []

for service in SERVICES:
    for username in USERNAMES:
        try:
            password = keyring.get_password(service, username)
            if password:
                print(f"Found key in {service}/{username}: {password[:10]}...")
                found_keys.append((service, username, password))
        except Exception as e:
            print(f"Error checking {service}/{username}: {e}")

print(f"\nFound {len(found_keys)} potential keys.")

for service, username, key in found_keys:
    try:
        f = Fernet(key)
        decrypted = f.decrypt(TARGET_TOKEN.encode()).decode()
        print(f"\nSUCCESS! Key from {service}/{username} decrypted the token!")
        print(f"Key: {key}")
        print(f"Decrypted value: {decrypted}")
        sys.exit(0)
    except Exception as e:
        print(f"Key from {service}/{username} failed: {e}")

print("\nNo working key found in keyring.")
