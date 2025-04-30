#!/usr/bin/env python3
"""
Script to add the color column to the audit_tasks table for per-site color wheel support.
"""

import os
import sys
import traceback
from sqlalchemy import create_engine, text, inspect

def add_audit_task_color_column():
    """Add the color column to the audit_tasks table."""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("DATABASE_URL environment variable not set.")
            return False
        engine = create_engine(database_url)
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('audit_tasks')]
        with engine.connect() as conn:
            if 'color' not in columns:
                print("Adding color column to audit_tasks table...")
                conn.execute(text("ALTER TABLE audit_tasks ADD COLUMN color VARCHAR(32)"))
                conn.commit()
                print("color column added successfully.")
            else:
                print("The color column already exists in the audit_tasks table.")
        return True
    except Exception as e:
        print(f"Error adding color column to audit_tasks table: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_audit_task_color_column()
    sys.exit(0 if success else 1)
