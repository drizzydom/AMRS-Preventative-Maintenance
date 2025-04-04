#!/usr/bin/env python3
"""
Utilities for backing up and restoring maintenance data.
"""

import os
import shutil
import sqlite3
import datetime
import time
import json
from flask import current_app

def get_db_path():
    """Get the path to the current database file"""
    if os.environ.get('RENDER'):
        return os.path.join('/var/data', 'maintenance.db')
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'maintenance.db')

def get_backup_dir():
    """Get the directory where backups should be stored"""
    if os.environ.get('RENDER'):
        backup_dir = os.path.join('/var/data', 'backups')
    else:
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'backups')
    
    # Create the directory if it doesn't exist
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir

def create_backup():
    """Create a backup of the current database"""
    try:
        db_path = get_db_path()
        if not os.path.exists(db_path):
            return False, "Database file not found"
        
        # Create a timestamp for the backup filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.db"
        backup_path = os.path.join(get_backup_dir(), backup_filename)
        
        # Test database connection before backup
        try:
            conn = sqlite3.connect(db_path)
            conn.close()
        except Exception as e:
            return False, f"Database access error before backup: {str(e)}"
        
        # Create the backup
        shutil.copy2(db_path, backup_path)
        
        # Verify backup file exists and has data
        if not os.path.exists(backup_path) or os.path.getsize(backup_path) == 0:
            return False, "Backup file creation failed or file is empty"
        
        # Create an info file with metadata about the backup
        info = {
            'created': datetime.datetime.now().isoformat(),
            'source_db': db_path,
            'backup_path': backup_path,
            'size_bytes': os.path.getsize(backup_path)
        }
        
        with open(f"{backup_path}.info", 'w') as f:
            json.dump(info, f, indent=2)
            
        return True, backup_filename
    except Exception as e:
        return False, f"Backup error: {str(e)}"

def restore_backup(backup_filename):
    """Restore database from a backup file"""
    try:
        backup_path = os.path.join(get_backup_dir(), backup_filename)
        db_path = get_db_path()
        
        if not os.path.exists(backup_path):
            return False, "Backup file not found"
        
        # Create a backup of the current database before restoring
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pre_restore_backup = f"pre_restore_{timestamp}.db"
        pre_restore_path = os.path.join(get_backup_dir(), pre_restore_backup)
        
        if os.path.exists(db_path):
            shutil.copy2(db_path, pre_restore_path)
        
        # Restore the backup
        shutil.copy2(backup_path, db_path)
        
        # Verify restore succeeded
        if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
            # If restore failed, try to recover from pre-restore backup
            if os.path.exists(pre_restore_path):
                shutil.copy2(pre_restore_path, db_path)
            return False, "Restore failed - database file is missing or empty"
            
        # Test the restored database
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            
            if len(tables) == 0:
                # No tables found, restore from pre-restore backup
                if os.path.exists(pre_restore_path):
                    shutil.copy2(pre_restore_path, db_path)
                return False, "Restored database contains no tables"
        except Exception as e:
            # Database error, restore from pre-restore backup
            if os.path.exists(pre_restore_path):
                shutil.copy2(pre_restore_path, db_path)
            return False, f"Error accessing restored database: {str(e)}"
        
        return True, f"Restored from {backup_filename}"
    except Exception as e:
        return False, f"Restore error: {str(e)}"

def list_backups():
    """List all available database backups with metadata"""
    try:
        backup_dir = get_backup_dir()
        backups = []
        
        for filename in os.listdir(backup_dir):
            if filename.endswith('.db'):
                backup_path = os.path.join(backup_dir, filename)
                info_path = f"{backup_path}.info"
                
                # Get file information
                size_bytes = os.path.getsize(backup_path)
                created = datetime.datetime.fromtimestamp(os.path.getctime(backup_path))
                
                # Get additional metadata if available
                info = {}
                if os.path.exists(info_path):
                    try:
                        with open(info_path, 'r') as f:
                            info = json.load(f)
                    except:
                        pass
                
                # Format size for display
                size = _format_size(size_bytes)
                
                backups.append({
                    'filename': filename,
                    'created': info.get('created', created.isoformat()),
                    'size': size,
                    'size_bytes': size_bytes
                })
        
        # Sort backups by creation time (newest first)
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups
    except Exception as e:
        print(f"Error listing backups: {str(e)}")
        return []

def _format_size(size_bytes):
    """Format file size in a human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
