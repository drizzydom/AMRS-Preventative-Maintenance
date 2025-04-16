"""
Simple SQLAlchemy 2.x compatibility patch

This adds the execute() method back to the Engine class for compatibility with code
written for SQLAlchemy 1.x
"""
import logging

logger = logging.getLogger('sqlalchemy_patch')

def apply_patch():
    """
    Apply compatibility patch to SQLAlchemy 2.x
    
    This adds the execute() method back to the Engine class.
    """
    try:
        # Check SQLAlchemy version
        import sqlalchemy
        
        # Only apply patch for SQLAlchemy 2.x
        if sqlalchemy.__version__.startswith('2.'):
            from sqlalchemy.engine import Engine
            
            # Check if patch is needed
            if not hasattr(Engine, 'execute'):
                logger.info(f"Patching SQLAlchemy {sqlalchemy.__version__} Engine class with execute() method")
                
                # Add execute method
                def _execute(self, statement, *multiparams, **params):
                    with self.connect() as conn:
                        return conn.execute(statement, *multiparams, **params)
                
                # Add the method to the Engine class
                Engine.execute = _execute
                
                return True
        return False
    except ImportError:
        logger.warning("SQLAlchemy not found, patch not applied")
        return False
    except Exception as e:
        logger.error(f"Failed to apply SQLAlchemy patch: {e}")
        return False

# Apply the patch when the module is imported
patched = apply_patch()
