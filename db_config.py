"""
Database configuration for the AMRS Maintenance Tracker application.
Handles connection pooling and other database settings.
"""

import os

def configure_database(app):
    """Configure database for different environments"""
    print("[DB_CONFIG] Configuring database connection...")
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Always use DATABASE_URL if set (PostgreSQL on Render)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        print(f"[DB_CONFIG] Using DATABASE_URL: {database_url}")
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

    # Only set engine options for non-SQLite databases
    uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not uri.startswith('sqlite://'):
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
