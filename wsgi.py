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
        for subdir in ['db', 'uploads']:
            full_path = os.path.join(data_dir, subdir)
            if not os.path.exists(full_path):
                os.makedirs(full_path, exist_ok=True)
                logger.info(f"Created directory: {full_path}")
except Exception as e:
    logger.error(f"Failed to set up directories: {str(e)}")

logger.info(f"FLASK_APP: {os.environ.get('FLASK_APP', 'Not set')}")
logger.info(f"DATA_DIR: {os.environ.get('DATA_DIR', '/var/data')}")

# Import the Flask app and SocketIO from render_app.py (which imports from app.py)
# The app.py file already handles all database initialization and migration
from render_app import app, socketio

# The app is now ready to serve requests
print("WSGI: Application ready to serve requests")

# For gunicorn usage - expose the Flask app
application = app

if __name__ == "__main__":
    # Direct run for testing
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"[AMRS] Starting SocketIO server on 0.0.0.0:{port}")
    socketio.run(app, host="0.0.0.0", port=port, debug=False)
