#!/usr/bin/env python3
"""
Initialize a standard SQLite database for offline mode 
This script creates an unencrypted SQLite database with an admin user
"""
import os
import sys
import logging
import sqlite3
from pathlib import Path
from datetime import datetime
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO, format='[INIT_SQLITE] %(levelname)s - %(message)s')
logger = logging.getLogger("init_sqlite_db")

# Configuration
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
DB_PATH = os.path.join(DB_DIR, 'maintenance.db')

def create_standard_db():
    """Create a standard SQLite database with necessary tables and admin user"""
    try:
        # Ensure directory exists
        if not os.path.exists(DB_DIR):
            os.makedirs(DB_DIR, exist_ok=True)
            
        # Remove existing database if it exists
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            logger.info(f"Removed existing database at {DB_PATH}")
            
        # Create a new database connection
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        logger.info(f"Creating new SQLite database at {DB_PATH}")
        
        # Create tables
        cursor.execute('''
        CREATE TABLE roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            permissions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            username_hash TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            email_hash TEXT NOT NULL UNIQUE,
            full_name TEXT,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            role_id INTEGER,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reset_token TEXT,
            reset_token_expiration TIMESTAMP,
            notification_preferences TEXT,
            FOREIGN KEY (role_id) REFERENCES roles (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT,
            contact_email TEXT,
            enable_notifications BOOLEAN DEFAULT 1,
            notification_threshold INTEGER DEFAULT 30,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE machines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            model TEXT,
            machine_number TEXT,
            serial_number TEXT,
            site_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            machine_id INTEGER NOT NULL,
            maintenance_frequency INTEGER DEFAULT 30,
            maintenance_unit TEXT DEFAULT 'day',
            maintenance_days INTEGER DEFAULT 30,
            last_maintenance TIMESTAMP,
            next_maintenance TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (machine_id) REFERENCES machines (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE maintenance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            machine_id INTEGER,
            date TIMESTAMP NOT NULL,
            comments TEXT,
            maintenance_type TEXT,
            description TEXT,
            performed_by TEXT,
            status TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (part_id) REFERENCES parts (id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (machine_id) REFERENCES machines (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE audit_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            site_id INTEGER NOT NULL,
            created_by INTEGER,
            interval TEXT DEFAULT 'daily',
            custom_interval_days INTEGER,
            color TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE audit_task_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audit_task_id INTEGER NOT NULL,
            machine_id INTEGER NOT NULL,
            date TIMESTAMP NOT NULL,
            completed BOOLEAN DEFAULT 0,
            completed_by INTEGER,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (audit_task_id) REFERENCES audit_tasks (id),
            FOREIGN KEY (machine_id) REFERENCES machines (id),
            FOREIGN KEY (completed_by) REFERENCES users (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE user_site (
            user_id INTEGER NOT NULL,
            site_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, site_id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (site_id) REFERENCES sites (id)
        )
        ''')

        logger.info("Tables created successfully")
        
        # Create admin role
        cursor.execute('''
        INSERT INTO roles (name, description, permissions)
        VALUES (?, ?, ?)
        ''', ('admin', 'Administrator', 'admin.full'))
        
        admin_role_id = cursor.lastrowid
        logger.info(f"Created admin role with ID {admin_role_id}")
        
        # Create admin user
        admin_username = 'admin'
        admin_username_hash = 'admin_hash'  # Simplified for this script
        admin_email = 'admin@example.com'
        admin_email_hash = 'admin_email_hash'  # Simplified for this script
        admin_password_hash = generate_password_hash('admin')
        
        cursor.execute('''
        INSERT INTO users (username, username_hash, email, email_hash, full_name, password_hash, is_admin, role_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (admin_username, admin_username_hash, admin_email, admin_email_hash, 'System Administrator', admin_password_hash, 1, admin_role_id))
        
        logger.info(f"Created admin user: username={admin_username}, password=admin")
        
        # Create test site
        cursor.execute('''
        INSERT INTO sites (name, location)
        VALUES (?, ?)
        ''', ('Test Site', 'Test Location'))
        
        site_id = cursor.lastrowid
        logger.info(f"Created test site with ID {site_id}")
        
        # Create test machine
        cursor.execute('''
        INSERT INTO machines (name, model, machine_number, serial_number, site_id)
        VALUES (?, ?, ?, ?, ?)
        ''', ('Test Machine', 'TM-1000', 'TM-1001', 'SN12345', site_id))
        
        machine_id = cursor.lastrowid
        logger.info(f"Created test machine with ID {machine_id}")
        
        # Commit all changes
        conn.commit()
        logger.info("Database initialized successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = create_standard_db()
    sys.exit(0 if success else 1)
