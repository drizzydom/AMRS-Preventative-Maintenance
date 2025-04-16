"""
Database configuration for the AMRS Preventative Maintenance application
"""
import os
import sys

def configure_database(app):
    """
    Configure the database connection for the Flask application
    """
    # Check if running on Render
    is_render = os.environ.get('RENDER', '') == 'true'
    
    # Get database URL depending on environment
    if is_render:
        # For Render deployment use the DATABASE_URL provided by Render
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            print("[DB] ERROR: No DATABASE_URL provided by Render. This is required.", file=sys.stderr)
            print("[DB] Falling back to in-memory SQLite as a last resort", file=sys.stderr)
            database_url = 'sqlite:///:memory:'
    else:
        # For local development, use SQLite
        database_url = os.environ.get('DATABASE_URL', 'sqlite:///instance/maintenance.db')
    
    # Fix common issue with PostgreSQL URLs from Heroku/Render
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    print(f"[DB] Configuring database with URL: {database_url}")
    
    # Configure SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Additional PostgreSQL-specific settings
    if 'postgresql' in database_url:
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'pool_size': 10,
            'max_overflow': 20,
            'connect_args': {
                'connect_timeout': 10
            }
        }
    
    # Initialize the app with the database
    from models import db
    db.init_app(app)
    
    return app

# Alias for configure_database for backwards compatibility
configure_db = configure_database

def get_db_engine():
    """
    Get a SQLAlchemy engine for direct database operations
    """
    from sqlalchemy import create_engine
    
    # Check if running on Render
    is_render = os.environ.get('RENDER', '') == 'true'
    
    # Get database URL - use the specific PostgreSQL URL if on Render
    if is_render:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("[DB] ERROR: No DATABASE_URL provided by Render. This is required.", file=sys.stderr)
            print("[DB] Falling back to in-memory SQLite as a last resort", file=sys.stderr)
            database_url = 'sqlite:///:memory:'
    else:
        # For local development, use SQLite
        database_url = os.environ.get('DATABASE_URL', 'sqlite:///instance/maintenance.db')
    
    # Fix common issue with PostgreSQL URLs
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
    print(f"[DB] Creating engine with URL: {database_url}")
    
    # Configure engine options based on database type
    engine_options = {
        'pool_pre_ping': True,
        'pool_recycle': 300
    }
    
    if 'postgresql' in database_url:
        engine_options.update({
            'pool_size': 10,
            'max_overflow': 20,
            'connect_args': {
                'connect_timeout': 10
            }
        })
    
    # Create and return engine
    return create_engine(database_url, **engine_options)
