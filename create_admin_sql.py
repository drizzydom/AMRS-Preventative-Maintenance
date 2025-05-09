#!/usr/bin/env python3
"""
Create an admin user in the SQLite database for offline mode
This script creates a user directly in the SQLite database using the proper encryption
"""
import os
import sys
import logging
import uuid
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[CREATE_ADMIN] %(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("create_admin")

# Import the local_database module we need
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import local_database
from cryptography.fernet import Fernet
from werkzeug.security import generate_password_hash

# Configuration
INSTANCE_DIR = os.path.join(current_dir, 'instance')
DB_PATH = Path(os.path.join(INSTANCE_DIR, 'maintenance.db'))
ENCRYPTION_KEY = "_CY9_bO9vrX2CEUNmFqD1ETx-CluNejbidXFGMYapis="

# Admin user config
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"
ADMIN_EMAIL = "admin@example.com"
ADMIN_FULLNAME = "System Administrator"

def create_admin_user():
    """Create an admin user directly in the SQLite database"""
    # Ensure the database exists and has the right tables
    try:
        if not DB_PATH.parent.exists():
            logger.info(f"Creating directory: {DB_PATH.parent}")
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Create database tables if they don't exist
        local_database.create_tables(DB_PATH, ENCRYPTION_KEY)
        logger.info(f"Database tables created at {DB_PATH}")
        
        # Prepare fernet for encryption
        fernet = Fernet(ENCRYPTION_KEY)
        
        # Connect to the database
        conn = local_database.get_db_connection(DB_PATH, ENCRYPTION_KEY)
        cursor = conn.cursor()
        
        # First ensure we have an admin role
        cursor.execute("SELECT id FROM roles WHERE name = 'admin'")
        admin_role = cursor.fetchone()
        
        if admin_role:
            admin_role_id = admin_role['id']
            logger.info(f"Found existing admin role with id {admin_role_id}")
        else:
            logger.info("Creating admin role")
            cursor.execute("""
                INSERT INTO roles (server_id, name, description, permissions, is_synced, last_modified)
                VALUES (1, 'admin', 'Administrator', 'admin.full', 1, ?)
            """, (datetime.now().isoformat(),))
            admin_role_id = cursor.lastrowid
            logger.info(f"Created admin role with id {admin_role_id}")
        
        # Generate client_id for the user
        client_id = str(uuid.uuid4())
        
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE username = ?", 
                      (fernet.encrypt(ADMIN_USERNAME.encode()).decode(),))
        admin_user = cursor.fetchone()
        
        if admin_user:
            logger.info(f"Admin user already exists with id {admin_user['id']}")
        else:
            # Create the admin user
            logger.info("Creating admin user")
            cursor.execute("""
                INSERT INTO users (
                    client_id, server_id, username, email, full_name, 
                    role_id, is_synced, last_modified
                ) VALUES (?, 1, ?, ?, ?, ?, 1, ?)
            """, (
                client_id,
                fernet.encrypt(ADMIN_USERNAME.encode()).decode(),
                fernet.encrypt(ADMIN_EMAIL.encode()).decode(),
                ADMIN_FULLNAME,
                admin_role_id,
                datetime.now().isoformat()
            ))
            
            user_id = cursor.lastrowid
            logger.info(f"Created admin user with id {user_id}, username '{ADMIN_USERNAME}', and password '{ADMIN_PASSWORD}'")
            
            # Note: The local database schema doesn't include password_hash column
            # In offline mode, we'll use a workaround where passwords are verified by Flask
            
            # Commit all changes
        conn.commit()
        logger.info("Database changes committed")
        
        return True
    
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_admin_user()
    sys.exit(0 if success else 1)
