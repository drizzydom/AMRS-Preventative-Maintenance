"""
Database operations module that handles SQLAlchemy compatibility across versions
"""
from sqlalchemy.orm import Session
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
        # SQLAlchemy 2.x method using a session
        with db.session() as session:
            if params:
                result = session.execute(query, params)
            else:
                result = session.execute(query)
            session.commit()
            return result
    except Exception as e:
        db.session.rollback()
        raise e

def init_db():
    """Initialize the database, creating all tables"""
    db.create_all()
    
def get_engine_connection():
    """
    Get a connection from the engine in a version-compatible way
    
    Returns:
        Connection object that can be used with execute()
    """
    return db.session.connection()
