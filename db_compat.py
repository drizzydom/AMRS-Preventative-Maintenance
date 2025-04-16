"""
Database compatibility layer for SQLAlchemy version differences
"""
import os
import sys
import logging
from sqlalchemy import text, __version__ as sa_version

# Check SQLAlchemy version
SA_VERSION = tuple(int(x) for x in sa_version.split('.')[:2])
IS_SQLALCHEMY_2 = SA_VERSION[0] >= 2

logger = logging.getLogger("db_compat")

def execute_query(db, query, params=None):
    """
    Execute a SQL query in a version-compatible way
    
    Args:
        db: SQLAlchemy database instance
        query: SQL query string or text object
        params: Optional parameters for the query
        
    Returns:
        Query result
    """
    # Convert to SQLAlchemy text object if it's a string
    if isinstance(query, str):
        query = text(query)
    
    try:
        # SQLAlchemy 2.0 style
        if IS_SQLALCHEMY_2:
            with db.engine.connect() as conn:
                if params:
                    result = conn.execute(query, params)
                else:
                    result = conn.execute(query)
                conn.commit()
                return result
        # SQLAlchemy 1.x style (fallback)
        else:
            if params:
                return db.engine.execute(query, params)
            else:
                return db.engine.execute(query)
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise

def check_connection(db):
    """
    Check database connection
    
    Args:
        db: SQLAlchemy database instance
        
    Returns:
        True if connected, False otherwise
    """
    try:
        # Try a simple query
        result = execute_query(db, "SELECT 1")
        return next(result)[0] == 1
    except Exception as e:
        logger.error(f"Connection check failed: {e}")
        return False
