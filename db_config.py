import os
import sqlite3
from flask import Flask

def configure_database(app: Flask):
    """Configure database for different environments"""
    
    # For Render deployment
    if os.environ.get('RENDER'):
        # Use the /tmp directory for SQLite on Render
        db_path = '/tmp/maintenance.db'
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        
        # Check if we need to initialize the database
        if not os.path.exists(db_path):
            print(f"Database not found at {db_path}, will be created")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    else:
        # Local development setup
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maintenance.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    return app
