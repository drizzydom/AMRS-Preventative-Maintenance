import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Print environment variables for debugging
logger.info(f"DATABASE_URL: {os.environ.get('DATABASE_URL', 'Not set')}")
logger.info(f"FLASK_APP: {os.environ.get('FLASK_APP', 'Not set')}")

# Import and create Flask app
from app import create_app

# Create app instance - this is what Gunicorn will use
app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=9000)
