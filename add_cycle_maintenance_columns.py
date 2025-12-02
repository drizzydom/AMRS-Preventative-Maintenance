#!/usr/bin/env python3
"""
Migration script to add cycle-based maintenance columns to machines and parts tables.
Run this once to add support for cycle-based maintenance scheduling.
"""

import sqlite3
import os
import sys

def get_db_path():
    """Get the database path from environment or default."""
    # Check for different possible database locations
    possible_paths = [
        os.path.join(os.path.dirname(__file__), 'instance', 'maintenance.db'),
        os.path.join(os.path.dirname(__file__), 'maintenance.db'),
        os.environ.get('DATABASE_PATH', ''),
    ]
    
    for path in possible_paths:
        if path and os.path.exists(path):
            return path
    
    # Default to instance folder
    return os.path.join(os.path.dirname(__file__), 'instance', 'maintenance.db')

def column_exists(cursor, table, column):
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns

def migrate_database():
    """Add cycle-based maintenance columns to the database."""
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        print("Please run the application first to create the database.")
        return False
    
    print(f"Migrating database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Machine table columns
        machine_columns = [
            ("cycle_count", "INTEGER DEFAULT 0"),
            ("last_cycle_update", "DATETIME"),
        ]
        
        # Part table columns
        part_columns = [
            ("maintenance_cycle_frequency", "INTEGER"),
            ("last_maintenance_cycle", "INTEGER DEFAULT 0"),
            ("next_maintenance_cycle", "INTEGER"),
        ]
        
        changes_made = 0
        
        # Add machine columns
        print("\nChecking machines table...")
        for col_name, col_type in machine_columns:
            if not column_exists(cursor, 'machines', col_name):
                print(f"  Adding column: {col_name}")
                cursor.execute(f"ALTER TABLE machines ADD COLUMN {col_name} {col_type}")
                changes_made += 1
            else:
                print(f"  Column {col_name} already exists")
        
        # Add part columns
        print("\nChecking parts table...")
        for col_name, col_type in part_columns:
            if not column_exists(cursor, 'parts', col_name):
                print(f"  Adding column: {col_name}")
                cursor.execute(f"ALTER TABLE parts ADD COLUMN {col_name} {col_type}")
                changes_made += 1
            else:
                print(f"  Column {col_name} already exists")
        
        conn.commit()
        conn.close()
        
        if changes_made > 0:
            print(f"\n✅ Migration complete! Added {changes_made} new column(s).")
        else:
            print("\n✅ No changes needed - all columns already exist.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
