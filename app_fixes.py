"""
Application fixes for common issues
"""
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[APP_FIXES] %(message)s')
logger = logging.getLogger("app_fixes")

def fix_sqlalchemy():
    """Apply SQLAlchemy compatibility fix"""
    try:
        # First try to load the module directly
        import sqlalchemy_compat
        logger.info("Applied SQLAlchemy compatibility fix")
        return True
    except ImportError:
        logger.warning("sqlalchemy_compat module not found, skipping SQLAlchemy fix")
        return False
    except Exception as e:
        logger.error(f"Error applying SQLAlchemy fix: {e}")
        return False

def apply_all_fixes(app=None):
    """Apply all fixes"""
    # Fix SQLAlchemy
    fix_sqlalchemy()
    
    # Fix Flask app configuration if provided
    if app:
        logger.info("Checking app configuration...")
        # Ensure app has secret_key (needed for sessions)
        if not app.secret_key:
            app.secret_key = os.urandom(24)
            logger.info("Added Flask secret_key for session support")
    
    logger.info("Applied compatibility fixes")
    return True
