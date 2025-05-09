#!/usr/bin/env python3
"""
Mock Online Database Manager

This script creates and manages a mock "online" database for testing
synchronization between online and offline databases.
"""
import os
import sys
import logging
import argparse
import json
from datetime import datetime
from pathlib import Path

# Add the current directory to the path to import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from db_controller import DatabaseController
except ImportError:
    print("Failed to import DatabaseController. Make sure db_controller.py is in the current directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[MOCK_ONLINE_DB] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mock_online_db.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mock_online_db")

class MockOnlineDB:
    """
    Manager for a mock online database to test synchronization
    """
    
    def __init__(self, db_path=None, use_encryption=False):
        """Initialize the mock online database manager"""
        if db_path is None:
            # Use default path in instance directory
            instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
            os.makedirs(instance_dir, exist_ok=True)
            db_path = os.path.join(instance_dir, 'mock_online.db')
            
        self.db_path = db_path
        self.db_controller = DatabaseController(db_path=db_path, use_encryption=use_encryption)
        logger.info(f"Initialized mock online database at {db_path}")
        
    def initialize_database(self):
        """Initialize the database schema"""
        try:
            # Create roles table if it doesn't exist
            if not self.db_controller.table_exists('roles'):
                logger.info("Creating roles table")
                self.db_controller.execute_query('''
                CREATE TABLE roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    permissions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                # Create default roles
                admin_role_id = self.db_controller.execute_query(
                    "INSERT INTO roles (name, description, permissions) VALUES (?, ?, ?)",
                    ('admin', 'Administrator', 'admin.full')
                ).lastrowid
                
                tech_role_id = self.db_controller.execute_query(
                    "INSERT INTO roles (name, description, permissions) VALUES (?, ?, ?)",
                    ('technician', 'Maintenance Technician', 'tech.full')
                ).lastrowid
                
                logger.info("Created default roles")
            
            # Create users table if it doesn't exist
            if not self.db_controller.table_exists('users'):
                logger.info("Creating users table")
                self.db_controller.execute_query('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    username_hash TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL UNIQUE,
                    email_hash TEXT NOT NULL UNIQUE,
                    full_name TEXT,
                    password_hash TEXT NOT NULL,
                    is_admin BOOLEAN DEFAULT 0,
                    role_id INTEGER,
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reset_token TEXT,
                    reset_token_expiration TIMESTAMP,
                    notification_preferences TEXT,
                    FOREIGN KEY (role_id) REFERENCES roles (id)
                )
                ''')
                
                # Get admin role
                role_result = self.db_controller.fetch_one("SELECT id FROM roles WHERE name = 'admin'")
                admin_role_id = role_result['id'] if role_result else 1
                
                # Create admin user
                self.db_controller.create_user(
                    username='admin',
                    email='admin@example.com',
                    full_name='Administrator',
                    password='admin',
                    is_admin=True,
                    role_id=admin_role_id
                )
                
                logger.info("Created default admin user")
            
            # Create maintenance_records table if it doesn't exist
            if not self.db_controller.table_exists('maintenance_records'):
                logger.info("Creating maintenance_records table")
                self.db_controller.execute_query('''
                CREATE TABLE maintenance_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    site_id INTEGER,
                    machine_id INTEGER,
                    maintenance_date TEXT,
                    technician_id INTEGER,
                    notes TEXT,
                    is_synced INTEGER DEFAULT 1,
                    client_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
            
            # Create sync_info table if it doesn't exist
            if not self.db_controller.table_exists('sync_info'):
                logger.info("Creating sync_info table")
                self.db_controller.execute_query('''
                CREATE TABLE sync_info (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
            
            return True
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return False
    
    def create_sample_data(self, count=5):
        """Create sample maintenance records"""
        try:
            # Create sample maintenance records
            for i in range(count):
                site_id = i + 1
                machine_id = i + 1
                maintenance_date = datetime.now().isoformat()
                notes = f"Sample online record {i+1}"
                
                self.db_controller.execute_query(
                    "INSERT INTO maintenance_records (site_id, machine_id, maintenance_date, technician_id, notes, is_synced) " +
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (site_id, machine_id, maintenance_date, 1, notes, 1)
                )
            
            logger.info(f"Created {count} sample maintenance records")
            return True
        except Exception as e:
            logger.error(f"Error creating sample data: {e}")
            return False
    
    def export_data_for_sync(self, output_file=None):
        """Export data to a JSON file for simulating sync to offline DB"""
        try:
            # Get all maintenance records
            records = self.db_controller.fetch_all("SELECT * FROM maintenance_records")
            
            # Convert records to list of dicts
            records_list = []
            for record in records:
                record_dict = dict(record)
                records_list.append(record_dict)
            
            # Create export data structure
            export_data = {
                'maintenance_records': records_list,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save to file if specified
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(export_data, f, indent=2)
                logger.info(f"Exported {len(records_list)} records to {output_file}")
            
            return export_data
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return None
    
    def import_data_from_offline(self, input_file=None, data=None):
        """Import data from a JSON file or dict to simulate sync from offline DB"""
        try:
            # Load data from file if specified
            if input_file and not data:
                with open(input_file, 'r') as f:
                    data = json.load(f)
            
            if not data:
                logger.error("No data provided for import")
                return False
            
            # Get offline records
            offline_records = data.get('maintenance_records', [])
            
            # Process each record
            imported_count = 0
            updated_count = 0
            
            for record in offline_records:
                # Check if record already exists by client_id
                if 'client_id' in record and record['client_id']:
                    existing = self.db_controller.fetch_one(
                        "SELECT id FROM maintenance_records WHERE client_id = ?",
                        (record['client_id'],)
                    )
                    
                    if existing:
                        # Update existing record
                        self.db_controller.execute_query(
                            "UPDATE maintenance_records SET site_id = ?, machine_id = ?, " +
                            "maintenance_date = ?, technician_id = ?, notes = ?, is_synced = 1, " +
                            "updated_at = CURRENT_TIMESTAMP WHERE client_id = ?",
                            (record['site_id'], record['machine_id'], record['maintenance_date'],
                             record['technician_id'], record['notes'], record['client_id'])
                        )
                        updated_count += 1
                    else:
                        # Insert new record
                        self.db_controller.execute_query(
                            "INSERT INTO maintenance_records (site_id, machine_id, maintenance_date, " +
                            "technician_id, notes, is_synced, client_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (record['site_id'], record['machine_id'], record['maintenance_date'],
                             record['technician_id'], record['notes'], 1, record['client_id'])
                        )
                        imported_count += 1
            
            logger.info(f"Imported {imported_count} new records and updated {updated_count} existing records")
            return True
        except Exception as e:
            logger.error(f"Error importing data: {e}")
            return False
    
    def close(self):
        """Close the database connection"""
        self.db_controller.close_connection()
        logger.info("Closed database connection")

def main():
    """Main function to manage mock online database"""
    parser = argparse.ArgumentParser(description='Mock Online Database Manager')
    parser.add_argument('--init', action='store_true', help='Initialize the database')
    parser.add_argument('--create-samples', type=int, metavar='COUNT', help='Create sample maintenance records')
    parser.add_argument('--export', metavar='FILE', help='Export data to a JSON file')
    parser.add_argument('--import', dest='import_file', metavar='FILE', help='Import data from a JSON file')
    parser.add_argument('--db-path', metavar='PATH', help='Path to the database file')
    
    args = parser.parse_args()
    
    # Create mock online database
    mock_db = MockOnlineDB(db_path=args.db_path)
    
    try:
        # Initialize database if requested
        if args.init:
            if mock_db.initialize_database():
                print("Database initialized successfully")
            else:
                print("Failed to initialize database")
        
        # Create sample data if requested
        if args.create_samples:
            if mock_db.create_sample_data(args.create_samples):
                print(f"Created {args.create_samples} sample maintenance records")
            else:
                print("Failed to create sample data")
        
        # Export data if requested
        if args.export:
            export_data = mock_db.export_data_for_sync(args.export)
            if export_data:
                print(f"Exported data to {args.export}")
            else:
                print("Failed to export data")
        
        # Import data if requested
        if args.import_file:
            if mock_db.import_data_from_offline(args.import_file):
                print(f"Imported data from {args.import_file}")
            else:
                print("Failed to import data")
    finally:
        # Close the database
        mock_db.close()

if __name__ == "__main__":
    main()
