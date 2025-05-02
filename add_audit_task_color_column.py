#!/usr/bin/env python3
"""
Script to add the color column to the audit_tasks table for per-site color wheel support.
"""

import os
import sys
import traceback
from db_config import get_engine
from sqlalchemy import text

def add_audit_task_color_column():
    """Add the color column to the audit_tasks table."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Check if the column already exists
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='audit_tasks' AND column_name='color'
            """))
            if result.fetchone():
                print("Column 'color' already exists in 'audit_tasks'.")
                return True
            print("Adding 'color' column to 'audit_tasks' table...")
            conn.execute(text("""
                ALTER TABLE audit_tasks ADD COLUMN color VARCHAR(32)
            """))
            print("Column 'color' added successfully.")
        return True
    except Exception as e:
        print(f"Error adding color column to audit_tasks table: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_audit_task_color_column()
    sys.exit(0 if success else 1)
