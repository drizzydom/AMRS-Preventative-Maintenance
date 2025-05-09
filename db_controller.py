"""
Unified Database Controller for AMRS Preventative Maintenance

This module provides a unified interface for database operations,
supporting both encrypted SQLite (SQLCipher) and standard SQLite databases.
"""

import os
import sys
import logging
from pathlib import Path
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO, format='[DB_CONTROLLER] %(levelname)s - %(message)s')
logger = logging.getLogger("db_controller")

# Thread-local storage for database connections
local_data = threading.local()

# Try to import pysqlcipher3, but fall back to standard sqlite3
SQLCIPHER_AVAILABLE = False
# Check if SQLCipher is explicitly disabled via environment variable
if os.environ.get('DISABLE_SQLCIPHER', '').lower() == 'true':
    logger.info("SQLCipher explicitly disabled via environment variable.")
else:
    try:
        from pysqlcipher3 import dbapi2 as sqlcipher
        # Test that SQLCipher actually works (not just imported)
        test_conn = sqlcipher.connect(':memory:')
        test_conn.execute('PRAGMA key="test"')
        test_conn.execute('CREATE TABLE test (id INTEGER PRIMARY KEY)')
        test_conn.close()
        SQLCIPHER_AVAILABLE = True
        logger.info("SQLCipher support is available and working properly.")
    except (ImportError, Exception) as e:
        SQLCIPHER_AVAILABLE = False
        # Use a cleaner error message that doesn't expose the full exception
        logger.warning("SQLCipher not available or not working correctly. Using standard SQLite only.")

class DatabaseController:
    """
    Unified controller for database operations supporting both
    encrypted and standard SQLite databases.
    """
    
    def __init__(self, db_path=None, encryption_key=None, use_encryption=False):
        """
        Initialize the database controller
        
        Args:
            db_path (str): Path to the SQLite database file
            encryption_key (str): Key for encrypted database
            use_encryption (bool): Whether to use encryption
        """
        # Set default database path
        if db_path is None:
            db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
            os.makedirs(db_dir, exist_ok=True)
            
            # Use custom database filename from environment variable if provided
            db_filename = os.environ.get('DB_FILE', 'maintenance.db')
            db_path = os.path.join(db_dir, db_filename)
            
        self.db_path = db_path
        self.encryption_key = encryption_key
        self.use_encryption = use_encryption and SQLCIPHER_AVAILABLE
        
        # Validate config
        if self.use_encryption and self.encryption_key is None:
            raise ValueError("Encryption key must be provided when use_encryption is True")
            
        logger.info(f"Initialized database controller for {db_path}")
        logger.info(f"Encryption enabled: {self.use_encryption}")
        
        # Create database directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
    def get_connection(self):
        """Get a database connection, creating it if needed"""
        conn_key = f"conn_{self.db_path}"
        
        if not hasattr(local_data, conn_key) or getattr(local_data, conn_key) is None:
            try:
                # Make sure directory exists
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
                
                if self.use_encryption:
                    # Use SQLCipher
                    conn = sqlcipher.connect(self.db_path)
                    conn.execute(f"PRAGMA key = '{self.encryption_key}';")
                    # Verify we can read the database
                    conn.execute("SELECT count(*) FROM sqlite_master;")
                else:
                    # Use standard SQLite
                    conn = sqlite3.connect(self.db_path)
                    
                # Enable row factory for both connection types
                if self.use_encryption:
                    conn.row_factory = sqlcipher.Row
                else:
                    conn.row_factory = sqlite3.Row
                    
                # Store the connection in thread-local storage
                setattr(local_data, conn_key, conn)
                logger.info(f"Created new database connection to {self.db_path}")
                
            except Exception as e:
                logger.error(f"Failed to connect to database at {self.db_path}: {str(e)}")
                # If encryption failed, try to fall back to standard SQLite
                if self.use_encryption:
                    logger.warning("Falling back to standard SQLite due to encryption error")
                    try:
                        # Use standard SQLite as fallback
                        conn = sqlite3.connect(self.db_path)
                        conn.row_factory = sqlite3.Row
                        setattr(local_data, conn_key, conn)
                        # Update the encryption flag for this instance
                        self.use_encryption = False
                        logger.info(f"Created fallback connection to {self.db_path} without encryption")
                    except Exception as inner_e:
                        logger.error(f"Fallback connection also failed: {str(inner_e)}")
                        setattr(local_data, conn_key, None)
                        raise
                else:
                    setattr(local_data, conn_key, None)
                    raise
                
        return getattr(local_data, conn_key)
        
    def close_connection(self):
        """Close the database connection if it exists"""
        conn_key = f"conn_{self.db_path}"
        if hasattr(local_data, conn_key) and getattr(local_data, conn_key) is not None:
            conn = getattr(local_data, conn_key)
            conn.close()
            setattr(local_data, conn_key, None)
            logger.info(f"Closed database connection to {self.db_path}")
            
    def execute_query(self, query, params=()):
        """Execute a query with parameters and commit changes"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor
        except Exception as e:
            conn.rollback()
            logger.error(f"Error executing query: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
            
    def execute_many(self, query, param_list):
        """Execute a query with multiple parameter sets"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.executemany(query, param_list)
            conn.commit()
            return cursor
        except Exception as e:
            conn.rollback()
            logger.error(f"Error executing query many: {str(e)}")
            logger.error(f"Query: {query}")
            raise
            
    def fetch_one(self, query, params=()):
        """Execute a query and fetch one result"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error in fetch_one: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
            
    def fetch_all(self, query, params=()):
        """Execute a query and fetch all results"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error in fetch_all: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
            
    def table_exists(self, table_name):
        """Check if a table exists in the database"""
        cursor = self.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
            (table_name,)
        )
        return cursor is not None
        
    def get_last_sync_time(self):
        """Get the timestamp of the last successful sync"""
        try:
            # Check if sync_info table exists
            if not self.table_exists('sync_info'):
                # Create the table if it doesn't exist
                self.execute_query("""
                CREATE TABLE sync_info (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                return None
                
            # Get the last sync time
            result = self.fetch_one("SELECT value FROM sync_info WHERE key = 'last_sync'")
            if result:
                return result[0]
            return None
        except Exception as e:
            logger.error(f"Error getting last sync time: {str(e)}")
            return None
            
    def update_last_sync_time(self):
        """Update the last sync timestamp"""
        try:
            now = datetime.now(timezone.utc).isoformat()
            
            # Check if the sync_info table exists
            if not self.table_exists('sync_info'):
                # Create the table if it doesn't exist
                self.execute_query("""
                CREATE TABLE sync_info (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
            # Update the last sync time
            self.execute_query("""
            INSERT INTO sync_info (key, value, updated_at)
            VALUES ('last_sync', ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """, (now,))
            
            return True
        except Exception as e:
            logger.error(f"Error updating last sync time: {str(e)}")
            return False
            
    def authenticate_user(self, username, password):
        """Authenticate a user with username and password"""
        try:
            user = self.fetch_one(
                "SELECT id, username, password_hash, is_admin, role_id FROM users WHERE username = ?",
                (username,)
            )
            
            if user and check_password_hash(user['password_hash'], password):
                # Update last login time
                self.execute_query(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                    (user['id'],)
                )
                
                return {
                    'id': user['id'],
                    'username': user['username'],
                    'is_admin': bool(user['is_admin']),
                    'role_id': user['role_id']
                }
            return None
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return None
            
    def create_user(self, username, email, full_name, password, is_admin=False, role_id=None):
        """Create a new user"""
        try:
            # Generate username and email hashes
            username_hash = str(uuid.uuid5(uuid.NAMESPACE_DNS, username))
            email_hash = str(uuid.uuid5(uuid.NAMESPACE_DNS, email))
            
            # Hash the password
            password_hash = generate_password_hash(password)
            
            # Insert the user
            cursor = self.execute_query("""
            INSERT INTO users (
                username, username_hash, email, email_hash, full_name, 
                password_hash, is_admin, role_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                username, username_hash, email, email_hash, full_name,
                password_hash, 1 if is_admin else 0, role_id
            ))
            
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise
            
    def get_pending_sync_count(self):
        """Get count of records pending synchronization"""
        try:
            maintenance_count = 0
            audit_count = 0
            
            # Check if tables exist
            if self.table_exists('maintenance_records'):
                result = self.fetch_one("SELECT COUNT(*) FROM maintenance_records WHERE is_synced = 0")
                if result:
                    maintenance_count = result[0]
                    
            if self.table_exists('audit_task_completions'):
                result = self.fetch_one("SELECT COUNT(*) FROM audit_task_completions WHERE is_synced = 0")
                if result:
                    audit_count = result[0]
                    
            return {
                'maintenance': maintenance_count,
                'audit': audit_count,
                'total': maintenance_count + audit_count
            }
        except Exception as e:
            logger.error(f"Error getting pending sync count: {str(e)}")
            return {'maintenance': 0, 'audit': 0, 'total': 0}

# Create a global instance of the controller for standard SQLite
db_controller = DatabaseController(use_encryption=False)
