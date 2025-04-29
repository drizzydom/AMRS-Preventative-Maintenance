"""
WSGI entry point for the AMRS Preventative Maintenance application.
This file is used by Gunicorn to serve the application in production.
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directory setup
try:
    data_dir = os.environ.get('DATA_DIR', '/var/data')
    if not os.path.exists(data_dir):
        logger.warning(f"Data directory {data_dir} does not exist!")
    else:
        for subdir in ['db', 'uploads']:  # Removed 'backups'
            full_path = os.path.join(data_dir, subdir)
            if not os.path.exists(full_path):
                os.makedirs(full_path, exist_ok=True)
                logger.info(f"Created directory: {full_path}")
except Exception as e:
    logger.error(f"Failed to set up directories: {str(e)}")

logger.info(f"FLASK_APP: {os.environ.get('FLASK_APP', 'Not set')}")
logger.info(f"DATA_DIR: {os.environ.get('DATA_DIR', '/var/data')}")
logger.info(f"PORT: {os.environ.get('PORT', '5000')}")  # Log the PORT variable for debugging

from auto_migrate import run_auto_migration
run_auto_migration()

# Import the Flask app from app.py
try:
    logger.info("Attempting to import app from app module...")
    from app import app
    logger.info("Successfully imported app from app.py")
except ImportError as e:
    logger.error(f"Failed to import app from app.py: {e}")
    
    # Try to import from render_app.py as a fallback
    try:
        logger.info("Attempting to import app from render_app module...")
        from render_app import app
        logger.info("Successfully imported app from render_app.py")
    except ImportError as e:
        logger.error(f"Failed to import app from render_app.py: {e}")
        raise RuntimeError("Could not initialize Flask app through any available method")

# Ensure all tables are created before serving requests
from models import db, AuditTask, AuditTaskCompletion, User, Role, Site, Machine, Part, MaintenanceRecord
with app.app_context():
    db.create_all()

# This is needed for Render.com to detect the app is listening on the right port
# The variable must be called 'app' for the WSGI server to find it
# No main block needed as Gunicorn will import this module and use the 'app' variable

# Log which port we'll be using
port = int(os.environ.get("PORT", 5000))
logger.info(f"Application configured to use port {port}")

# No app.run() call here as Gunicorn handles that part
