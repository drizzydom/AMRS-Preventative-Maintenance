import os
import sqlite3
from flask import Flask
import time
import sys

def configure_database(app: Flask):
    """Configure database for different environments"""
    
    print("[DB_CONFIG] Configuring database connection...")
    
    # For Render deployment
    if os.environ.get('RENDER'):
        try:
            # Use Render's persistent disk for database storage
            # /var/data is the persistent storage on Render
            data_dir = '/var/data'
            
            # Ensure the directory exists
            if not os.path.exists(data_dir):
                print(f"[DB_CONFIG] Creating data directory: {data_dir}")
                os.makedirs(data_dir, exist_ok=True)
            
            # Check if directory is writable
            if os.access(data_dir, os.W_OK):
                print(f"[DB_CONFIG] Using Render persistent storage at: {data_dir}")
                
                # Create a dedicated directory for database files
                db_dir = os.path.join(data_dir, 'db')
                os.makedirs(db_dir, exist_ok=True)
                
                db_path = os.path.join(db_dir, 'maintenance.db')
                app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
                print(f"[DB_CONFIG] Database will be stored at: {db_path}")
                
                # Also create directory for backups
                backup_dir = os.path.join(data_dir, 'backups')
                os.makedirs(backup_dir, exist_ok=True)
                app.config['BACKUP_DIR'] = backup_dir
                print(f"[DB_CONFIG] Backups will be stored at: {backup_dir}")
            else:
                print(f"[DB_CONFIG] Warning: {data_dir} is not writable.")
                # Fallback to project directory
                db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'maintenance.db')
                app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
                print(f"[DB_CONFIG] Using fallback database at: {db_path}")
        except Exception as e:
            print(f"[DB_CONFIG] Error setting up database: {str(e)}")
            # Fallback to project directory as a last resort
            try:
                db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'maintenance.db')
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
                print(f"[DB_CONFIG] Using fallback database at: {db_path}")
            except:
                # Last resort - in-memory database (non-persistent)
                app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
                print("[DB_CONFIG] WARNING: Using non-persistent in-memory database!")
    else:
        # Local development setup - store in project directory
        try:
            instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
            print(f"[DB_CONFIG] Using local instance path: {instance_path}")
            os.makedirs(instance_path, exist_ok=True)
            
            # Create database directory
            db_path = os.path.join(instance_path, 'maintenance.db')
            app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
            print(f"[DB_CONFIG] Using local database at: {db_path}")
            
            # Create backups directory
            backup_dir = os.path.join(instance_path, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            app.config['BACKUP_DIR'] = backup_dir
            print(f"[DB_CONFIG] Using local backups at: {backup_dir}")
        except Exception as e:
            print(f"[DB_CONFIG] Error setting up local database: {str(e)}")
            # Fallback to a very basic configuration
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maintenance.db'
            print(f"[DB_CONFIG] Using fallback database: maintenance.db in current directory")
    
    # Disable SQLAlchemy event system - improves performance
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Set up connection pooling - good for SQLite
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,  # Check connections before using them
        'pool_recycle': 280,    # Recycle connections every ~4.5 minutes
    }
    
    print("[DB_CONFIG] Database configuration complete.")
    return app
