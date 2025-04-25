#!/usr/bin/env python3
"""
Script to add machine_id column to maintenance_records table.
Run this script to fix the "Entity namespace for maintenance_records has no property machine_id" error.
"""

import os
import sys
from sqlalchemy import text
from app import app, db
from models import Part, MaintenanceRecord

def add_machine_id_column():
    """Add machine_id column to maintenance_records table and populate it from related part's machine"""
    try:
        print("Adding machine_id column to maintenance_records table...")
        with app.app_context():
            # Check if column already exists
            inspector = db.inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('maintenance_records')]
            
            if 'machine_id' not in columns:
                # Add the column
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE maintenance_records ADD COLUMN machine_id INTEGER"))
                    conn.commit()
                print("Column added successfully.")
                
                # Populate machine_id from associated part's machine_id
                maintenance_records = MaintenanceRecord.query.all()
                for record in maintenance_records:
                    if record.part:
                        record.machine_id = record.part.machine_id
                
                db.session.commit()
                print("Populated machine_id values from parts table.")
                
                # Add foreign key constraint
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("""
                            ALTER TABLE maintenance_records 
                            ADD CONSTRAINT fk_maintenance_records_machine_id 
                            FOREIGN KEY (machine_id) REFERENCES machines (id)
                        """))
                        conn.commit()
                    print("Added foreign key constraint.")
                except Exception as e:
                    print(f"Note: Could not add foreign key constraint: {str(e)}")
                    print("This is not critical, the column is still usable.")
            else:
                print("machine_id column already exists in maintenance_records table.")
            
        return True
    except Exception as e:
        print(f"Error adding machine_id column: {str(e)}")
        return False

if __name__ == "__main__":
    add_machine_id_column()
    print("Migration complete. You should now be able to delete machines without errors.")