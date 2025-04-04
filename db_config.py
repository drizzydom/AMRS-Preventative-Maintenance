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
            # Render's persistent disk is mounted at /var/data
            # This is where we should store our database file
            data_dir = '/var/data'
            
            # Ensure the directory exists
            print(f"[DB_CONFIG] Using persistent data directory: {data_dir}")
            try:
                os.makedirs(data_dir, exist_ok=True)
                print(f"[DB_CONFIG] Data directory ready: {os.path.exists(data_dir)}")
            except Exception as e:
                print(f"[DB_CONFIG] Error creating data directory: {str(e)}", file=sys.stderr)
            
            # Create the database path
            db_path = os.path.join(data_dir, 'maintenance.db')
            
            # Configure Flask app to use this database
            app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
            
            print(f"[DB_CONFIG] Using persistent database at {db_path}")
            
            # Check database access
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
                    print(f"[DB_CONFIG] Attempt {retry_count}/{MAX_RETRIES} - Error accessing database: {str(e)}", file=sys.stderr)
                    if retry_count < MAX_RETRIES:
                        print(f"[DB_CONFIG] Waiting 3 seconds before retry...")
                        time.sleep(3)
                    else:
                        print(f"[DB_CONFIG] Failed to access database after {MAX_RETRIES} attempts. Will continue anyway - tables will be created if needed.", file=sys.stderr)
        except Exception as e:
            print(f"[DB_CONFIG] Error setting up Render database: {str(e)}", file=sys.stderr)
            # Fallback to a safe configuration
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maintenance.db'
            print(f"[DB_CONFIG] Using fallback database: maintenance.db in current working directory", file=sys.stderr)
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
            print(f"[DB_CONFIG] Error setting up local database: {str(e)}", file=sys.stderr)
            # Fallback to a very basic configuration
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maintenance.db'
            print(f"[DB_CONFIG] Using fallback database: maintenance.db in current working directory", file=sys.stderr)
    
    # Disable SQLAlchemy event system - improves performance
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    print("[DB_CONFIG] Database configuration complete.")
    return app
