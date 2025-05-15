"""
SQLite Database Setup for Electron App

This module handles SQLite database initialization and schema migration for the Electron app.
"""

import os
import sys
import logging
from pathlib import Path
import importlib.util
import sqlite3
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_electron():
    """Detect if running in Electron environment"""
    return os.environ.get('ELECTRON_RUN_AS_NODE') is not None or os.environ.get('AMRS_ELECTRON') == '1' or os.environ.get('ELECTRON') == '1'

def get_app_dir():
    """Get the application directory for storing data"""
    try:
        from electron_config import get_app_dir
        return get_app_dir()
    except ImportError:
        # Fallback to default location
        if sys.platform == 'win32':
            app_dir = Path(os.environ.get('APPDATA', '')) / 'AMRS-Maintenance-Tracker'
        elif sys.platform == 'darwin':
            app_dir = Path.home() / 'Library' / 'Application Support' / 'AMRS-Maintenance-Tracker'
        else:  # Linux and others
            app_dir = Path.home() / '.amrs-maintenance-tracker'
        
        # Create directory if it doesn't exist
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir

def get_database_path():
    """Get the SQLite database file path"""
    app_dir = get_app_dir()
    return app_dir / 'amrs_maintenance.db'

def setup_sqlite_database():
    """Initialize or migrate the SQLite database"""
    if not is_electron():
        logger.warning("Not running in Electron mode, skipping SQLite setup")
        return False
    
    db_path = get_database_path()
    logger.info(f"Setting up SQLite database at: {db_path}")
    
    # Check if database exists
    if db_path.exists():
        logger.info("Database already exists, checking for migration needs")
        return migrate_database(db_path)
    else:
        logger.info("Database does not exist, creating new database")
        return create_database(db_path)

def create_database(db_path):
    """Create a new SQLite database with all required tables"""
    try:
        # Create the database file and connection
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create tables based on SQLAlchemy models
        from electron_db_setup import create_database
        from electron_config import get_database_uri
        
        # Use the SQLAlchemy ORM to create all tables
        create_database(get_database_uri())
        
        # Record the database version
        cursor.execute('PRAGMA user_version = 1')
        
        conn.commit()
        conn.close()
        
        logger.info("Successfully created SQLite database")
        return True
        
    except Exception as e:
        logger.error(f"Error creating SQLite database: {e}")
        return False

def migrate_database(db_path):
    """Check and apply migrations to an existing SQLite database"""
    try:
        # Connect to the database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get current database version
        cursor.execute('PRAGMA user_version')
        current_version = cursor.fetchone()[0]
        logger.info(f"Current database version: {current_version}")
        
        # Run auto-migration using the SQLAlchemy models
        from auto_migrate import run_auto_migration
        from flask import Flask
        from models import db
        
        # Create a minimal Flask app
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)
        
        with app.app_context():
            run_auto_migration(app, db)
        
        # Update database version
        cursor.execute('PRAGMA user_version = 2')
        
        conn.commit()
        conn.close()
        
        logger.info("Successfully migrated SQLite database")
        return True
        
    except Exception as e:
        logger.error(f"Error migrating SQLite database: {e}")
        return False

def backup_database():
    """Create a backup of the current database"""
    db_path = get_database_path()
    if not db_path.exists():
        logger.warning("No database to backup")
        return False
    
    try:
        # Create backups directory
        backup_dir = get_app_dir() / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_dir / f"amrs_maintenance_{timestamp}.db"
        
        # Copy the database file
        import shutil
        shutil.copy2(db_path, backup_path)
        
        logger.info(f"Database backup created at: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Error backing up database: {e}")
        return False

if __name__ == "__main__":
    setup_sqlite_database()