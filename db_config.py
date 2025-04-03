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
        
        # Check if we need to initialize the database
        if not os.path.exists(db_path):
            print(f"Database not found at {db_path}, will be created")
            # But we don't want to lose data by recreating tables
            # The actual schema creation is done in the app.py file
    else:
        # Local development setup
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maintenance.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    return app
