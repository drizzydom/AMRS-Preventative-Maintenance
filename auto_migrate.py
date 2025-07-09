from models import db
import sqlalchemy
from sqlalchemy import inspect, text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_column_if_not_exists(engine, table, column, coltype):
    inspector = inspect(engine)
    try:
        existing_columns = [col['name'] for col in inspector.get_columns(table)]
        if column not in existing_columns:
            with engine.connect() as conn:
                try:
                    # Use transaction to ensure atomic operation
                    trans = conn.begin()
                    conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {coltype}'))
                    trans.commit()
                    logger.info(f"[AUTO_MIGRATE] Added column {column} to {table}")
                except Exception as e:
                    trans.rollback()
                    logger.error(f"[AUTO_MIGRATE] Error adding column {column} to {table}: {e}")
                    raise
        else:
            logger.info(f"[AUTO_MIGRATE] Column {column} already exists in {table}")
    except Exception as e:
        logger.error(f"[AUTO_MIGRATE] Error checking/adding column {column} to {table}: {e}")
        raise

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
            
def create_maintenance_files_table(engine):
    inspector = inspect(engine)
    if 'maintenance_files' not in inspector.get_table_names():
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                conn.execute(text('''
                    CREATE TABLE maintenance_files (
                        id SERIAL PRIMARY KEY,
                        maintenance_record_id INTEGER NOT NULL REFERENCES maintenance_records(id) ON DELETE CASCADE,
                        filename VARCHAR(255) NOT NULL,
                        filepath VARCHAR(512) NOT NULL,
                        filetype VARCHAR(50) NOT NULL,
                        filesize INTEGER NOT NULL,
                        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        thumbnail_path VARCHAR(512)
                    )
                '''))
                trans.commit()
                logger.info("[AUTO_MIGRATE] Created table maintenance_files")
            except Exception as e:
                trans.rollback()
                logger.error(f"[AUTO_MIGRATE] Error creating maintenance_files table: {e}")
                raise
    else:
        logger.info("[AUTO_MIGRATE] Table maintenance_files already exists")

def run_auto_migration():
    from app import app  # Import here to avoid circular import
    with app.app_context():
        db.create_all()
        engine = db.engine
        
        # Critical migration: Ensure decommissioned fields exist first
        critical_fields = [
            ('machines', 'decommissioned', 'BOOLEAN DEFAULT FALSE NOT NULL'),
            ('machines', 'decommissioned_date', 'TIMESTAMP NULL'),
            ('machines', 'decommissioned_by', 'INTEGER NULL'),
            ('machines', 'decommissioned_reason', 'TEXT NULL')
        ]
        
        logger.info("[AUTO_MIGRATE] Starting critical decommissioned fields migration...")
        for table, column, coltype in critical_fields:
            try:
                add_column_if_not_exists(engine, table, column, coltype)
            except Exception as e:
                logger.error(f"[AUTO_MIGRATE] CRITICAL ERROR: Failed to add {table}.{column}: {e}")
                raise  # Re-raise to prevent app startup with missing critical columns
        
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
        # Ensure users table has remember me columns
        add_column_if_not_exists(engine, 'users', 'remember_token', 'VARCHAR(100)')
        add_column_if_not_exists(engine, 'users', 'remember_token_expiration', 'TIMESTAMP')
        add_column_if_not_exists(engine, 'users', 'remember_enabled', 'BOOLEAN DEFAULT FALSE')
        
        # Add your new database migrations here
        create_maintenance_files_table(engine)
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
