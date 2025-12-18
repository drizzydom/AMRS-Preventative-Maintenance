
import os
import sys
import requests
import json
from models import db, User
from app import app

# Bootstrap credentials (from .env.bootstrap or hardcoded for testing)
BOOTSTRAP_URL = "https://amrs-preventative-maintenance.onrender.com/api/bootstrap-secrets"
BOOTSTRAP_TOKEN = "REDACTED_BOOTSTRAP_TOKEN"

def fetch_server_users():
    """Fetch users from the server to see what they look like."""
    # We need to authenticate to get users. 
    # But first, let's just check if we can get the bootstrap secrets to confirm the key.
    
    print(f"Fetching bootstrap secrets from {BOOTSTRAP_URL}...")
    try:
        resp = requests.post(
            BOOTSTRAP_URL, 
            headers={"Authorization": f"Bearer {BOOTSTRAP_TOKEN}"},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            server_key = data.get("USER_FIELD_ENCRYPTION_KEY")
            print(f"Server returned key: {server_key}")
            
            # Load local key from .env manually since app context might not have it if not in os.environ
            from dotenv import load_dotenv
            load_dotenv()
            local_key = os.environ.get("USER_FIELD_ENCRYPTION_KEY")
            print(f"Local key: {local_key}")
            
            if server_key == local_key:
                print("KEYS MATCH!")
            else:
                print("KEYS DO NOT MATCH!")
        else:
            print(f"Failed to fetch secrets: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"Error fetching secrets: {e}")

if __name__ == "__main__":
    with app.app_context():
        fetch_server_users()
