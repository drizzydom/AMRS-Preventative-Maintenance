"""
Simple SQLAlchemy 2.x compatibility patch - adds execute() to Engine class
"""
import logging
from sqlalchemy import text, __version__

logging.basicConfig(level=logging.INFO, format='[SQLALCHEMY_COMPAT] %(message)s')
logger = logging.getLogger("sqlalchemy_compat")

# Only patch if using SQLAlchemy 2.x
if __version__.startswith("2."):
    try:
        from sqlalchemy.engine import Engine
        
        if not hasattr(Engine, "execute"):
            # Add missing execute() method to Engine class
            def _engine_execute(self, statement, *multiparams, **params):
                """Compatibility method for SQLAlchemy 1.x code"""
                # Convert string to text object if needed
                if isinstance(statement, str):
                    statement = text(statement)
                
                # Execute using SQLAlchemy 2.0 style
                with self.connect() as conn:
                    result = conn.execute(statement, *multiparams, **params)
                    try:
                        conn.commit()
                    except:
                        pass  # Some statements don't need commit
                    return result
            
            # Add method to Engine class
            Engine.execute = _engine_execute
            logger.info(f"Added execute() method to SQLAlchemy {__version__} Engine class")
    except Exception as e:
        logger.error(f"Failed to patch SQLAlchemy: {e}")
