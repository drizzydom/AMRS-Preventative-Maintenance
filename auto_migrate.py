from models import db
import sqlalchemy
from sqlalchemy import inspect, text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_column_if_not_exists(engine, table, column, coltype):
    inspector = inspect(engine)
    existing_columns = [col['name'] for col in inspector.get_columns(table)]
    if column not in existing_columns:
        with engine.connect() as conn:
            try:
                conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {coltype}'))
                logger.info(f"[AUTO_MIGRATE] Added column {column} to {table}")
            except Exception as e:
                logger.error(f"[AUTO_MIGRATE] Error adding column {column} to {table}: {e}")

def run_data_fix(engine, fix_function, description):
    """Run a data fix function and log the result"""
    try:
        fix_function(engine)
        logger.info(f"[AUTO_MIGRATE] Successfully ran fix: {description}")
    except Exception as e:
        logger.error(f"[AUTO_MIGRATE] Error running fix '{description}': {e}")

def fix_audit_completions_timestamps(engine):
    """Fix audit completion records that have completed=True but no completed_at timestamp"""
    with engine.connect() as conn:
        # Check if the relevant columns exist
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('audit_task_completions')]
        if 'completed' in columns and 'completed_at' in columns:
            # Update records with missing timestamps
            conn.execute(text(
                """
                UPDATE audit_task_completions 
                SET completed_at = created_at 
                WHERE completed = TRUE AND completed_at IS NULL
                """
            ))
            
def run_auto_migration():
    from app import app  # Import here to avoid circular import
    with app.app_context():
        db.create_all()
        engine = db.engine
        # Ensure audit_tasks columns
        add_column_if_not_exists(engine, 'audit_tasks', 'interval', "VARCHAR(20) DEFAULT 'daily'")
        add_column_if_not_exists(engine, 'audit_tasks', 'custom_interval_days', "INTEGER")
        add_column_if_not_exists(engine, 'audit_tasks', 'color', "VARCHAR(32) DEFAULT '#007bff'")
        # Ensure audit_task_completions columns
        add_column_if_not_exists(engine, 'audit_task_completions', 'created_at', "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        add_column_if_not_exists(engine, 'audit_task_completions', 'updated_at', "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        # Ensure users table has username_hash and email_hash columns
        add_column_if_not_exists(engine, 'users', 'username_hash', 'VARCHAR(64)')
        add_column_if_not_exists(engine, 'users', 'email_hash', 'VARCHAR(64)')
        
        # Ensure machines table has decommissioned fields
        add_column_if_not_exists(engine, 'machines', 'decommissioned', 'BOOLEAN DEFAULT FALSE NOT NULL')
        add_column_if_not_exists(engine, 'machines', 'decommissioned_date', 'TIMESTAMP NULL')
        add_column_if_not_exists(engine, 'machines', 'decommissioned_by', 'INTEGER NULL')
        add_column_if_not_exists(engine, 'machines', 'decommissioned_reason', 'TEXT NULL')
        
        # Add your new database migrations here
        
        # Run data fixes
        run_data_fix(engine, fix_audit_completions_timestamps, 
                    "Fix audit completion records with missing timestamps")
        
        # Explicitly run the color column migration from the dedicated script
        try:
            # Import and run the dedicated color column migration
            from add_audit_task_color_column import add_audit_task_color_column
            add_audit_task_color_column()
            logger.info("[AUTO_MIGRATE] Ran dedicated audit_task color column migration")
        except Exception as e:
            logger.error(f"[AUTO_MIGRATE] Error running audit_task color column migration: {e}")
        
        # Example of how to add more fixes:
        # run_data_fix(engine, fix_another_issue_function, "Description of the fix")
        
        logger.info("[AUTO_MIGRATE] Auto-migration complete.")

if __name__ == "__main__":
    run_auto_migration()
