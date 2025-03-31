import os
import logging
from flask import current_app
from app.extensions import db

logger = logging.getLogger(__name__)

def init_db():
    """Initialize database tables"""
    try:
        db.create_all()
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

def get_db_info():
    """Get database configuration info for debugging"""
    return {
        'database_url': current_app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured'),
        'environment_var': os.environ.get('DATABASE_URL', 'Not set')
    }
