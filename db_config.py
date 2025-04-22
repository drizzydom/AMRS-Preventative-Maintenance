"""
Database configuration for the AMRS Maintenance Tracker application.
Handles connection pooling and other database settings.
"""

import os

def configure_database(app):
    """Configure database for different environments"""
    print("[DB_CONFIG] Configuring database connection...")
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
        database_uri = os.environ.get(
            'DATABASE_URL', 
            'postgresql://maintenance_tracker_data_user:mbVv4EmuXc0co5A0KcHe57SPhW7Kd0gi@dpg-cvv7vebe5dus73ec3ksg-a/maintenance_tracker_data'
        )
        
        # Basic SQLAlchemy configuration
        app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Connection pool configuration
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 10,                # Maximum number of connections to keep
            'pool_recycle': 1800,           # Recycle connections after 30 minutes
            'pool_pre_ping': True,          # Check connections before using them
            'pool_timeout': 30,             # Timeout after 30 seconds when getting connection
            'max_overflow': 5,              # Allow 5 connections beyond pool_size
            'echo': app.debug,              # Log SQL queries in debug mode
            'echo_pool': app.debug,         # Log connection pool events in debug mode
        }
    
    return app
