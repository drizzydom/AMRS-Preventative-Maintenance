"""
Simple adapter for Render.
This file imports the app from app.py directly for Render deployment.
"""

import os
import sys
print("Initializing render_app.py for Render deployment...")

# Import the app and socketio from the main application FIRST
try:
    from app import app, socketio
    print("Successfully imported app and socketio from app.py")
except ImportError as e:
    print(f"Error importing from app.py: {e}")
    print(f"Python path: {sys.path}")
    print("Fatal error: Could not import application!")
    raise

# Now run auto migration after the app is available
# We need to avoid the circular import in auto_migrate.py
print("Running auto migration...")
try:
    # Import the database instance and run migration directly with our app
    from models import db
    from auto_migrate import (
        add_column_if_not_exists, 
        logger, 
        create_maintenance_files_table,
        run_data_fix,
        fix_audit_completions_timestamps
    )
    
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
        
        # Add maintenance files table
        create_maintenance_files_table(engine)
        
        # Run data fixes
        run_data_fix(engine, fix_audit_completions_timestamps, 
                    "Fix audit completion records with missing timestamps")
        
        # Run the dedicated color column migration
        try:
            from add_audit_task_color_column import add_audit_task_color_column
            add_audit_task_color_column()
            logger.info("[AUTO_MIGRATE] Ran dedicated audit_task color column migration")
        except Exception as e:
            logger.error(f"[AUTO_MIGRATE] Error running audit_task color column migration: {e}")
        
        logger.info("[AUTO_MIGRATE] Auto-migration complete.")
        print("Auto migration completed successfully")
        
except Exception as e:
    print(f"Error during auto migration: {e}")
    # Don't fail the entire deployment for migration issues
    pass
