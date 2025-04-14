import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_database():
    """Initialize the database with required tables"""
    
    try:
        # Import the database models
        from models import db, User
        from app import app
        
        # Create database tables
        with app.app_context():
            logger.info("Creating database tables...")
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
                    db.session.add(admin)
                    db.session.commit()
                    logger.info("Admin user created successfully")
                else:
                    logger.warning("DEFAULT_ADMIN_PASSWORD not set, skipping admin creation")
            else:
                logger.info("Admin user already exists")
            
            return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    initialize_database()
