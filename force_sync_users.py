
import os
import sys
import requests
import json
from models import db, User
from app import app

# Sync credentials (environment-driven)
AMRS_ONLINE_URL = os.environ.get("AMRS_ONLINE_URL", "").rstrip("/")
SYNC_URL = os.environ.get("SYNC_URL") or (
    f"{AMRS_ONLINE_URL}/api/sync/data" if AMRS_ONLINE_URL else None
)
SYNC_USERNAME = os.environ.get("SYNC_USERNAME") or os.environ.get("AMRS_ADMIN_USERNAME")
SYNC_PASSWORD = os.environ.get("SYNC_PASSWORD") or os.environ.get("AMRS_ADMIN_PASSWORD")


def validate_required_env():
    """Ensure required sync values are available before making requests."""
    required = {
        "SYNC_URL": SYNC_URL,
        "SYNC_USERNAME": SYNC_USERNAME,
        "SYNC_PASSWORD": SYNC_PASSWORD,
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing)
        )

def fetch_and_update_users():
    """Fetch users from the server and update the local database."""
    validate_required_env()
    print(f"Fetching user data from {SYNC_URL}...")
    
    try:
        # Authenticate first? The sync endpoint usually requires Basic Auth
        resp = requests.get(
            SYNC_URL, 
            auth=(SYNC_USERNAME, SYNC_PASSWORD),
            params={"since": 0}, # Get all data
            timeout=30
        )
        
        if resp.status_code == 200:
            data = resp.json()
            users = data.get("users", [])
            print(f"Received {len(users)} users from server.")
            
            with app.app_context():
                updated_count = 0
                for u in users:
                    # Find local user
                    local_user = User.query.get(u['id'])
                    if local_user:
                        # Check if we need to update
                        # The server sends 'username' (decrypted) and 'email' (decrypted)
                        # We should use the property setters to encrypt them with the local key
                        
                        if u.get('username'):
                            print(f"Updating User {u['id']} username: {u['username']}")
                            local_user.username = u['username']
                            updated_count += 1
                            
                        if u.get('email'):
                            print(f"Updating User {u['id']} email: {u['email']}")
                            local_user.email = u['email']
                            updated_count += 1
                
                if updated_count > 0:
                    db.session.commit()
                    print(f"Successfully updated {updated_count} fields.")
                else:
                    print("No updates needed. Local data matches server data.")
                    
        else:
            print(f"Failed to fetch sync data: {resp.status_code} {resp.text}")
            
    except Exception as e:
        print(f"Error during sync: {e}")

if __name__ == "__main__":
    fetch_and_update_users()
