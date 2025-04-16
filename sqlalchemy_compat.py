"""
Simple SQLAlchemy 2.x compatibility patch

This adds the execute() method back to the Engine class for compatibility with code
written for SQLAlchemy 1.x
"""
import logging
from sqlalchemy import text, __version__

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='[SQLALCHEMY_COMPAT] %(message)s')
logger = logging.getLogger("sqlalchemy_compat")

def patch_sqlalchemy():
    """
    Patch SQLAlchemy 2.x to add back the execute() method on Engine objects
    """
    # Only patch if using SQLAlchemy 2.x
    if __version__.startswith("2."):
        try:
            from sqlalchemy.engine import Engine
            
            # Only add the method if it doesn't already exist
            if not hasattr(Engine, "execute"):
                def _execute(self, statement, *multiparams, **params):
                    """Compatibility execute method for SQLAlchemy 1.x code"""
                    # Convert string queries to text objects
                    if isinstance(statement, str):
                        statement = text(statement)
                    
                    # Execute using SQLAlchemy 2.0 style
                    with self.connect() as conn:
                        try:
                            result = conn.execute(statement, *multiparams, **params)
                            conn.commit()
                            return result
                        except Exception as e:
                            conn.rollback()
                            logger.error(f"Error executing SQL: {e}")
                            raise
                
                # Add the method to the Engine class
                Engine.execute = _execute
                logger.info(f"Patched SQLAlchemy {__version__} with compatibility execute() method")
                return True
            else:
                logger.info("Engine.execute() method already exists, no patching required")
                return False
        except Exception as e:
            logger.error(f"Failed to patch SQLAlchemy: {e}")
            return False
    else:
        logger.info(f"SQLAlchemy {__version__} does not require patching")
        return False

# Apply the patch when this module is imported
is_patched = patch_sqlalchemy()
