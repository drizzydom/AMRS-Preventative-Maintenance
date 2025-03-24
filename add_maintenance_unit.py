#!/usr/bin/env python3
"""
Script to add the maintenance_unit column to the part table.
Run this script to fix the "no such column: part.maintenance_unit" error.
"""

import sqlite3
import os
import sys

def add_maintenance_unit_column():
    """Add the maintenance_unit column to the part table."""
    # Path to the SQLite database
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'maintenance.db')
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return False
        
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists to avoid errors
        cursor.execute("PRAGMA table_info(part)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'maintenance_unit' not in columns:
            # Add the maintenance_unit column
            print("Adding maintenance_unit column to part table...")
            cursor.execute("ALTER TABLE part ADD COLUMN maintenance_unit VARCHAR(10) DEFAULT 'day'")
            conn.commit()
            print("Column added successfully.")
        else:
            print("The maintenance_unit column already exists in the part table.")
            
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding maintenance_unit column: {str(e)}")
        return False

if __name__ == "__main__":
    success = add_maintenance_unit_column()
    sys.exit(0 if success else 1)
