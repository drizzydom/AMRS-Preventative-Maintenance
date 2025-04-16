"""
SQLAlchemy 2.0 compatibility layer
"""
import logging
from sqlalchemy import text, __version__

# Configure a logger
logger = logging.getLogger("sqlalchemy_compat")

# Check SQLAlchemy version
IS_SQLALCHEMY_2 = __version__.startswith("2.")
logger.info(f"SQLAlchemy version: {__version__}")

def patch_sqlalchemy():
    """
    Apply SQLAlchemy 2.0 compatibility patches
    """
    if IS_SQLALCHEMY_2:
        from sqlalchemy.engine import Engine
        
        # If Engine doesn't have execute method, add it
        if not hasattr(Engine, "execute"):
            # Define a compatibility method
            def _execute(self, statement, *multiparams, **params):
                """
                Execute a statement and return a result object
                
                This emulates SQLAlchemy 1.x behavior on SQLAlchemy 2.x
                """
                # Convert string statements to text objects
                if isinstance(statement, str):
                    statement = text(statement)
                
                # Use the new execution style through a connection
                with self.connect() as conn:
                    result = conn.execute(statement, *multiparams, **params)
                    return result
                
            # Add method to Engine class
            Engine.execute = _execute
            logger.info("Added SQLAlchemy 2.0 compatibility execute() method to Engine class")
            
            return True
    return False

# Apply patch when module is imported
patched = patch_sqlalchemy()
