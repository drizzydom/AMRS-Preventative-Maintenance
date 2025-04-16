"""
Database configuration for different environments
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from models import db

def configure_db(app):
    """
    Configure the database connection based on environment
    
    Args:
        app: Flask application instance
        
    Returns:
        Configured Flask application
    """
    # Get database URL from environment or use default
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///instance/maintenance.db')
    
    # Handle potential Heroku/Render PostgreSQL URL format issue
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database with the app
    db.init_app(app)
    
    return app

def get_db_engine():
    """
    Create and return a SQLAlchemy engine based on environment
    
    Returns:
        SQLAlchemy engine
    """
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///instance/maintenance.db')
    
    # Handle potential Heroku/Render PostgreSQL URL format issue
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    # Create engine with appropriate parameters for PostgreSQL
    connect_args = {}
    if 'postgresql' in database_url:
        connect_args = {
            'client_encoding': 'utf8',
            'connect_timeout': 15
        }
    
    return create_engine(
        database_url,
        connect_args=connect_args,
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=300,    # Recycle connections every 5 minutes
        pool_size=10,        # Maximum pool size
        max_overflow=20      # Allow up to 20 connections to overflow
    )
