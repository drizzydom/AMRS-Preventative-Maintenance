"""
Offline Adapter Module for Electron App

This module provides the necessary adapter functionality to switch between online (PostgreSQL)
and offline (SQLite) modes, handling database operations and synchronization.
"""

import os
import sys
import logging
from datetime import datetime
import json
from pathlib import Path
import threading
import time
import queue

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global state
sync_thread = None
sync_queue = queue.Queue()
is_syncing = False
last_sync_time = None
sync_interval = 300  # 5 minutes default

def is_electron():
    """Detect if running in Electron environment"""
    return os.environ.get('ELECTRON_RUN_AS_NODE') is not None or os.environ.get('AMRS_ELECTRON') == '1' or os.environ.get('ELECTRON') == '1'

def is_online():
    """Check if the application can connect to the PostgreSQL database"""
    if not is_electron():
        return True  # Always online in web mode
    
    try:
        import requests
        # Try to connect to a reliable internet check service
        response = requests.get('https://www.google.com', timeout=5)
        return response.status_code == 200
    except:
        # If any exception occurs, assume offline
        return False

def get_db_session():
    """Get the appropriate SQLAlchemy session based on current mode"""
    from models import db
    return db.session

def setup_sqlite_database():
    """Ensure SQLite database is set up correctly"""
    if not is_electron():
        return True  # Not needed in web mode
    
    try:
        from electron_db_setup import create_database
        from electron_config import get_database_uri
        
        db_uri = get_database_uri()
        create_database(db_uri)
        return True
    except Exception as e:
        logger.error(f"Error setting up SQLite database: {e}")
        return False

def schedule_sync(immediate=False):
    """Schedule a database synchronization"""
    if not is_electron():
        return False  # Not needed in web mode
    
    global sync_queue
    sync_queue.put(immediate)
    return True

def _sync_worker():
    """Background worker that handles database synchronization"""
    global is_syncing, last_sync_time, sync_interval
    
    logger.info("Sync worker thread started")
    
    while True:
        try:
            # Wait for a sync request or timeout
            immediate = False
            try:
                immediate = sync_queue.get(timeout=sync_interval)
            except queue.Empty:
                # Timeout occurred, check if we should sync
                pass
            
            # Skip sync if not online unless immediate sync was requested
            if not is_online() and not immediate:
                logger.info("Skipping sync - offline mode")
                continue
                
            # Check if enough time has passed since last sync
            current_time = time.time()
            if last_sync_time is not None and not immediate:
                elapsed = current_time - last_sync_time
                if elapsed < sync_interval:
                    logger.info(f"Skipping sync - last sync was {elapsed:.0f} seconds ago")
                    continue
            
            # Perform sync
            is_syncing = True
            logger.info("Starting database synchronization")
            
            from electron_db_sync import sync_data, get_database_connections
            
            # Get database sessions
            sqlite_session, postgres_session = get_database_connections()
            
            if not sqlite_session or not postgres_session:
                logger.error("Failed to establish database connections for sync")
                is_syncing = False
                continue
            
            # Determine sync direction based on which is more recent
            # For simplicity, we'll sync from PostgreSQL to SQLite by default
            direction = "to_sqlite"
            
            # Perform the sync
            success = sync_data(sqlite_session, postgres_session, direction=direction)
            
            if success:
                logger.info("Database synchronization completed successfully")
                last_sync_time = current_time
            else:
                logger.error("Database synchronization failed")
            
            is_syncing = False
                
        except Exception as e:
            logger.error(f"Error in sync worker: {e}")
            is_syncing = False
            # Sleep a bit before trying again to avoid tight loops on errors
            time.sleep(10)

def start_sync_service():
    """Start the background synchronization service"""
    global sync_thread
    
    if not is_electron():
        return False  # Not needed in web mode
    
    if sync_thread is not None and sync_thread.is_alive():
        return True  # Already running
    
    # Start sync worker thread
    sync_thread = threading.Thread(target=_sync_worker, daemon=True)
    sync_thread.start()
    
    logger.info("Database sync service started")
    return True

def get_sync_status():
    """Get the current synchronization status"""
    return {
        "is_syncing": is_syncing,
        "last_sync": last_sync_time,
        "is_online": is_online(),
        "mode": "electron" if is_electron() else "web"
    }

def initial_setup():
    """Perform initial setup for offline mode"""
    if not is_electron():
        return True  # Not needed in web mode
    
    # Ensure SQLite database is set up
    if not setup_sqlite_database():
        logger.error("Failed to set up SQLite database")
        return False
    
    # Start sync service
    if not start_sync_service():
        logger.error("Failed to start sync service")
        return False
    
    # Perform initial sync if online
    if is_online():
        schedule_sync(immediate=True)
    
    logger.info("Offline adapter initial setup completed")
    return True

# Initialize on import
def initialize():
    """Initialize the offline adapter"""
    if is_electron():
        logger.info("Initializing offline adapter for Electron mode")
        return initial_setup()
    return True