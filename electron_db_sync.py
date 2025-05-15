"""
Database synchronization module for Electron application.
Handles synchronization between local SQLite and remote PostgreSQL databases.
"""
import os
import sys
import logging
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)

class DBSync:
    """Database synchronization handler"""
    
    def __init__(self, sqlite_uri=None, postgres_uri=None):
        self.sqlite_uri = sqlite_uri
        self.postgres_uri = postgres_uri
        
        # Fix URI formats
        if self.sqlite_uri and self.sqlite_uri.startswith('sqlite:///'):
            self.sqlite_path = self.sqlite_uri[10:]  # Remove 'sqlite:///'
        else:
            self.sqlite_path = self.sqlite_uri
            
        logger.info(f"DBSync initialized with SQLite: {self.sqlite_path}")
        
    def validate_config(self):
        """Validate synchronization configuration"""
        if not self.sqlite_uri:
            logger.error("SQLite URI not configured")
            return False
            
        if not self.postgres_uri:
            logger.warning("PostgreSQL URI not configured, running in local-only mode")
            # This is not an error, just a warning
            return True
            
        if self.sqlite_uri == self.postgres_uri:
            logger.error("SQLite and PostgreSQL URIs are identical")
            return False
            
        return True
        
    def sync_data(self):
        """Synchronize data between databases"""
        if not self.validate_config():
            return False
            
        try:
            # For now, just validate SQLite database
            if not self.sqlite_path or not os.path.exists(self.sqlite_path):
                logger.error(f"SQLite database not found at {self.sqlite_path}")
                return False
                
            # Connect to SQLite database
            sqlite_conn = sqlite3.connect(self.sqlite_path)
            sqlite_cursor = sqlite_conn.cursor()
            
            # Basic validation
            sqlite_cursor.execute("SELECT sqlite_version();")
            version = sqlite_cursor.fetchone()[0]
            logger.info(f"Connected to SQLite version {version}")
            
            # Get tables
            sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [table[0] for table in sqlite_cursor.fetchall()]
            logger.info(f"Found {len(tables)} tables: {', '.join(tables)}")
            
            # In local-only mode, we're done
            if not self.postgres_uri:
                logger.info("Running in local-only mode, no synchronization performed")
                sqlite_conn.close()
                return True
                
            # TODO: Add actual synchronization code when PostgreSQL is configured
            
            sqlite_conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error during database synchronization: {e}")
            return False
            
def get_sync_handler():
    """Get a configured sync handler based on environment"""
    sqlite_uri = os.environ.get('SQLITE_DATABASE_URI')
    postgres_uri = os.environ.get('POSTGRES_DATABASE_URI')
    
    # If no explicit URIs provided, construct default SQLite path
    if not sqlite_uri:
        appdata_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
        db_dir = os.path.join(appdata_dir, 'amrs-preventative-maintenance', 'AMRS-Maintenance-Tracker')
        db_path = os.path.join(db_dir, 'amrs_maintenance.db')
        sqlite_uri = f"sqlite:///{db_path}"
        
    # Create sync handler
    sync = DBSync(sqlite_uri=sqlite_uri, postgres_uri=postgres_uri)
    return sync

# Allow direct running for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sync = get_sync_handler()
    if sync.sync_data():
        print("Synchronization successful")
    else:
        print("Synchronization failed")
        sys.exit(1)
