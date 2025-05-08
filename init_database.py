import os
import sys
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_database(max_retries=3, retry_delay=1):
    """Initialize the database with required tables"""
    
    for attempt in range(max_retries):
        try:
            # Import the database models
            from models import db, User
            from app import app
            
            # Create database tables
            with app.app_context():
                logger.info("Creating database tables...")
                
                # Print database location for debugging
                db_uri = app.config['SQLALCHEMY_DATABASE_URI']
                if db_uri.startswith('sqlite:///'):
                    db_path = db_uri.replace('sqlite:///', '')
                    logger.info(f"Using SQLite database at: {os.path.abspath(db_path)}")
                else:
                    logger.info(f"Using database at: {db_uri}")
                
                db.create_all()
                
                # Check if admin user exists
                admin = User.query.filter_by(username='admin').first()
                if not admin:
                    # Create default admin user if DEFAULT_ADMIN_PASSWORD is set
                    admin_password = os.environ.get('DEFAULT_ADMIN_PASSWORD')
                    if admin_password:
                        logger.info("Creating default admin user...")
                        from werkzeug.security import generate_password_hash
                        admin = User(
                            username='admin',
                            email='admin@example.com',
                            password_hash=generate_password_hash(admin_password),
                            is_admin=True,
                            active=True
                        )
                        
                        try:
                            db.session.add(admin)
                            db.session.commit()
                            logger.info("Admin user created successfully")
                        except Exception as e:
                            db.session.rollback()
                            logger.error(f"Failed to create admin user: {e}")
                            raise
                    else:
                        logger.warning("DEFAULT_ADMIN_PASSWORD not set, skipping admin creation")
                else:
                    logger.info("Admin user already exists")
                
                # Verify database connection is working
                try:
                    db.session.execute("SELECT 1")
                    logger.info("Database connection verified")
                except Exception as e:
                    logger.error(f"Database connection test failed: {e}")
                
                return True
        except Exception as e:
            logger.error(f"Error initializing database (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error("Failed to initialize database after multiple attempts")
                return False

if __name__ == "__main__":
    initialize_database()
