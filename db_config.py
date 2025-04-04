import os
import sqlite3
from flask import Flask
import time

def configure_database(app: Flask):
    """Configure database for different environments"""
    
    # For Render deployment
    if os.environ.get('RENDER'):
        # Render's persistent disk is mounted at /var/data
        # This is where we should store our database file
        data_dir = '/var/data'
        
        # Ensure the directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Create the database path
        db_path = os.path.join(data_dir, 'maintenance.db')
        
        # Configure Flask app to use this database
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        
        print(f"[DATABASE] Using persistent database at {db_path}")
        
        # Check database access
        MAX_RETRIES = 5
        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                # Try to connect to and access the database
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                conn.close()
                print(f"[DATABASE] Successfully connected to database. Found {len(tables)} tables.")
                break
            except Exception as e:
                retry_count += 1
                print(f"[DATABASE] Attempt {retry_count}/{MAX_RETRIES} - Error accessing database: {str(e)}")
                if retry_count < MAX_RETRIES:
                    print(f"[DATABASE] Waiting 2 seconds before retry...")
                    time.sleep(2)
                else:
                    print(f"[DATABASE] Failed to access database after {MAX_RETRIES} attempts.")
                    # Continue anyway - tables will be created if needed
    else:
        # Local development setup - store in project directory
        instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
        os.makedirs(instance_path, exist_ok=True)
        db_path = os.path.join(instance_path, 'maintenance.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        print(f"[DATABASE] Using local database at {db_path}")
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    return app
