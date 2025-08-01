"""
Simple adapter for Render.
This file imports the app from app.py directly for Render deployment.
"""

import os
import sys
print("Initializing render_app.py for Render deployment...")

# Import the app and socketio from the main application FIRST
try:
    from app import app, socketio
    print("Successfully imported app and socketio from app.py")
except ImportError as e:
    print(f"Error importing from app.py: {e}")
    print(f"Python path: {sys.path}")
    print("Fatal error: Could not import application!")
    raise

# Now run auto migration after the app is available
from auto_migrate import run_auto_migration
print("Running auto migration...")
run_auto_migration()
