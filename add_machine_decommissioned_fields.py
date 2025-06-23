#!/usr/bin/env python3
"""
Add decommissioned fields to machines table.
This migration adds columns to track when machines are decommissioned.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Flask app context
os.environ['FLASK_ENV'] = 'development'

from app import app, db
from sqlalchemy import text, inspect
from datetime import datetime

def add_decommissioned_columns():
    """Add decommissioned-related columns to machines table"""
    
    with app.app_context():
        print("Adding decommissioned fields to machines table...")
        
        try:
            # Check which columns already exist
            inspector = inspect(db.engine)
            existing_columns = [col['name'] for col in inspector.get_columns('machines')]
            
            # List of columns to add
            columns_to_add = [
                ('decommissioned', 'BOOLEAN DEFAULT FALSE NOT NULL'),
                ('decommissioned_date', 'TIMESTAMP NULL'),
                ('decommissioned_by', 'INTEGER NULL'),
                ('decommissioned_reason', 'TEXT NULL')
            ]
            
            with db.engine.connect() as conn:
                for column_name, column_definition in columns_to_add:
                    if column_name not in existing_columns:
                        print(f"Adding column: {column_name}")
                        conn.execute(text(f"ALTER TABLE machines ADD COLUMN {column_name} {column_definition}"))
                        conn.commit()
                        print(f"✓ Added {column_name} column")
                    else:
                        print(f"✓ Column {column_name} already exists")
                
                # Add foreign key constraint for decommissioned_by if it doesn't exist
                if 'decommissioned_by' not in existing_columns:
                    try:
                        print("Adding foreign key constraint for decommissioned_by...")
                        conn.execute(text("""
                            ALTER TABLE machines 
                            ADD CONSTRAINT fk_machines_decommissioned_by 
                            FOREIGN KEY (decommissioned_by) REFERENCES users (id)
                        """))
                        conn.commit()
                        print("✓ Added foreign key constraint")
                    except Exception as e:
                        print(f"Note: Could not add foreign key constraint: {str(e)}")
                        print("This is not critical, the column is still usable.")
            
            print("\n✅ Migration completed successfully!")
            print("All machines are now marked as active by default.")
            return True
            
        except Exception as e:
            print(f"❌ Error during migration: {str(e)}")
            return False

def verify_migration():
    """Verify that the migration was successful"""
    
    with app.app_context():
        print("\nVerifying migration...")
        
        try:
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('machines')]
            
            required_columns = ['decommissioned', 'decommissioned_date', 'decommissioned_by', 'decommissioned_reason']
            
            for column in required_columns:
                if column in columns:
                    print(f"✓ {column} column exists")
                else:
                    print(f"❌ {column} column missing")
                    return False
            
            # Test that we can query the table
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM machines WHERE decommissioned = FALSE"))
                active_count = result.scalar()
                print(f"✓ Found {active_count} active machines")
            
            print("✅ Migration verification successful!")
            return True
            
        except Exception as e:
            print(f"❌ Migration verification failed: {str(e)}")
            return False

if __name__ == "__main__":
    print("AMRS Machine Decommissioned Fields Migration")
    print("=" * 50)
    print("This will add decommissioned tracking fields to the machines table.")
    print("All existing machines will remain active by default.\n")
    
    response = input("Do you want to proceed with the migration? (y/N): ").strip().lower()
    if response == 'y':
        success = add_decommissioned_columns()
        if success:
            verify_migration()
        else:
            print("\n💥 Migration failed!")
    else:
        print("Migration cancelled.")
