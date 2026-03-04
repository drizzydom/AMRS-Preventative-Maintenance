
import os
import sys
import requests
import json
from models import db, User
from app import app

# Bootstrap credentials (environment-driven)
AMRS_ONLINE_URL = os.environ.get("AMRS_ONLINE_URL", "").rstrip("/")
BOOTSTRAP_URL = os.environ.get("BOOTSTRAP_URL") or (
    f"{AMRS_ONLINE_URL}/api/bootstrap-secrets" if AMRS_ONLINE_URL else None
)
BOOTSTRAP_TOKEN = os.environ.get("DEVICE_BOOTSTRAP_TOKEN") or os.environ.get("BOOTSTRAP_SECRET_TOKEN")
BOOTSTRAP_DEVICE_ID = os.environ.get("BOOTSTRAP_DEVICE_ID") or os.environ.get("DEVICE_ID")


def validate_required_env():
    """Ensure required bootstrap values are available before making requests."""
    required = {
        "BOOTSTRAP_URL": BOOTSTRAP_URL,
        "BOOTSTRAP_SECRET_TOKEN/DEVICE_BOOTSTRAP_TOKEN": BOOTSTRAP_TOKEN,
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing)
        )

def fetch_server_users():
    """Fetch users from the server to see what they look like."""
    validate_required_env()
    # We need to authenticate to get users. 
    # But first, let's just check if we can get the bootstrap secrets to confirm the key.
    
    print(f"Fetching bootstrap secrets from {BOOTSTRAP_URL}...")
    try:
        headers = {"Authorization": f"Bearer {BOOTSTRAP_TOKEN}"}
        if BOOTSTRAP_DEVICE_ID:
            headers["X-Device-ID"] = BOOTSTRAP_DEVICE_ID

        resp = requests.post(
            BOOTSTRAP_URL, 
            headers=headers,
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
