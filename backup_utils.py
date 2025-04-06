#!/usr/bin/env python3
"""
Utilities for backing up and restoring maintenance data.
"""

import os
import time
import json
import sqlite3
import shutil
from datetime import datetime
from flask import current_app

def get_backup_dir():
    """Get the directory where backups should be stored"""
    # First check if BACKUP_DIR is configured in Flask app
    if current_app and current_app.config.get('BACKUP_DIR'):
        backup_dir = current_app.config['BACKUP_DIR']
    else:
        # Check if on Render
        if os.environ.get('RENDER'):
            # Use Render's persistent storage
            backup_dir = '/var/data/backups'
        else:
            # Local development - use instance directory
            backup_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'instance',
                'backups'
            )
    
    # Ensure the directory exists
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir

def get_database_path():
    """Get path to the current SQLite database file"""
    if current_app:
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if db_uri.startswith('sqlite:///'):
            # Strip the prefix
            if db_uri.startswith('sqlite:////'):  # Absolute path
                return db_uri[10:]
            else:  # Relative path
                return db_uri[9:]
    
    # Fallback - check if on Render
    if os.environ.get('RENDER'):
        return '/var/data/db/maintenance.db'
    else:
        # Local development
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'instance',
            'maintenance.db'
        )

def create_backup():
    """Create a backup of the database"""
    try:
        # Get the database path
        db_path = get_database_path()
        if not os.path.exists(db_path):
            return False, f"Database file not found at {db_path}"
        
        # Get the backup directory
        backup_dir = get_backup_dir()
        
        # Create a timestamp for the backup file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Create backup metadata
        metadata = {
            'created': datetime.now().isoformat(),
            'source_db': db_path,
            'description': f"Automatic backup - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            'size_bytes': os.path.getsize(db_path),
        }
        
        # Connect to the database to ensure it's valid and check tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        metadata['tables'] = [table[0] for table in tables if table[0] != 'sqlite_sequence']
        
        # Get row counts for each table
        table_counts = {}
        for table in metadata['tables']:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM '{table}'")
                count = cursor.fetchone()[0]
                table_counts[table] = count
            except sqlite3.OperationalError:
                table_counts[table] = "Error counting rows"
        
        metadata['table_counts'] = table_counts
        conn.close()
        
        # Copy the database file
        shutil.copy2(db_path, backup_path)
        
        # Save metadata to a JSON file
        with open(f"{backup_path}.info", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return True, backup_filename
    
    except Exception as e:
        return False, str(e)

def restore_backup(backup_filename):
    """Restore the database from a backup file"""
    try:
        # Get the backup directory
        backup_dir = get_backup_dir()
        backup_path = os.path.join(backup_dir, backup_filename)
        
        if not os.path.exists(backup_path):
            return False, f"Backup file not found: {backup_filename}"
        
        # Get the current database path
        db_path = get_database_path()
        
        # Create a backup of the current database before restoring
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        pre_restore_backup = f"{db_path}.pre_restore_{current_time}"
        
        if os.path.exists(db_path):
            shutil.copy2(db_path, pre_restore_backup)
        
        # Copy the backup file to the database path
        shutil.copy2(backup_path, db_path)
        
        return True, f"Database restored from {backup_filename}. Previous database saved as {os.path.basename(pre_restore_backup)}"
    
    except Exception as e:
        return False, str(e)

def list_backups():
    """List all available backups"""
    try:
        backup_dir = get_backup_dir()
        if not os.path.exists(backup_dir):
            return []
        
        backups = []
        for filename in os.listdir(backup_dir):
            if filename.endswith('.db'):
                file_path = os.path.join(backup_dir, filename)
                info_path = f"{file_path}.info"
                
                # Basic backup info
                backup_info = {
                    'filename': filename,
                    'created': datetime.fromtimestamp(os.path.getctime(file_path)),
                    'size': os.path.getsize(file_path)
                }
                
                # Add additional metadata if available
                if os.path.exists(info_path):
                    try:
                        with open(info_path, 'r') as f:
                            metadata = json.load(f)
                        # Update with more detailed info
                        backup_info.update(metadata)
                    except:
                        pass
                
                backups.append(backup_info)
        
        # Sort backups by creation time (newest first)
        backups.sort(key=lambda x: x['created'] if isinstance(x['created'], str) 
                    else x['created'].isoformat(), reverse=True)
        
        return backups
    except Exception as e:
        print(f"Error listing backups: {str(e)}")
        return []

def delete_backup(backup_filename):
    """Delete a backup file"""
    try:
        backup_dir = get_backup_dir()
        backup_path = os.path.join(backup_dir, backup_filename)
        info_path = f"{backup_path}.info"
        
        if os.path.exists(backup_path):
            os.remove(backup_path)
            
        if os.path.exists(info_path):
            os.remove(info_path)
            
        return True, f"Backup {backup_filename} deleted."
    except Exception as e:
        return False, str(e)
