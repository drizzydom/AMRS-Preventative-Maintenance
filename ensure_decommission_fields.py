#!/usr/bin/env python3
"""
Dedicated script to ensure decommissioned fields exist in the machines table.
This should be run before the main application starts to avoid schema errors.
"""

import sys
import os
import logging

# Add current directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text, inspect
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_decommission_fields():
    """Ensure all decommissioned fields exist in the machines table"""
    try:
        # Create engine directly using the database URL
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        # Check if machines table exists first
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'machines' not in tables:
            logger.info("Machines table does not exist yet, will be created by SQLAlchemy")
            return True
            
        # Get existing columns
        existing_columns = [col['name'] for col in inspector.get_columns('machines')]
        logger.info(f"Existing columns in machines table: {existing_columns}")
        
        # Define the fields we need to add
        fields_to_add = [
            ('decommissioned', 'BOOLEAN DEFAULT FALSE NOT NULL'),
            ('decommissioned_date', 'TIMESTAMP NULL'),
            ('decommissioned_by', 'INTEGER NULL'),
            ('decommissioned_reason', 'TEXT NULL')
        ]
        
        added_columns = []
        
        with engine.connect() as conn:
            for field_name, field_type in fields_to_add:
                if field_name not in existing_columns:
                    try:
                        trans = conn.begin()
                        sql = f'ALTER TABLE machines ADD COLUMN {field_name} {field_type}'
                        logger.info(f"Executing: {sql}")
                        conn.execute(text(sql))
                        trans.commit()
                        added_columns.append(field_name)
                        logger.info(f"Successfully added column: {field_name}")
                    except Exception as e:
                        trans.rollback()
                        logger.error(f"Failed to add column {field_name}: {e}")
                        return False
                else:
                    logger.info(f"Column {field_name} already exists")
        
        if added_columns:
            logger.info(f"Successfully added columns: {added_columns}")
        else:
            logger.info("All decommissioned fields already exist")
            
        return True
        
    except Exception as e:
        logger.error(f"Error ensuring decommission fields: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = ensure_decommission_fields()
    sys.exit(0 if success else 1)
