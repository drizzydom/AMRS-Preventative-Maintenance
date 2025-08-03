"""
Simple adapter for Render.
This file imports the app from app.py directly for Render deployment.
"""

import os
import sys
print("Initializing render_app.py for Render deployment...")

# Import the app and socketio from the main application
# The app.py file handles all database initialization and migration
try:
    from app import app, socketio
    print("Successfully imported app and socketio from app.py")
    print("Database initialization and migration completed by app.py")
    # Print the current SQLALCHEMY_DATABASE_URI to confirm which database is being used
    try:
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', None)
        print(f"Active SQLALCHEMY_DATABASE_URI: {db_uri}")
    except Exception as db_uri_exc:
        print(f"Could not retrieve SQLALCHEMY_DATABASE_URI: {db_uri_exc}")
except ImportError as e:
    print(f"Error importing from app.py: {e}")
    print(f"Python path: {sys.path}")
    print("Fatal error: Could not import application!")
    raise
