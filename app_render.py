"""
Render.com app entry point.
Since Render insists on running 'gunicorn app:app', this file
acts as a bridge to import the actual Flask application.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting AMRS Maintenance application for Render.com")

from auto_migrate import run_auto_migration
run_auto_migration()

# Import the app from the main app.py file
try:
    # First, try to import directly from app.py
    logger.info("Attempting to import app from app module...")
    from app import app
    logger.info("Successfully imported app from app.py")
except ImportError as e:
    logger.error(f"Failed to import app from app.py: {e}")
    
    # Second option: try to import from wsgi.py
    try:
        logger.info("Attempting to import app from wsgi module...")
        from wsgi import app
        logger.info("Successfully imported app from wsgi.py")
    except ImportError as e:
        logger.error(f"Failed to import app from wsgi.py: {e}")
        
        # Third option: try to create a new app from flask_app
        try:
            logger.info("Attempting to import create_app from flask_app module...")
            from flask_app import create_app
            app = create_app()
            logger.info("Successfully created app from flask_app.create_app()")
        except ImportError as e:
            logger.error(f"Failed to import create_app from flask_app: {e}")
            raise RuntimeError("Could not initialize Flask app through any available method")

# Log startup information for debugging
logger.info(f"App initialized with name: {app.name}")
logger.info(f"Available routes: {[str(rule) for rule in app.url_map.iter_rules()]}")

# This is what Gunicorn will import
# The variable must be named 'app' for 'gunicorn app:app' to work
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting development server on port {port}")
    app.run(host="0.0.0.0", port=port)
