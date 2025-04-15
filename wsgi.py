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
        for subdir in ['db', 'backups', 'uploads']:
            full_path = os.path.join(data_dir, subdir)
            if not os.path.exists(full_path):
                os.makedirs(full_path, exist_ok=True)
                logger.info(f"Created directory: {full_path}")
except Exception as e:
    logger.error(f"Failed to set up directories: {str(e)}")

logger.info(f"FLASK_APP: {os.environ.get('FLASK_APP', 'Not set')}")
logger.info(f"DATA_DIR: {os.environ.get('DATA_DIR', '/var/data')}")

# Import the real Flask application file
# Instead of importing from app.py, import directly from the actual application module
# Adjust this import to match your actual application structure
import sys
sys.path.insert(0, os.path.dirname(__file__))
from flask_app import create_app  # Assuming your actual app is in flask_app.py

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
