#!/usr/bin/env python3
"""
Initialize SQLite database for offline mode
"""
import os
import sys
import logging
from pathlib import Path
import secrets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[INIT_DB] %(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("init_local_db")

def main():
    # Set environment variables
    os.environ['OFFLINE_MODE'] = 'true'
    os.environ['USER_FIELD_ENCRYPTION_KEY'] = "_CY9_bO9vrX2CEUNmFqD1ETx-CluNejbidXFGMYapis="
    
    # Import models and database modules after setting environment variables
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    from models import db, User, Role
    from werkzeug.security import generate_password_hash
    from app import app
    
    # Make sure we're using SQLite
    from db_config import configure_database
    app = configure_database(app)
    
    # Output database URI for confirmation
    logger.info(f"Using database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Create all tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables created")
        
        # Create admin role if it doesn't exist
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin', description='Administrator', permissions='admin.full')
            db.session.add(admin_role)
            db.session.commit()
            logger.info("Created admin role with full permissions")
        
        # Create admin user directly with non-encrypted username/email for testing
        test_user = User.query.filter_by(_username='admin').first()
        if not test_user:
            logger.info("Creating test admin user")
            test_user = User(
                # Use raw values directly for testing
                _username='admin',
                _email='admin@example.com',
                password_hash=generate_password_hash('admin'),
                role=admin_role
            )
            db.session.add(test_user)
            db.session.commit()
            logger.info("Created test admin user: username=admin, password=admin")
        else:
            logger.info("Test admin user already exists")
        
        # Get the instance path
        logger.info(f"Instance path: {app.instance_path}")
        
        # Log success message
        logger.info("Local database initialization complete!")

if __name__ == "__main__":
    main()
