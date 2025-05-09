#!/usr/bin/env python3
"""
Initialize local offline database with sample data for testing
"""
import os
import sys
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='[INIT_DB] %(levelname)s - %(message)s')
logger = logging.getLogger("init_offline_db")

# Import local modules
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import local_database
from local_database import get_db_connection

# Set environment variables
os.environ['OFFLINE_MODE'] = 'true'
os.environ['USER_FIELD_ENCRYPTION_KEY'] = "_CY9_bO9vrX2CEUNmFqD1ETx-CluNejbidXFGMYapis="

# Configuration
DB_PATH = Path(os.path.join(current_dir, 'instance', 'maintenance.db'))
ENCRYPTION_KEY = "_CY9_bO9vrX2CEUNmFqD1ETx-CluNejbidXFGMYapis="

def create_sample_data():
    """Create sample data for the local database"""
    try:
        # Ensure the database directory exists
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Create tables
        local_database.create_tables(DB_PATH, ENCRYPTION_KEY)
        logger.info(f"Initialized database at {DB_PATH}")
        
        conn = get_db_connection(DB_PATH, ENCRYPTION_KEY)
        cursor = conn.cursor()
        
        # Create sample roles
        logger.info("Creating sample roles...")
        role_data = [
            {"id": 1, "name": "admin", "description": "Administrator", "permissions": "admin.full"},
            {"id": 2, "name": "technician", "description": "Maintenance Technician", "permissions": "tech.full"}
        ]
        
        for role in role_data:
            local_database.upsert_role_from_server(DB_PATH, ENCRYPTION_KEY, role)
            
        # Create sample sites
        logger.info("Creating sample sites...")
        site_data = [
            {"id": 1, "name": "Main Factory", "location": "Building A"},
            {"id": 2, "name": "Secondary Plant", "location": "Building B"}
        ]
        
        for site in site_data:
            local_database.upsert_site_from_server(DB_PATH, ENCRYPTION_KEY, site)
            
        # Create sample machines
        logger.info("Creating sample machines...")
        machine_data = [
            {"id": 1, "name": "CNC Machine 1", "model": "CNC-5000", "machine_number": "CN1001", "serial_number": "SN12345", "site_id": 1},
            {"id": 2, "name": "Lathe 1", "model": "LT-2000", "machine_number": "LT1001", "serial_number": "SN67890", "site_id": 1},
            {"id": 3, "name": "Drill Press", "model": "DP-1000", "machine_number": "DP1001", "serial_number": "SN24680", "site_id": 2}
        ]
        
        for machine in machine_data:
            local_database.upsert_machine_from_server(DB_PATH, ENCRYPTION_KEY, machine)
            
        # Create sample parts
        logger.info("Creating sample parts...")
        part_data = [
            {"id": 1, "name": "CNC Spindle", "description": "Main spindle assembly", "machine_id": 1},
            {"id": 2, "name": "CNC Coolant Pump", "description": "Coolant circulation system", "machine_id": 1},
            {"id": 3, "name": "Lathe Chuck", "description": "Primary chuck assembly", "machine_id": 2},
            {"id": 4, "name": "Drill Bit Set", "description": "Standard drill bit set", "machine_id": 3}
        ]
        
        for part in part_data:
            local_database.upsert_part_from_server(DB_PATH, ENCRYPTION_KEY, part)
            
        # Create sample audit tasks
        logger.info("Creating sample audit tasks...")
        task_data = [
            {"id": 1, "name": "Weekly Safety Check", "description": "Check all safety features", "site_id": 1, "interval": "weekly"},
            {"id": 2, "name": "Monthly Maintenance", "description": "Perform standard monthly maintenance", "site_id": 1, "interval": "monthly"},
            {"id": 3, "name": "Quarterly Inspection", "description": "Detailed quarterly inspection", "site_id": 2, "interval": "custom", "custom_interval_days": 90}
        ]
        
        for task in task_data:
            cursor.execute("""
                INSERT INTO audit_tasks (server_id, name, description, site_id, interval, custom_interval_days)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(server_id) DO UPDATE SET
                name=excluded.name, description=excluded.description
            """, (
                task["id"], task["name"], task["description"], task["site_id"], 
                task["interval"], task.get("custom_interval_days")
            ))
            
        conn.commit()
        logger.info("Sample data created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_sample_data()
    sys.exit(0 if success else 1)
