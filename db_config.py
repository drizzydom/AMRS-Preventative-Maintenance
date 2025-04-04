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
            # Try multiple possible data directories
            possible_paths = [
                '/var/data',                      # Standard Render persistent storage
                '/tmp',                           # Fallback to temp directory
                os.path.dirname(os.path.abspath(__file__)),  # Project directory
                os.getcwd()                       # Current working directory
            ]
            
            db_path = None
            
            for path in possible_paths:
                try:
                    print(f"[DB_CONFIG] Trying path: {path}")
                    # Check if directory exists and is writable
                    if os.path.exists(path) and os.access(path, os.W_OK):
                        # Try to create a test file to verify write permissions
                        test_file = os.path.join(path, 'db_test_file')
                        with open(test_file, 'w') as f:
                            f.write('test')
                        os.remove(test_file)
                        
                        db_path = os.path.join(path, 'maintenance.db')
                        print(f"[DB_CONFIG] Found writable directory: {path}")
                        break
                    else:
                        print(f"[DB_CONFIG] Directory not writable: {path}")
                except Exception as e:
                    print(f"[DB_CONFIG] Error with path {path}: {str(e)}")
                    continue
                    
            if db_path is None:
                print("[DB_CONFIG] No writable directory found. Using in-memory database as fallback.")
                db_path = ':memory:'
                
            # Configure Flask app to use this database
            app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
            
            print(f"[DB_CONFIG] Using database at: {db_path}")
            
            # Check database access
            if db_path != ':memory:':
                MAX_RETRIES = 5
                retry_count = 0
                while retry_count < MAX_RETRIES:
                    try:
                        # Try to connect to and access the database
                        print(f"[DB_CONFIG] Testing database connection (attempt {retry_count+1}/{MAX_RETRIES})...")
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
                        tables = cursor.fetchall()
                        conn.close()
                        print(f"[DB_CONFIG] Successfully connected to database. Found {len(tables)} tables.")
                        break
                    except Exception as e:
                        retry_count += 1
                        print(f"[DB_CONFIG] Attempt {retry_count}/{MAX_RETRIES} - Error accessing database: {str(e)}")
                        if retry_count < MAX_RETRIES:
                            print(f"[DB_CONFIG] Waiting 3 seconds before retry...")
                            time.sleep(3)
                        else:
                            print(f"[DB_CONFIG] Failed to access database after {MAX_RETRIES} attempts.")
                            print(f"[DB_CONFIG] Will create one when tables are created.")
            
        except Exception as e:
            print(f"[DB_CONFIG] Error setting up database: {str(e)}")
            # Fallback to in-memory database as a last resort
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
            print(f"[DB_CONFIG] Using in-memory database as fallback")
    else:
        # Local development setup - store in project directory
        try:
            instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
            print(f"[DB_CONFIG] Using local instance path: {instance_path}")
            os.makedirs(instance_path, exist_ok=True)
            db_path = os.path.join(instance_path, 'maintenance.db')
            app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
            print(f"[DB_CONFIG] Using local database at {db_path}")
        except Exception as e:
            print(f"[DB_CONFIG] Error setting up local database: {str(e)}")
            # Fallback to a very basic configuration
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maintenance.db'
            print(f"[DB_CONFIG] Using fallback database: maintenance.db in current directory")
    
    # Disable SQLAlchemy event system - improves performance
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    print("[DB_CONFIG] Database configuration complete.")
    return app
