"""
WSGI entry point for the AMRS Preventative Maintenance application.
This file is used by Gunicorn to serve the application in production.
Optimized for SocketIO with memory management.
"""
import os
import sys
import logging
import eventlet

# Patch standard library for eventlet compatibility BEFORE any other imports
eventlet.monkey_patch()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directory setup
try:
    data_dir = os.environ.get('DATA_DIR', '/var/data')
    if not os.path.exists(data_dir):
        logger.warning(f"Data directory {data_dir} does not exist!")
    else:
        for subdir in ['db', 'uploads']:
            full_path = os.path.join(data_dir, subdir)
            if not os.path.exists(full_path):
                os.makedirs(full_path, exist_ok=True)
                logger.info(f"Created directory: {full_path}")
except Exception as e:
    logger.error(f"Failed to set up directories: {str(e)}")

logger.info(f"FLASK_APP: {os.environ.get('FLASK_APP', 'Not set')}")
logger.info(f"DATA_DIR: {os.environ.get('DATA_DIR', '/var/data')}")

# Run auto migration
from auto_migrate import run_auto_migration
run_auto_migration()

# Import the Flask app and SocketIO instance from render_app.py
from render_app import app, socketio

# Ensure all tables are created before serving requests
from models import db, AuditTask, AuditTaskCompletion, User, Role, Site, Machine, Part, MaintenanceRecord
with app.app_context():
    db.create_all()

# Memory management settings for eventlet
eventlet.debug.hub_exceptions(False)  # Reduce debug overhead

# For gunicorn usage - expose the app
application = app

if __name__ == "__main__":
    # Direct run (not recommended for production)
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"[AMRS Production] Starting SocketIO server on 0.0.0.0:{port}")
    socketio.run(app, host="0.0.0.0", port=port, debug=False)
