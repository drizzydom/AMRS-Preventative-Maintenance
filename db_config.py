"""
Database configuration for different environments
"""
import os
import sys
from flask import Flask
from sqlalchemy import create_engine

def configure_database(app):
    """
    Configure the database connection based on environment
    
    Args:
        app: Flask application instance
        
    Returns:
        Configured Flask application
    """
    # Check if running on Render
    is_render = os.environ.get('RENDER', '') == 'true'
    
    # Get database URL from environment or use default
    database_url = os.environ.get('DATABASE_URL')
    
    # Force PostgreSQL on Render - never fall back to SQLite
    if is_render and not database_url:
        print("[DB] ERROR: No DATABASE_URL provided in Render environment", file=sys.stderr)
        print("[DB] Please set the DATABASE_URL environment variable in your Render dashboard", file=sys.stderr)
        database_url = "postgresql://postgres:postgres@localhost/postgres"  # This will fail but with a clearer error
    elif not database_url:
        # Local development can use SQLite
        print("[DB] No DATABASE_URL found, using SQLite for local development")
        
        # Determine if we're running in a writable directory
        instance_path = os.path.join(os.getcwd(), 'instance')
        try:
            os.makedirs(instance_path, exist_ok=True)
            database_url = f'sqlite:///{instance_path}/maintenance.db'
        except PermissionError:
            print("[DB] WARNING: Cannot create instance directory, using in-memory SQLite")
            database_url = 'sqlite:///:memory:'
    
    # Handle old-style Heroku/Render PostgreSQL URL format
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        print(f"[DB] Converted postgres:// URL to postgresql:// format")
    
    print(f"[DB] Configuring database with URL: {database_url}")
    
    # Configure SQLAlchemy settings
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Additional PostgreSQL connection settings
    if 'postgresql' in database_url:
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'connect_args': {
                'connect_timeout': 10
            }
        }
    
    # Initialize the database with the app
    from models import db
    db.init_app(app)
    
    return app

def get_db_engine():
    """
    Create and return a SQLAlchemy engine based on environment
    
    Returns:
        SQLAlchemy engine
    """
    # Get database URL from environment or use default
    database_url = os.environ.get('DATABASE_URL')
    
    # Check if running on Render
    is_render = os.environ.get('RENDER', '') == 'true'
    
    if is_render and not database_url:
        print("[DB] ERROR: No DATABASE_URL provided in Render environment", file=sys.stderr)
        raise ValueError("DATABASE_URL environment variable must be set on Render")
    elif not database_url:
        print("[DB] Using SQLite for local development")
        instance_path = os.path.join(os.getcwd(), 'instance')
        os.makedirs(instance_path, exist_ok=True)
        database_url = f'sqlite:///{instance_path}/maintenance.db'
    
    # Handle potential Heroku/Render PostgreSQL URL format issue
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    # Create engine with appropriate parameters
    connect_args = {}
    engine_args = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    if 'postgresql' in database_url:
        connect_args = {
            'connect_timeout': 10
        }
        engine_args['connect_args'] = connect_args
        
    return create_engine(
        database_url,
        **engine_args
    )
