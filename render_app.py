"""
Simple adapter for Render.
This file imports the app from app.py directly for Render deployment.
"""

import os
import sys
print("Initializing render_app.py for Render deployment...")

# Import the app from the main application
try:
    from app import app
    print("Successfully imported app from app.py")
except ImportError as e:
    print(f"Error importing from app.py: {e}")
    print(f"Python path: {sys.path}")
    print("Fatal error: Could not import application!")
    raise

from models import db, AuditTask, AuditTaskCompletion, User, Role, Site, Machine, Part, MaintenanceRecord
with app.app_context():
    db.create_all()
