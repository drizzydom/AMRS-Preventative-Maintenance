#!/usr/bin/env python
"""
Check Render database configuration
"""
import os
import sys
import datetime

def check_environment():
    """Check the environment for database configuration"""
    print("\n=== ENVIRONMENT CHECK ===")
    print(f"Current time: {datetime.datetime.now()}")
    print(f"Python version: {sys.version}")
    print(f"Running on Render: {os.environ.get('RENDER', 'false')}")
    print(f"Working directory: {os.getcwd()}")
    
    # Check for database environment variables
    database_vars = [
        'DATABASE_URL',
        'RENDER_DATABASE_URL',
        'INTERNAL_DATABASE_URL',
        'POSTGRES_URL',
        'PG_URL',
        'POSTGRESQL_URL'
    ]
    
    print("\n=== DATABASE ENVIRONMENT VARIABLES ===")
    found = False
    for var in database_vars:
        if var in os.environ:
            found = True
            # Mask the password if present
            value = os.environ[var]
            if '@' in value and ':' in value:
                # Simple masking for usernames and passwords in URLs
                parts = value.split('@')
                auth_parts = parts[0].split(':')
                if len(auth_parts) > 2:  # protocol:user:pass format
                    masked = f"{auth_parts[0]}:{auth_parts[1]}:****@{parts[1]}"
                else:  # user:pass format
                    masked = f"{auth_parts[0]}:****@{parts[1]}"
                print(f"  {var}: {masked}")
            else:
                print(f"  {var}: {value}")
    
    if not found:
        print("  No database environment variables found!")
    
    print("\n=== DATABASE RELATED ENVIRONMENT VARIABLES ===")
    for key, value in os.environ.items():
        if any(term in key.upper() for term in ['DB', 'SQL', 'POSTGRES', 'DATABASE']):
            if key not in database_vars:
                # Mask potential sensitive values
                if any(term in value for term in ['password', 'user', '@', ':']):
                    value = "****"
                print(f"  {key}: {value}")
    
    print("\n=== TESTING DATABASE CONNECTION ===")
    try:
        from db_compat import check_db_connection
        from db_config import get_db_engine
        
        engine = get_db_engine()
        connected = check_db_connection(engine)
        
        if connected:
            print("✅ Database connection successful!")
            # Try to get database metadata
            try:
                from sqlalchemy import inspect
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                print(f"  Tables found: {len(tables)}")
                if tables:
                    print(f"  Table names: {', '.join(tables[:5])}{'...' if len(tables) > 5 else ''}")
            except Exception as e:
                print(f"  Error fetching metadata: {e}")
        else:
            print("❌ Database connection failed!")
    except Exception as e:
        print(f"❌ Error testing database connection: {e}")
    
    print("\n=== END OF CHECK ===")

if __name__ == "__main__":
    check_environment()
