import os
import sys
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_database_config():
    """Debug database configuration issues"""
    logger.info("Debugging database configuration")
    
    # Check environment variables
    db_url = os.environ.get('DATABASE_URL')
    logger.info(f"DATABASE_URL environment variable: {db_url}")
    
    # Check Python version and path
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Python executable: {sys.executable}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    try:
        # Try to import and initialize Flask app
        from app import create_app, db
        
        # Try to create app
        app = create_app()
        logger.info(f"App created successfully")
        logger.info(f"SQLALCHEMY_DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
        
        # Try to initialize database
        with app.app_context():
            logger.info("Attempting to create database tables...")
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Try to check if tables exist
            try:
                from app.models import User
                user_count = User.query.count()
                logger.info(f"Found {user_count} users in database")
            except Exception as e:
                logger.error(f"Error accessing User table: {str(e)}")
        
        logger.info("Database configuration appears to be working!")
        return True
        
    except Exception as e:
        logger.error(f"Error during database initialization: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_database_config()
    sys.exit(0 if success else 1)
