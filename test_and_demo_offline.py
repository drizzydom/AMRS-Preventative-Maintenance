#!/usr/bin/env python3
"""
Offline Mode Testing and Synchronization Demo

This script runs the offline mode tests and demonstrates how to synchronize
between offline and online databases.
"""
import os
import sys
import subprocess
import time
import json
from datetime import datetime

print("\n===== AMRS Preventative Maintenance - Offline Mode Testing and Demo =====\n")

# Define paths
WORKSPACE_ROOT = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(WORKSPACE_ROOT, 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)

ONLINE_DB_PATH = os.path.join(INSTANCE_DIR, 'demo_online.db')
OFFLINE_DB_PATH = os.path.join(INSTANCE_DIR, 'demo_offline.db')
SYNC_DATA_PATH = os.path.join(INSTANCE_DIR, 'sync_data.json')

# Step 1: Initialize mock online database
print("Step 1: Initializing mock online database...")
subprocess.run([
    sys.executable,
    os.path.join(WORKSPACE_ROOT, 'mock_online_db.py'),
    '--init',
    '--create-samples', '10',
    '--db-path', ONLINE_DB_PATH
])

# Step 2: Run offline mode tests
print("\nStep 2: Running offline mode tests...")
test_result = subprocess.run([
    sys.executable,
    os.path.join(WORKSPACE_ROOT, 'test_offline_mode.py')
])

if test_result.returncode != 0:
    print("\n❌ Tests failed, but continuing with demo...")
else:
    print("\n✅ Tests passed!")

# Step 3: Start a demonstration of synchronization
print("\nStep 3: Starting synchronization demonstration...")

# Remove existing demo offline database if it exists
if os.path.exists(OFFLINE_DB_PATH):
    os.remove(OFFLINE_DB_PATH)
    print(f"Removed existing offline database: {OFFLINE_DB_PATH}")

# Import necessary modules
sys.path.insert(0, WORKSPACE_ROOT)
try:
    from db_controller import DatabaseController
    from mock_online_db import MockOnlineDB
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)

# Initialize demo databases
print("\nInitializing demo databases...")
online_db = MockOnlineDB(db_path=ONLINE_DB_PATH)
online_db.initialize_database()

offline_db = DatabaseController(db_path=OFFLINE_DB_PATH, use_encryption=False)

# Initialize offline database
print("Creating schema in offline database...")
offline_db.execute_query('''
CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    permissions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

offline_db.execute_query('''
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
    notification_preferences TEXT
)
''')

offline_db.execute_query('''
CREATE TABLE maintenance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER,
    machine_id INTEGER,
    maintenance_date TEXT,
    technician_id INTEGER,
    notes TEXT,
    is_synced INTEGER DEFAULT 0,
    client_id TEXT,
    server_id INTEGER,
    sync_status TEXT DEFAULT 'pending',
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

offline_db.execute_query('''
CREATE TABLE sync_info (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Create admin role in offline database
offline_db.execute_query(
    "INSERT INTO roles (name, description, permissions) VALUES (?, ?, ?)",
    ('admin', 'Administrator', 'admin.full')
)

# Create admin user in offline database
offline_db.create_user(
    username='admin',
    email='admin@example.com',
    full_name='Administrator',
    password='admin',
    is_admin=True,
    role_id=1
)

# Create some offline-only records
print("\nCreating records in offline database...")
for i in range(5):
    client_id = f"offline-{datetime.now().timestamp()}-{i}"
    offline_db.execute_query(
        "INSERT INTO maintenance_records (site_id, machine_id, maintenance_date, technician_id, notes, is_synced, client_id) " +
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (100+i, 100+i, datetime.now().isoformat(), 1, f"Offline record {i+1} created on {datetime.now().isoformat()}", 0, client_id)
    )

# Step 4: Demonstrate downloading from online to offline
print("\nStep 4: Demonstrating download from online to offline...")

# Export data from online database
online_data = online_db.export_data_for_sync()
online_records = online_data['maintenance_records']

print(f"Found {len(online_records)} records in online database")

# Import online records into offline database
for record in online_records:
    # Check if record already exists
    existing = offline_db.fetch_one(
        "SELECT id FROM maintenance_records WHERE server_id = ?", 
        (record['id'],)
    )
    
    if not existing:
        # Insert as new record with server_id reference
        offline_db.execute_query(
            "INSERT INTO maintenance_records (site_id, machine_id, maintenance_date, technician_id, notes, " +
            "is_synced, server_id, sync_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (record['site_id'], record['machine_id'], record['maintenance_date'], 
             record['technician_id'], record['notes'], 1, record['id'], 'synced')
        )
        print(f"Imported record: Site {record['site_id']}, Machine {record['machine_id']}")

# Step 5: Demonstrate uploading from offline to online
print("\nStep 5: Demonstrating upload from offline to online...")

# Get offline records that need to be synced
offline_records = offline_db.fetch_all(
    "SELECT * FROM maintenance_records WHERE is_synced = 0"
)

print(f"Found {len(offline_records)} records in offline database pending sync")

# Convert offline records to a format for export
offline_export = {
    'maintenance_records': [],
    'timestamp': datetime.now().isoformat()
}

for record in offline_records:
    # Add to export list
    record_dict = dict(record)
    offline_export['maintenance_records'].append(record_dict)
    print(f"Prepared record for upload: {record_dict['notes']}")

# Write to JSON file for demonstration
with open(SYNC_DATA_PATH, 'w') as f:
    json.dump(offline_export, f, indent=2)

# Import the offline records into the online database
print("\nImporting offline records into online database...")
online_db.import_data_from_offline(data=offline_export)

# Update offline records to mark them as synced
for record in offline_records:
    offline_db.execute_query(
        "UPDATE maintenance_records SET is_synced = 1, sync_status = 'synced' WHERE id = ?",
        (record['id'],)
    )

# Step 6: Verify final state
print("\nStep 6: Verifying final state after synchronization...")

# Count records in online database
online_count = online_db.db_controller.fetch_one(
    "SELECT COUNT(*) FROM maintenance_records"
)[0]

# Count records in offline database
offline_count = offline_db.fetch_one(
    "SELECT COUNT(*) FROM maintenance_records"
)[0]

# Count synced records in offline database
synced_count = offline_db.fetch_one(
    "SELECT COUNT(*) FROM maintenance_records WHERE is_synced = 1"
)[0]

print(f"\nOnline database record count: {online_count}")
print(f"Offline database record count: {offline_count}")
print(f"Synced records in offline database: {synced_count}")

# Update last sync time
offline_db.update_last_sync_time()
last_sync = offline_db.get_last_sync_time()
print(f"Last sync time: {last_sync}")

# Clean up
print("\nCleaning up...")
online_db.close()
offline_db.close_connection()

print(f"\nDemo sync data saved to: {SYNC_DATA_PATH}")
print("\nDemonstration complete! You can now run the application and test offline functionality.")
print("\nTo run the offline application:")
print(f"  python {os.path.join(WORKSPACE_ROOT, 'run_offline_app.py')}")
print("\nTo login:")
print("  Username: admin")
print("  Password: admin")
