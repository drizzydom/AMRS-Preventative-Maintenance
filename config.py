"""
Configuration file for the AMRS Preventative Maintenance application
"""
import os
from datetime import timedelta

class Config:
    """Base configuration class with settings common to all environments"""
    # Generate a default secret key for development
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    
    # Database settings - SQLite by default
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///maintenance.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') != 'false'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Application settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    BACKUP_FOLDER = os.environ.get('BACKUP_FOLDER') or 'backups'


class DevelopmentConfig(Config):
    """Development configuration - enables debug mode and detailed error messages"""
    DEBUG = True
    TESTING = False
    EXPLAIN_TEMPLATE_LOADING = True  # Helpful for debugging template issues
    
    # Development mail settings
    MAIL_DEBUG = True
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND') != 'false'


class ProductionConfig(Config):
    """Production configuration - optimized for deployment"""
    DEBUG = False
    TESTING = False
    
    # For production, use the environment variable if set, otherwise use the parent's default
    # This avoids raising an error when running in development mode
    if os.environ.get('FLASK_ENV') == 'production' and not os.environ.get('SECRET_KEY'):
        raise ValueError("No SECRET_KEY set for production environment")
    
    # Production specific database settings
    if os.environ.get('DATABASE_URL'):
        # Use external database if configured
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    else:
        # Default to SQLite in a persistent location
        SQLALCHEMY_DATABASE_URI = 'sqlite:///var/data/maintenance.db'
    
    # Mail settings for production
    MAIL_DEBUG = False
    MAIL_SUPPRESS_SEND = False


class TestingConfig(Config):
    """Testing configuration - used for automated tests"""
    DEBUG = False
    TESTING = True
    
    # Use in-memory SQLite for tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF protection in tests
    WTF_CSRF_ENABLED = False
    
    # Don't actually send emails during tests
    MAIL_SUPPRESS_SEND = True
