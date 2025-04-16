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
    
    # On Render, check for all possible environment variable names for database
    if is_render:
        # Check for internal Render PostgreSQL - use all possible env var names
        database_url = os.environ.get('DATABASE_URL') or os.environ.get('RENDER_DATABASE_URL') or os.environ.get('INTERNAL_DATABASE_URL')
        
        # If Render PostgreSQL not found, use the external database URL if available
        if not database_url:
            # Check for common PostgreSQL env vars
            print("[DB] Checking for PostgreSQL environment variables...")
            postgres_vars = ['POSTGRES_URL', 'PG_URL', 'POSTGRESQL_URL']
            for var in postgres_vars:
                if os.environ.get(var):
                    database_url = os.environ.get(var)
                    print(f"[DB] Using {var} for database connection")
                    break
                    
        # If still no database URL found, log available env vars for debugging
        if not database_url:
            print("[DB] No database URL found in environment variables. Available env vars:")
            for key in sorted(os.environ.keys()):
                if 'DB' in key.upper() or 'SQL' in key.upper() or 'DATABASE' in key.upper() or 'POSTGRES' in key.upper():
                    print(f"  - {key}")
            
            print("[DB] Falling back to in-memory SQLite as a last resort")
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
            'max_overflow': 20
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
    
    # Get database URL depending on environment
    if is_render:
        # Check for internal Render PostgreSQL
        database_url = os.environ.get('DATABASE_URL') or os.environ.get('RENDER_DATABASE_URL') or os.environ.get('INTERNAL_DATABASE_URL')
        
        if not database_url:
            # Check other common PostgreSQL env vars
            postgres_vars = ['POSTGRES_URL', 'PG_URL', 'POSTGRESQL_URL']
            for var in postgres_vars:
                if os.environ.get(var):
                    database_url = os.environ.get(var)
                    break
                    
        if not database_url:
            print("[DB] No database URL found for engine creation. Using in-memory SQLite.")
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

def execute_query(query, params=None):
    """
    Execute a SQL query using SQLAlchemy 2.0 compatible methods
    
    Args:
        query: SQL query string
        params: Optional parameters for the query
        
    Returns:
        Query results
    """
    from sqlalchemy import text
    from models import db
    
    try:
        with db.engine.connect() as conn:
            if params:
                result = conn.execute(text(query), params)
            else:
                result = conn.execute(text(query))
            return result
    except Exception as e:
        print(f"[DB] Query execution error: {e}")
        raise
