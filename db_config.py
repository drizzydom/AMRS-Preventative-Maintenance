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
    
    # Get database URL - use the specific PostgreSQL URL if on Render
    if is_render:
        # First check the environment variable
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            print("[DB] WARNING: No DATABASE_URL environment variable found on Render", file=sys.stderr)
            print("[DB] Using the hardcoded PostgreSQL URL as fallback", file=sys.stderr)
            # Use the hardcoded URL as fallback if needed
            database_url = "postgresql://maintenance_tracker_data_user:mbVv4EmuXc0co5A0KcHe57SPhW7Kd0gi@dpg-cvv7vbe5dus73ec3ksg-a/maintenance_tracker_data"
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
        # First check the environment variable
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            print("[DB] WARNING: No DATABASE_URL environment variable found on Render", file=sys.stderr)
            print("[DB] Using the hardcoded PostgreSQL URL as fallback", file=sys.stderr)
            # Use the hardcoded URL as fallback if needed
            database_url = "postgresql://maintenance_tracker_data_user:mbVv4EmuXc0co5A0KcHe57SPhW7Kd0gi@dpg-cvv7vbe5dus73ec3ksg-a/maintenance_tracker_data"
    else:
        # For local development, use SQLite
        database_url = os.environ.get('DATABASE_URL', 'sqlite:///instance/maintenance.db')
    
    # Fix common issue with PostgreSQL URLs from Heroku/Render
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
