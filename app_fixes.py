"""
Application fixes for common issues
"""
import os
import sys
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

def fix_flask_routes(app):
    """
    Fix Flask routing issues - carefully check if routes already exist
    
    Args:
        app: Flask application instance
    """
    try:
        # Check existing routes
        existing_endpoints = set(app.view_functions.keys())
        existing_rules = set(rule.rule for rule in app.url_map.iter_rules())
        
        logger.info(f"Found existing endpoints: {', '.join(existing_endpoints)}")
        
        # Check for Flask-Login
        using_flask_login = False
        try:
            from flask_login import LoginManager, login_user, current_user
            using_flask_login = True
            logger.info("Flask-Login is available")
        except ImportError:
            logger.info("Flask-Login not detected")
        
        # DON'T add a login route if one already exists
        if 'login' not in existing_endpoints and '/login' not in existing_rules:
            logger.info("SKIPPING login route creation to avoid conflicts with existing auth system")
        
        # Instead of adding routes, fix the database compatibility issues only
        logger.info("Focus on SQLAlchemy compatibility only - not adding any routes")
        
        return True
    except Exception as e:
        logger.error(f"Error in fix_flask_routes: {e}")
        return False

def apply_all_fixes(app=None):
    """Apply all fixes"""
    # Fix SQLAlchemy
    fix_sqlalchemy()
    
    # Fix Flask routes if app is provided - BUT DON'T MODIFY ROUTES
    if app:
        logger.info("Checking app configuration...")
        # Just check if app has secret_key (needed for sessions)
        if not app.secret_key:
            app.secret_key = os.urandom(24)
            logger.info("Added Flask secret_key for session support")
        
        # Don't actually modify any routes - just fix SQLAlchemy
        # fix_flask_routes(app)
    
    logger.info("Applied compatibility fixes")
    return True
