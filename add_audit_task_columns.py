#!/usr/bin/env python3
"""
Script to add the interval and custom_interval_days columns to the audit_tasks table.
Run this script to fix the "column audit_tasks.interval does not exist" error.
"""

import os
import sys
import traceback
from sqlalchemy import create_engine, text, inspect

def add_audit_task_columns():
    """Add the interval and custom_interval_days columns to the audit_tasks table."""
    try:
        # Get the database URL from environment variables
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("DATABASE_URL environment variable not set.")
            return False
            
        # Create an engine for database connection
        engine = create_engine(database_url)
        
        # Check if columns already exist
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('audit_tasks')]
        
        with engine.connect() as conn:
            if 'interval' not in columns:
                print("Adding interval column to audit_tasks table...")
                conn.execute(text("ALTER TABLE audit_tasks ADD COLUMN interval VARCHAR(20) DEFAULT 'daily'"))
                conn.commit()
                print("interval column added successfully.")
            else:
                print("The interval column already exists in the audit_tasks table.")
                
            if 'custom_interval_days' not in columns:
                print("Adding custom_interval_days column to audit_tasks table...")
                conn.execute(text("ALTER TABLE audit_tasks ADD COLUMN custom_interval_days INTEGER"))
                conn.commit()
                print("custom_interval_days column added successfully.")
            else:
                print("The custom_interval_days column already exists in the audit_tasks table.")
                
        return True
    except Exception as e:
        print(f"Error adding columns to audit_tasks table: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_audit_task_columns()
    sys.exit(0 if success else 1)