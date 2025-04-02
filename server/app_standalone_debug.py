import os
import sys

# Configure logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("debug")

# Try to import the main application
try:
    from app_standalone import app, User, db
    
    # Check routes
    logger.info("Available routes:")
    for rule in app.url_map.iter_rules():
        logger.info(f"{rule.endpoint}: {rule.methods} {rule}")
    
    # Check database status
    with app.app_context():
        try:
            user_count = User.query.count()
            logger.info(f"Database connected successfully. Found {user_count} users.")
            
            # Check for superadmin user
            superadmin = User.query.filter_by(username="techsupport").first()
            if superadmin:
                logger.info("Superadmin account exists!")
            else:
                logger.warning("Superadmin account not found!")
                
        except Exception as db_error:
            logger.error(f"Database error: {db_error}")
    
except Exception as e:
    logger.error(f"Error importing application: {e}")
    import traceback
    traceback.print_exc()

print("Debug script completed. Check the logs for details.")
