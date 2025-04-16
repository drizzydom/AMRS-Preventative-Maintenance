"""
Database compatibility fix for Render deployment
"""
import os
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='[DB_FIX] %(message)s'
)
logger = logging.getLogger("fix_database")

def apply_all_fixes():
    """Apply all database compatibility fixes"""
    logger.info("Applying database compatibility fixes...")
    
    # 1. Apply SQLAlchemy compatibility patch
    from app_db_fix import patch_sqlalchemy
    sqlalchemy_patched = patch_sqlalchemy()
    
    # 2. Check for environment variables
    env_vars = [k for k in os.environ.keys() if any(term in k for term in ['DB', 'SQL', 'POSTGRES'])]
    if env_vars:
        logger.info(f"Found database-related environment variables: {', '.join(env_vars)}")
    else:
        logger.warning("No database-related environment variables found")
    
    # 3. Log SQLAlchemy version
    try:
        import sqlalchemy
        logger.info(f"SQLAlchemy version: {sqlalchemy.__version__}")
    except ImportError:
        logger.warning("SQLAlchemy not installed")
    
    logger.info("Database fixes applied successfully")
    return True

def patch_engine(engine):
    """
    Patch a specific SQLAlchemy engine for compatibility
    
    Args:
        engine: SQLAlchemy engine object
        
    Returns:
        Patched engine
    """
    try:
        import sqlalchemy
        if sqlalchemy.__version__.startswith('2.') and not hasattr(engine, 'execute'):
            logger.info("Patching specific engine with execute() method")
            
            def _execute(statement, *args, **kwargs):
                with engine.connect() as conn:
                    return conn.execute(statement, *args, **kwargs)
            
            engine.execute = _execute
    except Exception as e:
        logger.error(f"Error patching engine: {e}")
    
    return engine

# Apply fixes if run directly
if __name__ == "__main__":
    apply_all_fixes()
