import os
import logging
from flask import Flask

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask app"""
    app = Flask(__name__)
    
    # Configure the app - MUST BE DONE BEFORE ANY DB OPERATIONS
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key')
    
    # Print debug info for troubleshooting
    logger.debug(f"Creating app with database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Initialize database - must import after config is set
    from app.models import db
    db.init_app(app)
    
    # Configure other app components
    with app.app_context():
        # Create database tables
        db.create_all()
        logger.debug("Database tables created successfully")
    
    # Add health check endpoint
    @app.route('/api/health')
    def health_check():
        return {'status': 'ok', 'version': '1.0.0'}
    
    return app