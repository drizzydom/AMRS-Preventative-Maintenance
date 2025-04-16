"""
Database compatibility layer to handle different SQLAlchemy versions
"""
import sys
import warnings
from sqlalchemy import __version__ as sa_version

# Check SQLAlchemy version
SA_VERSION = tuple(int(x) for x in sa_version.split('.')[0:2])
SA_1_4_OR_LATER = SA_VERSION >= (1, 4)
SA_2_0_OR_LATER = SA_VERSION >= (2, 0)

def safe_db_execute(engine, query, params=None, scalar=False, fetch_one=False):
    """
    Execute a database query safely regardless of SQLAlchemy version
    
    Args:
        engine: SQLAlchemy engine or connection
        query: SQL query string
        params: Optional parameters for the query
        scalar: Whether to return a scalar result
        fetch_one: Whether to fetch only one row
        
    Returns:
        Query results
    """
    try:
        # Convert string to text clause if needed
        from sqlalchemy import text
        if isinstance(query, str):
            query = text(query)
            
        # SQLAlchemy 2.0 style
        if SA_2_0_OR_LATER or not hasattr(engine, 'execute'):
            with engine.connect() as conn:
                if params:
                    result = conn.execute(query, params)
                else:
                    result = conn.execute(query)
                    
                if scalar and hasattr(result, 'scalar'):
                    return result.scalar()
                elif fetch_one:
                    return result.fetchone()
                else:
                    return result.fetchall()
        # SQLAlchemy 1.x style
        else:
            if params:
                result = engine.execute(query, params)
            else:
                result = engine.execute(query)
                
            if scalar:
                if hasattr(result, 'scalar'):
                    return result.scalar()
                else:
                    row = result.fetchone()
                    return row[0] if row else None
            elif fetch_one:
                return result.fetchone()
            else:
                return result.fetchall()
    except Exception as e:
        print(f"[DB] Database query error: {str(e)}", file=sys.stderr)
        raise

def check_db_connection(engine):
    """
    Check if the database connection is working
    
    Args:
        engine: SQLAlchemy engine
        
    Returns:
        True if connected, False otherwise
    """
    try:
        # Simple query to test connection
        result = safe_db_execute(engine, "SELECT 1", scalar=True)
        return result == 1
    except Exception as e:
        print(f"[DB] Connection check failed: {str(e)}", file=sys.stderr)
        return False
