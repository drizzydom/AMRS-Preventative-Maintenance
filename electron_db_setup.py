"""
Database setup utilities for Electron application
"""
import os
import logging
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)

def create_database(db_path, schema_file=None):
    """
    Create a SQLite database for the application
    
    Args:
        db_path (str): Path to the database file (not URI)
        schema_file (str, optional): Path to SQL schema file
        
    Returns:
        sqlite3.Connection: Database connection
    """
    logger.info(f"Creating database at {db_path}")
    
    # Fix the SQLite URI issue - ensure we're using a file path, not a URI
    if db_path.startswith('sqlite:///'):
        db_path = db_path[10:]  # Remove 'sqlite:///'
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create or connect to the database
    conn = sqlite3.connect(db_path)
    
    # Apply schema if provided
    if schema_file and os.path.exists(schema_file):
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        conn.executescript(schema_sql)
        logger.info(f"Applied schema from {schema_file}")
    else:
        logger.info("No schema applied (file not provided or not found)")
    
    # Create a basic structure if no schema provided
    cursor = conn.cursor()
    
    # Check if users table exists and create if not
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        logger.info("Creating basic users table")
        cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            username_hash TEXT,
            email TEXT UNIQUE,
            email_hash TEXT,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            role_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reset_token TEXT,
            reset_token_expiration TIMESTAMP,
            notification_preferences TEXT,
            last_login TIMESTAMP
        )
        ''')
    
    # Apply any necessary migrations
    try:
        # Add last_login column to users table if it doesn't exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'last_login' not in columns:
            logger.info("Adding last_login column to users table")
            cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
    except Exception as e:
        logger.error(f"Error applying migrations: {str(e)}")
    
    conn.commit()
    return conn

def get_database_path():
    """Get the default database path"""
    appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    db_dir = os.path.join(appdata, 'amrs-preventative-maintenance', 'AMRS-Maintenance-Tracker')
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, 'amrs_maintenance.db')

logger.info("electron_db_setup module loaded successfully")