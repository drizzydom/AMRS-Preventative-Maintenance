"""
Utilities for configuring databases on Render
"""
import os
import sys
import json
import logging
from pathlib import Path

logger = logging.getLogger("render_db_utils")

def setup_render_database():
    """
    Configure database for Render environment
    
    Returns:
        Database URL string
    """
    # Check if running on Render
    is_render = os.environ.get('RENDER', '').lower() == 'true'
    
    # Get potential database URLs
    database_url = None
    
    # Check environment variables in order of preference
    possible_vars = [
        'DATABASE_URL',
        'RENDER_DATABASE_URL',
        'POSTGRES_URL',
        'POSTGRESQL_URL'
    ]
    
    # First check for explicit database URLs
    for var in possible_vars:
        if var in os.environ:
            database_url = os.environ[var]
            logger.info(f"Found database URL in {var}")
            break
    
    # If no URL but we have PostgreSQL components, build the URL
    if not database_url and all(v in os.environ for v in ['PGUSER', 'PGPASSWORD', 'PGHOST', 'PGDATABASE']):
        user = os.environ['PGUSER']
        password = os.environ['PGPASSWORD']
        host = os.environ['PGHOST']
        database = os.environ['PGDATABASE']
        port = os.environ.get('PGPORT', '5432')
        
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        logger.info("Built PostgreSQL URL from individual environment variables")
    
    # If on Render but no database URL found, use SQLite in-memory as last resort
    if is_render and not database_url:
        logger.warning("No database URL found on Render, using in-memory SQLite")
        logger.warning("This is NOT recommended for production as data will be lost when the service restarts")
        database_url = "sqlite:///:memory:"
    
    # Local development fallback to SQLite file
    if not is_render and not database_url:
        # Create instance directory if needed
        instance_dir = Path('instance')
        instance_dir.mkdir(exist_ok=True)
        
        database_url = "sqlite:///instance/maintenance.db"
        logger.info(f"Using SQLite database for local development: {database_url}")
    
    # Fix PostgreSQL URL format if needed
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        logger.info("Fixed PostgreSQL URL format (postgres:// → postgresql://)")
    
    return database_url

def test_database_connection(url):
    """
    Test a database connection
    
    Args:
        url: Database URL string
        
    Returns:
        (success, message) tuple
    """
    try:
        # Create engine with minimal options
        engine = create_engine(url, pool_pre_ping=True)
        
        # Try to connect
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.scalar() == 1:
                return True, "Database connection successful"
            else:
                return False, "Database connection test failed"
    except Exception as e:
        return False, f"Database connection error: {str(e)}"

def fix_sqlalchemy_compatibility():
    """
    Patch SQLAlchemy for compatibility between versions
    
    This is a monkey patch to add missing methods in SQLAlchemy 2.0
    """
    import sqlalchemy
    from sqlalchemy.engine.base import Engine
    
    # Only patch if using SQLAlchemy 2.0+
    if sqlalchemy.__version__.startswith('2.'):
        if not hasattr(Engine, 'execute'):
            # Add execute method to Engine class for backwards compatibility
            def _engine_execute(self, statement, *args, **kwargs):
                with self.connect() as conn:
                    return conn.execute(statement, *args, **kwargs)
                    
            Engine.execute = _engine_execute
            logger.info("Added execute() compatibility method to SQLAlchemy Engine")
    
    return True
