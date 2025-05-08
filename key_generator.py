from cryptography.fernet import Fernet

# Generate a key (do this once and save the key securely)
key = Fernet.generate_key()
print("KEY:", key.decode())

# Encrypt your secret
f = Fernet(key)
token = f.encrypt(b'your_actual_secret_here')
print("ENCRYPTED_SECRET:", token.decode())