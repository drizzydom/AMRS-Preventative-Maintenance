import os
import sqlite3
from flask import Flask

def configure_database(app: Flask):
    """Configure database for different environments"""
    
    # For Render deployment
    if os.environ.get('RENDER'):
        # Use Render's persistent disk instead of /tmp
        # Render provides /var/data as persistent storage
        os.makedirs('/var/data', exist_ok=True)
        db_path = '/var/data/maintenance.db'
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

    # Make sure SQLAlchemy doesn't create tables automatically
    # This prevents the database from being recreated on startup
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    return app
