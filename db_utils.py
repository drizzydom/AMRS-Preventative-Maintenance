"""
Database utilities for PostgreSQL database
"""
import os
import psycopg2
from datetime import datetime
from flask import current_app

def get_db_connection():
    """Get a connection to the PostgreSQL database"""
    # Get the database URL from the app config or environment
    db_url = current_app.config.get('SQLALCHEMY_DATABASE_URI') or os.environ.get('DATABASE_URL')
    
    if not db_url:
        raise ValueError("Database URL is not configured")
    
    # Connect to the database
    conn = psycopg2.connect(db_url)
    return conn

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
