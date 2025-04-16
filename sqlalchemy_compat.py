"""
Simple compatibility patch for SQLAlchemy 2.0+

This script adds back the execute() method that was removed in SQLAlchemy 2.0
to maintain compatibility with code written for SQLAlchemy 1.x.
"""
import logging
import sqlalchemy

logger = logging.getLogger("sqlalchemy_compat")

def patch_sqlalchemy():
    """
    Apply compatibility patches for SQLAlchemy 2.0+
    """
    # Only apply the patch if using SQLAlchemy 2.x
    if sqlalchemy.__version__.startswith("2."):
        logger.info(f"Patching SQLAlchemy {sqlalchemy.__version__} for backward compatibility")
        
        # Import the Engine class
        from sqlalchemy.engine import Engine
        
        # Only add the method if it doesn't already exist
        if not hasattr(Engine, "execute"):
            # Define a compatibility execute() method
            def _execute(self, statement, *multiparams, **params):
                """
                Compatibility method for SQLAlchemy 1.x-style execute()
                
                This mimics the behavior of the execute() method in SQLAlchemy 1.x
                """
                with self.connect() as conn:
                    result = conn.execute(statement, *multiparams, **params)
                    return result
                    
            # Add the method to the Engine class
            Engine.execute = _execute
            logger.info("Added execute() method to Engine class")
            return True
    
    return False

# Apply the patch when this module is imported
is_patched = patch_sqlalchemy()
