#!/usr/bin/env python3
"""
Migration module to add color column to audit_tasks table.
"""
import os
import logging
import sqlite3

logger = logging.getLogger(__name__)

def migrate(db_connection=None):
    """
    Add color column to audit_tasks table if it doesn't exist.
    
    Args:
        db_connection: SQLite database connection (optional)
        
    Returns:
        bool: True if successful, False if failed
    """
    logger.info("Starting audit_task color column migration")
    
    try:
        # If no connection provided, create one
        connection_created = False
        if db_connection is None:
            appdata_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
            db_dir = os.path.join(appdata_dir, 'amrs-preventative-maintenance', 'AMRS-Maintenance-Tracker')
            db_path = os.path.join(db_dir, 'amrs_maintenance.db')
            
            if not os.path.exists(db_path):
                logger.error(f"Database not found at {db_path}")
                return False
                
            db_connection = sqlite3.connect(db_path)
            connection_created = True
            logger.info(f"Connected to database at {db_path}")
            
        cursor = db_connection.cursor()
        
        # Check if audit_tasks table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_tasks';")
        if not cursor.fetchone():
            logger.info("audit_tasks table doesn't exist, skipping migration")
            if connection_created:
                db_connection.close()
            return True
            
        # Check if color column already exists
        cursor.execute("PRAGMA table_info(audit_tasks);")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'color' not in columns:
            logger.info("Adding color column to audit_tasks table")
            # For older SQLite versions that don't support IF NOT EXISTS in ALTER TABLE
            cursor.execute("ALTER TABLE audit_tasks ADD COLUMN color TEXT DEFAULT '#3498db';")
            db_connection.commit()
            logger.info("Color column added successfully")
        else:
            logger.info("Color column already exists in audit_tasks table")
            
        if connection_created:
            db_connection.close()
            
        return True
        
    except Exception as e:
        logger.error(f"Error in audit_task color column migration: {e}")
        return False

# If run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = migrate()
    print(f"Migration {'successful' if result else 'failed'}")
