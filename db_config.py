import os
from flask import Flask

def configure_database(app):
    """Configure database settings for the application"""
    try:
        # Check if running on Render
        if os.environ.get('RENDER', False):
            # Use PostgreSQL configuration on Render
            print("[DB_CONFIG] Running on Render platform, using PostgreSQL")
            app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
                'DATABASE_URL', 
                'postgresql://maintenance_tracker_data_user:mbVv4EmuXc0co5A0KcHe57SPhW7Kd0gi@dpg-cvv7vebe5dus73ec3ksg-a/maintenance_tracker_data'
            )
        
            # Set up database directory on persistent storage
            if os.environ.get('RENDER_DATA_DIR'):
                data_dir = os.environ.get('RENDER_DATA_DIR')
                print(f"[DB_CONFIG] Using Render persistent storage: {data_dir}")

                # Create uploads directory
                uploads_dir = os.path.join(data_dir, 'uploads')
                os.makedirs(uploads_dir, exist_ok=True)
                app.config['UPLOAD_DIR'] = uploads_dir
                print(f"[DB_CONFIG] Uploads will be stored at: {uploads_dir}")

        else:
            # Local development environment
            print("[DB_CONFIG] Running in local environment")
            
            # Get instance path for database and other persistent data
            instance_path = app.instance_path
            os.makedirs(instance_path, exist_ok=True)
            print(f"[DB_CONFIG] Using instance path: {instance_path}")
            
            # Create uploads directory
            uploads_dir = os.path.join(instance_path, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            app.config['UPLOAD_DIR'] = uploads_dir
            print(f"[DB_CONFIG] Using local uploads at: {uploads_dir}")
            
            # Use SQLite by default if no DATABASE_URL is set
            if os.environ.get('DATABASE_URL'):
                app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
                print(f"[DB_CONFIG] Using database from environment: {os.environ.get('DATABASE_URL')}")
            else:
                # Default to PostgreSQL for local development
                app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/maintenance_tracker'
                print("[DB_CONFIG] Using default PostgreSQL database")
        
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        return app
            
    except Exception as e:
        print(f"[DB_CONFIG] Error configuring database: {str(e)}")
        raise
