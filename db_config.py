"""
Database configuration for the AMRS Preventative Maintenance application
"""
import os

def configure_database(app):
    """
    Configure the database connection for the Flask application
    """
    # Get database URL from environment or use SQLite default
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///instance/maintenance.db')
    
    # Fix common issue with PostgreSQL URLs from Heroku/Render
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    print(f"[DB] Configuring database with URL: {database_url}")
    
    # Configure SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
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
    
    # Get database URL from environment or use SQLite default
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///instance/maintenance.db')
    
    # Fix common issue with PostgreSQL URLs from Heroku/Render
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    # Create and return engine
    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=300
    )
