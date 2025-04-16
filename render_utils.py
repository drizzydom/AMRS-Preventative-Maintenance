"""
Utilities for deploying on Render
"""
import os
import sys
import json
from pathlib import Path

def setup_render_environment():
    """
    Configure application for Render environment
    """
    print("[RENDER] Setting up Render-specific environment")
    
    # Check if we're on Render
    is_render = os.environ.get('RENDER', '').lower() == 'true'
    if not is_render:
        print("[RENDER] Not running on Render, skipping setup")
        return False
        
    # Potential database URLs
    database_url = None
    
    # 1. Check for PostgreSQL variables set by Render
    potential_vars = [
        'DATABASE_URL',
        'RENDER_DATABASE_URL',
        'POSTGRES_URL',
        'PGDATABASE',
        'PGUSER',
        'PGPASSWORD',
        'PGHOST',
        'PGPORT'
    ]
    
    found_vars = []
    for var in potential_vars:
        if var in os.environ:
            found_vars.append(var)
    
    if found_vars:
        print(f"[RENDER] Found database-related variables: {', '.join(found_vars)}")
    else:
        print("[RENDER] No database environment variables found")
    
    # 2. Check for DATABASE_URL explicitly
    if 'DATABASE_URL' in os.environ:
        database_url = os.environ['DATABASE_URL']
        print("[RENDER] DATABASE_URL environment variable is set")
        
        # Fix common postgres:// vs postgresql:// issue
        if database_url.startswith('postgres://'):
            fixed_url = database_url.replace('postgres://', 'postgresql://', 1)
            os.environ['DATABASE_URL'] = fixed_url
            print("[RENDER] Fixed DATABASE_URL protocol from postgres:// to postgresql://")
    
    # 3. Construct from individual params if needed
    elif all(var in os.environ for var in ['PGUSER', 'PGPASSWORD', 'PGHOST', 'PGDATABASE']):
        user = os.environ['PGUSER']
        password = os.environ['PGPASSWORD']
        host = os.environ['PGHOST']
        db = os.environ['PGDATABASE']
        port = os.environ.get('PGPORT', '5432')
        
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
        os.environ['DATABASE_URL'] = database_url
        print("[RENDER] Constructed DATABASE_URL from individual PostgreSQL environment variables")
    
    # 4. If still no database URL, create a service info file
    if not database_url:
        try:
            service_info = {
                'render_service': True,
                'timestamp': os.environ.get('RENDER_TIMESTAMP', 'unknown'),
                'service_id': os.environ.get('RENDER_SERVICE_ID', 'unknown'),
                'service_name': os.environ.get('RENDER_SERVICE_NAME', 'unknown'),
                'env_vars_found': found_vars,
                'missing_database_url': True
            }
            
            # Write to a file that can be examined later
            info_path = Path('/opt/render/project/src/render_service_info.json')
            with open(info_path, 'w') as f:
                json.dump(service_info, f, indent=2)
                
            print(f"[RENDER] Created service info file at {info_path}")
            print("[RENDER] WARNING: No PostgreSQL connection could be established")
            print("[RENDER] The application will use in-memory SQLite, which will NOT persist data")
            print("[RENDER] Please add a PostgreSQL database from the Render dashboard")
        except Exception as e:
            print(f"[RENDER] Error writing service info: {e}")
    
    return True

if __name__ == "__main__":
    setup_render_environment()
