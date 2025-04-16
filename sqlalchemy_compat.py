"""
Simple SQLAlchemy 2.x compatibility patch - adds execute() to Engine class
"""
import logging
from sqlalchemy import text, __version__

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sqlalchemy_compat")

# Only patch if using SQLAlchemy 2.x
if __version__.startswith("2."):
    try:
        from sqlalchemy.engine import Engine
        
        if not hasattr(Engine, "execute"):
            # Add missing execute() method to Engine class
            def _engine_execute(self, statement, *multiparams, **params):
                """Compatibility method for Engine.execute()"""
                # Convert string to text object if needed
                if isinstance(statement, str):
                    statement = text(statement)
                
                # Use SQLAlchemy 2.0 connect()/execute() pattern
                with self.connect() as conn:
                    return conn.execute(statement, *multiparams, **params)
            
            # Add method to Engine class
            Engine.execute = _engine_execute
            logger.info(f"Added execute() method to SQLAlchemy {__version__} Engine class")
    except Exception as e:
        logger.error(f"Failed to patch SQLAlchemy: {e}")
