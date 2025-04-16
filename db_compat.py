"""
SQLAlchemy compatibility layer to handle version differences
"""
import sqlalchemy
from sqlalchemy import text

# Check SQLAlchemy version
SQLALCHEMY_VERSION = sqlalchemy.__version__
IS_SQLALCHEMY_2 = SQLALCHEMY_VERSION.startswith('2.')

def execute_query(db, query_text, params=None):
    """
    Execute a SQL query in a version-compatible way
    
    Args:
        db: SQLAlchemy database instance
        query_text: SQL query string
        params: Optional parameters for the query
        
    Returns:
        Query result
    """
    # Convert to SQLAlchemy text object if it's a string
    if isinstance(query_text, str):
        query = text(query_text)
    else:
        query = query_text
        
    # SQLAlchemy 2.0 style
    if IS_SQLALCHEMY_2:
        with db.engine.connect() as conn:
            if params:
                result = conn.execute(query, params)
            else:
                result = conn.execute(query)
            return result
    # SQLAlchemy 1.x style (fallback)
    else:
        if params:
            return db.engine.execute(query, params)
        else:
            return db.engine.execute(query)

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
        print(f"Connection check failed: {e}")
        return False
