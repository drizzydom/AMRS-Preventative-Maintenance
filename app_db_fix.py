"""
Direct patch for SQLAlchemy compatibility in app.py
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[APP_FIX] %(message)s'
)

logger = logging.getLogger("app_db_fix")

def patch_sqlalchemy():
    """
    Apply compatibility patch for SQLAlchemy
    This adds missing methods to SQLAlchemy 2.0 for backwards compatibility
    """
    try:
        # Only apply patch if using SQLAlchemy 2.0+
        import sqlalchemy
        if sqlalchemy.__version__.startswith('2.'):
            from sqlalchemy.engine.base import Engine
            
            # Add execute method to Engine class for backwards compatibility
            if not hasattr(Engine, 'execute'):
                def _engine_execute(self, statement, *args, **kwargs):
                    with self.connect() as conn:
                        return conn.execute(statement, *args, **kwargs)
                
                logger.info("Adding execute() method to SQLAlchemy Engine for compatibility")
                Engine.execute = _engine_execute
                return True
        return False
    except Exception as e:
        logger.error(f"Failed to patch SQLAlchemy: {e}")
        return False

def fix_database_connection():
    """Apply all database connection fixes"""
    patched = patch_sqlalchemy()
    if patched:
        logger.info("Successfully applied SQLAlchemy compatibility patches")
    return patched

# Apply fixes if run directly
if __name__ == "__main__":
    fix_database_connection()
    
    # Also dump environment for debugging
    logger.info("Environment variables:")
    for key in sorted(os.environ):
        if any(term in key.upper() for term in ['DB', 'SQL', 'POSTGRES', 'DATABASE']):
            logger.info(f"  {key}={os.environ[key]}")
