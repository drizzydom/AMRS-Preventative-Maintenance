"""
Database configuration for the AMRS Maintenance Tracker application.
Handles connection pooling and other database settings.
"""

import os

def configure_database(app):
    """Configure the database connection settings for the application."""
    # Get database URI from environment or use default
    database_uri = os.environ.get(
        'DATABASE_URL', 
        'postgresql://maintenance_tracker_data_user:mbVv4EmuXc0co5A0KcHe57SPhW7Kd0gi@dpg-cvv7vebe5dus73ec3ksg-a/maintenance_tracker_data'
    )
    
    # Basic SQLAlchemy configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Connection pool configuration
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,                # Maximum number of connections to keep
        'pool_recycle': 1800,           # Recycle connections after 30 minutes
        'pool_pre_ping': True,          # Check connections before using them
        'pool_timeout': 30,             # Timeout after 30 seconds when getting connection
        'max_overflow': 5,              # Allow 5 connections beyond pool_size
        'echo': app.debug,              # Log SQL queries in debug mode
        'echo_pool': app.debug,         # Log connection pool events in debug mode
    }
    
    return app
