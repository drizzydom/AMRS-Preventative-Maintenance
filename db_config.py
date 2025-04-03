import os
import sqlite3
from flask import Flask

def configure_database(app: Flask):
    """Configure database for different environments"""
    
    # For Render deployment
    if os.environ.get('RENDER'):
        # Use Render's mount path environment variable, or fall back to app directory
        if os.environ.get('RENDER_MOUNT_PATH'):
            # Use the mount path specified by Render
            data_dir = os.environ.get('RENDER_MOUNT_PATH')
            print(f"Using Render mount path: {data_dir}")
        else:
            # Fall back to a directory in the project that we can write to
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
            print(f"Using fallback data directory: {data_dir}")
        
        os.makedirs(data_dir, exist_ok=True)
        db_path = os.path.join(data_dir, 'maintenance.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        
        print(f"Using persistent database at {db_path}")
        
        # Print whether the database file exists for debugging
        if os.path.exists(db_path):
            print(f"Database file exists with size: {os.path.getsize(db_path)} bytes")
        else:
            print(f"Database does not exist yet at {db_path}, will be created")
    else:
        # Local development setup
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maintenance.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    return app
