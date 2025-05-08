"""
Database configuration for the AMRS Maintenance Tracker application.
Handles connection pooling and other database settings.
"""

import os

def configure_database(app):
    """Configure database for different environments"""
    print("[DB_CONFIG] Configuring database connection...")
    database_url = os.environ.get('DATABASE_URL')
    
    # Check for offline mode (set in app_bootstrap.py)
    offline_mode = os.environ.get('OFFLINE_MODE', '').lower() == 'true'
    
    if database_url:
        # Always use DATABASE_URL if set (PostgreSQL on Render or SQLite path in offline mode)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        print(f"[DB_CONFIG] Using DATABASE_URL: {database_url}")
        
        # For offline mode with SQLite, ensure the directory exists
        if offline_mode and database_url.startswith('sqlite:///'):
            # Extract path from sqlite:///path format
            db_path = database_url.replace('sqlite:///', '')
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                print(f"[DB_CONFIG] Creating database directory: {db_dir}")
                os.makedirs(db_dir, exist_ok=True)
                print(f"[DB_CONFIG] Offline mode database directory created at: {db_dir}")
            
            # Print the actual database file path for debugging
            print(f"[DB_CONFIG] SQLite database path: {os.path.abspath(db_path)}")
            
            # Add SQLite-specific connection options for better reliability
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                'connect_args': {
                    'timeout': 30,            # Wait up to 30 seconds for locks
                    'check_same_thread': False, # Allow cross-thread usage
                    'isolation_level': None   # Use autocommit mode
                }
            }
            
            # Verify database file is writable
            try:
                if os.path.exists(db_path):
                    # Check if file is writable
                    if not os.access(db_path, os.W_OK):
                        print(f"[DB_CONFIG] WARNING: Database file is not writable: {db_path}")
                        # Try to fix permissions
                        try:
                            os.chmod(db_path, 0o600)  # User read/write permissions
                            print(f"[DB_CONFIG] Fixed permissions on database file")
                        except Exception as e:
                            print(f"[DB_CONFIG] Could not fix permissions: {e}")
                else:
                    # Directory should be writable to create the file
                    if not os.access(db_dir, os.W_OK):
                        print(f"[DB_CONFIG] WARNING: Database directory is not writable: {db_dir}")
                        try:
                            os.chmod(db_dir, 0o700)  # User read/write/execute for directory
                            print(f"[DB_CONFIG] Fixed permissions on database directory")
                        except Exception as e:
                            print(f"[DB_CONFIG] Could not fix permissions: {e}")
            except Exception as e:
                print(f"[DB_CONFIG] Error checking database permissions: {e}")
    else:
        # Fallback to SQLite (local development or if no DATABASE_URL)
        if os.environ.get('RENDER'):
            try:
                data_dir = '/var/data'
                if not os.path.exists(data_dir):
                    print(f"[DB_CONFIG] Creating data directory: {data_dir}")
                    os.makedirs(data_dir, exist_ok=True)
                db_dir = os.path.join(data_dir, 'db')
                os.makedirs(db_dir, exist_ok=True)
                db_path = os.path.join(db_dir, 'maintenance.db')
                app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
                print(f"[DB_CONFIG] Using Render persistent storage at: {db_path}")
            except Exception as e:
                print(f"[DB_CONFIG] Error setting up Render database: {e}")
                app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maintenance.db'
                print(f"[DB_CONFIG] Fallback to local maintenance.db")
        else:
            # Get database URI from environment or use default
            instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
            if not os.path.exists(instance_dir):
                print(f"[DB_CONFIG] Creating instance directory: {instance_dir}")
                os.makedirs(instance_dir, exist_ok=True)
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/maintenance.db'
            print(f"[DB_CONFIG] Using local SQLite database at instance/maintenance.db")
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Configure SQLite specific options
    uri = app.config['SQLALCHEMY_DATABASE_URI']
    if uri.startswith('sqlite://'):
        # Set SQLite-specific options if not already set
        if 'SQLALCHEMY_ENGINE_OPTIONS' not in app.config:
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                'connect_args': {
                    'timeout': 30,
                    'check_same_thread': False,
                    'isolation_level': None
                }
            }
    # Only set pool options for non-SQLite databases
    elif not uri.startswith('sqlite://'):
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 10,
            'pool_recycle': 1800,
            'pool_pre_ping': True,
            'pool_timeout': 30,
            'max_overflow': 5,
            'echo': app.debug,
            'echo_pool': app.debug,
        }
    return app
