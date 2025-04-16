"""
Database connection fixing utility
"""
import os
import sys
import subprocess

def fix_database_connection():
    """
    Diagnose and fix database connection issues
    """
    print("\n=== DATABASE CONNECTION FIXER ===")
    
    # 1. Check for environment variables
    db_vars = ['DATABASE_URL', 'POSTGRES_URL', 'PGDATABASE', 'DB_URL', 
               'SQLALCHEMY_DATABASE_URI', 'RENDER_POSTGRES_URL']
    
    found_vars = []
    for var in db_vars:
        if var in os.environ:
            safe_value = mask_db_url(os.environ[var])
            found_vars.append(f"{var}={safe_value}")
    
    if found_vars:
        print("Found database environment variables:")
        for var in found_vars:
            print(f"  {var}")
    else:
        print("No database environment variables found.")
        
        # Try to check if we're on Render
        is_render = 'RENDER' in os.environ
        if is_render:
            print("Running on Render, but no DATABASE_URL found.")
            print("This likely means the PostgreSQL add-on is not attached.")
            print("\nFix options:")
            print("1. Add a PostgreSQL database from the Render dashboard")
            print("2. Set DATABASE_URL manually in the environment variables section")
        else:
            print("Not running on a recognized hosting environment.")
    
    # 2. Check database connectivity
    try:
        # Try to connect with Python
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import SQLAlchemyError
        
        # For troubleshooting, try a more direct SQLAlchemy connection
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            try:
                print(f"\nTrying direct SQLAlchemy connection to {mask_db_url(db_url)}...")
                engine = create_engine(db_url)
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT version();"))
                    version = result.scalar()
                    print(f"Connection successful! Database version: {version}")
            except SQLAlchemyError as e:
                print(f"SQLAlchemy connection failed: {e}")
        else:
            print("\nNo DATABASE_URL to test direct connection.")
    except ImportError:
        print("SQLAlchemy not available for direct connection test.")
    
    # 3. Make recommendations
    print("\n=== RECOMMENDATIONS ===")
    print("1. Set the DATABASE_URL environment variable to a valid PostgreSQL URL")
    print("2. Ensure the database is accessible from your application")
    print("3. Add a solid error handler to db_config.py for database connection failures")
    
    print("\n=== EXAMPLE FIX FOR app.py ===")
    print("""
    # Add to your app.py:
    from db_compat import execute_query
    
    # Replace:
    # db.engine.execute("SELECT 1")
    
    # With:
    execute_query(db, "SELECT 1")
    """)

def mask_db_url(url):
    """Mask sensitive information in database URL"""
    if not url or '@' not in url:
        return url
        
    parts = url.split('@')
    prefix = parts[0]
    
    # Handle username:password part
    if ':' in prefix and '://' in prefix:
        # Extract protocol (postgres://, postgresql://, etc.)
        protocol_parts = prefix.split('://')
        protocol = protocol_parts[0] + '://'
        
        # Mask the credentials
        return f"{protocol}****:****@{parts[1]}"
    
    return url

if __name__ == "__main__":
    fix_database_connection()
