"""
Database utilities for PostgreSQL database
"""
import os
import psycopg2
from datetime import datetime
from flask import current_app
from sqlalchemy import text

def get_db_connection():
    """Get a connection to the PostgreSQL database"""
    # Get the database URL from the app config or environment
    db_url = current_app.config.get('SQLALCHEMY_DATABASE_URI') or os.environ.get('DATABASE_URL')
    
    if not db_url:
        raise ValueError("Database URL is not configured")
    
    # Connect to the database
    conn = psycopg2.connect(db_url)
    return conn

def execute_sql(sql_statement, params=None):
    """
    Execute SQL with proper connection handling for SQLAlchemy 2.0+
    
    Args:
        sql_statement: SQL query string or SQLAlchemy text object
        params: Optional parameters for the query
    
    Returns:
        Result of the execution
    """
    from app import db
    
    # Convert string to text object if needed
    if isinstance(sql_statement, str):
        sql_statement = text(sql_statement)
    
    # Execute with proper connection handling
    with db.engine.connect() as conn:
        result = conn.execute(sql_statement, parameters=params or {})
        return result
        
def check_connection():
    """Test database connection"""
    try:
        execute_sql("SELECT 1")
        return True
    except Exception as e:
        current_app.logger.error(f"Database connection error: {e}")
        return False

def check_database_status():
    """Check if the database is available and connected"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return True, f"Connected to PostgreSQL: {version}"
    except Exception as e:
        return False, f"Database connection failed: {str(e)}"

def get_table_row_counts():
    """Get count of rows in important tables"""
    results = {}
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        tables = ['users', 'roles', 'sites', 'machines', 'parts', 'maintenance_records']
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                results[table] = count
            except:
                results[table] = "Not available"
                
        cursor.close()
        conn.close()
        return True, results
    except Exception as e:
        return False, f"Error getting table counts: {str(e)}"
