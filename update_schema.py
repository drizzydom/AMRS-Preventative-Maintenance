#!/usr/bin/env python3
"""
Simple script to update the database schema with new fields.
Run this if you're having trouble with the update-db-schema command.
"""

import sqlite3
import os

def update_database_schema():
    # Path to the SQLite database
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'maintenance.db')
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check Machine table columns
        cursor.execute("PRAGMA table_info(machine)")
        machine_columns = [col[1] for col in cursor.fetchall()]
        
        # Add machine_number if it doesn't exist
        if 'machine_number' not in machine_columns:
            cursor.execute("ALTER TABLE machine ADD COLUMN machine_number VARCHAR(100)")
            print("Added machine_number column")
        else:
            print("machine_number column already exists")
            
        # Add serial_number if it doesn't exist
        if 'serial_number' not in machine_columns:
            cursor.execute("ALTER TABLE machine ADD COLUMN serial_number VARCHAR(100)")
            print("Added serial_number column")
        else:
            print("serial_number column already exists")
        
        # Check Part table columns
        cursor.execute("PRAGMA table_info(part)")
        part_columns = [col[1] for col in cursor.fetchall()]
        
        # Add last_maintained_by if it doesn't exist
        if 'last_maintained_by' not in part_columns:
            cursor.execute("ALTER TABLE part ADD COLUMN last_maintained_by VARCHAR(100)")
            print("Added last_maintained_by column")
        else:
            print("last_maintained_by column already exists")
            
        # Add invoice_number if it doesn't exist
        if 'invoice_number' not in part_columns:
            cursor.execute("ALTER TABLE part ADD COLUMN invoice_number VARCHAR(50)")
            print("Added invoice_number column")
        else:
            print("invoice_number column already exists")
            
        conn.commit()
        conn.close()
        
        print("Database schema updated successfully")
        return True
    except Exception as e:
        print(f"Error updating database schema: {str(e)}")
        return False

if __name__ == "__main__":
    update_database_schema()
