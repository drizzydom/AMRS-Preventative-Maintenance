"""
Database operations module that handles SQLAlchemy compatibility across versions
"""
from models import db

def execute_query(query, params=None):
    """
    Execute a SQL query using the appropriate method based on SQLAlchemy version
    
    Args:
        query (str): SQL query to execute
        params (dict, optional): Parameters for the query
        
    Returns:
        Result of the query execution
    """
    try:
        # Use SQLAlchemy 2.x method with session
        with db.session() as session:
            if params:
                result = session.execute(query, params)
            else:
                result = session.execute(query)
            session.commit()
            return result
    except AttributeError:
        # Fallback to SQLAlchemy 1.x method
        conn = db.engine.connect()
        try:
            if params:
                result = conn.execute(query, params)
            else:
                result = conn.execute(query)
            return result
        finally:
            conn.close()
    except Exception as e:
        if hasattr(db, 'session'):
            db.session.rollback()
        raise e

def init_db():
    """Initialize the database, creating all tables"""
    db.create_all()
