#!/usr/bin/env python3
"""
Test script for local_database.py functionality.
This script tests the core offline database operations without running the full application.
"""

import logging
import os
from pathlib import Path
import sys
import time
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("local_db_test")

# Import local_database module - ensure we're in the right directory first
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import local_database

# Test configuration
TEST_DB_PATH = Path.home() / ".amrs_test_data/test_local_db.sqlite"
TEST_KEY = "testkey1234567890123456789012345678901234567890123456789012345"  # Test key only

# Ensure test directory exists
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Delete the test database if it exists to start fresh
if TEST_DB_PATH.exists():
    try:
        TEST_DB_PATH.unlink()
        logger.info(f"Deleted existing test database at {TEST_DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to delete existing test database: {e}")

def setup_db():
    """Initialize the test database and schema"""
    try:
        local_database.create_tables(TEST_DB_PATH, TEST_KEY)
        logger.info(f"Database initialized at {TEST_DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False
    return True

def create_test_data():
    """Create sample data for testing relations and queries"""
    try:
        # Create roles
        role_data = {
            "id": 1,  # Server ID for test
            "name": "Admin",
            "description": "Administrator role",
            "permissions": "admin"
        }
        local_database.upsert_role_from_server(TEST_DB_PATH, TEST_KEY, role_data)
        
        role_data = {
            "id": 2,
            "name": "Technician",
            "description": "Maintenance technician",
            "permissions": "tech"
        }
        local_database.upsert_role_from_server(TEST_DB_PATH, TEST_KEY, role_data)
        
        # Create users
        user_data = {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "full_name": "Admin User",
            "role_id": 1
        }
        local_database.upsert_user_from_server(TEST_DB_PATH, TEST_KEY, user_data)
        
        user_data = {
            "id": 2,
            "username": "tech1",
            "email": "tech1@example.com",
            "full_name": "Technician One",
            "role_id": 2
        }
        local_database.upsert_user_from_server(TEST_DB_PATH, TEST_KEY, user_data)
        
        # Create sites
        site_data = {
            "id": 1,
            "name": "Main Factory",
            "location": "Building 1"
        }
        local_database.upsert_site_from_server(TEST_DB_PATH, TEST_KEY, site_data)
        
        site_data = {
            "id": 2,
            "name": "Secondary Factory",
            "location": "Building 2"
        }
        local_database.upsert_site_from_server(TEST_DB_PATH, TEST_KEY, site_data)
        
        # Create machines
        machine_data = {
            "id": 1,
            "name": "CNC Mill A",
            "model": "CNC-5000",
            "machine_number": "M1001",
            "serial_number": "SN12345",
            "site_id": 1
        }
        local_database.upsert_machine_from_server(TEST_DB_PATH, TEST_KEY, machine_data)
        
        machine_data = {
            "id": 2,
            "name": "Lathe B",
            "model": "LT-2000",
            "machine_number": "M1002",
            "serial_number": "SN67890",
            "site_id": 1
        }
        local_database.upsert_machine_from_server(TEST_DB_PATH, TEST_KEY, machine_data)
        
        machine_data = {
            "id": 3,
            "name": "Grinder C",
            "model": "GR-1000",
            "machine_number": "M2001",
            "serial_number": "SN11223",
            "site_id": 2
        }
        local_database.upsert_machine_from_server(TEST_DB_PATH, TEST_KEY, machine_data)
        
        # Create parts
        part_data = {
            "id": 1,
            "name": "Spindle",
            "description": "Main spindle assembly",
            "machine_id": 1,
            "maintenance_frequency": 90,
            "maintenance_unit": "day"
        }
        local_database.upsert_part_from_server(TEST_DB_PATH, TEST_KEY, part_data)
        
        part_data = {
            "id": 2,
            "name": "Hydraulic Pump",
            "description": "Main hydraulic pump",
            "machine_id": 1,
            "maintenance_frequency": 180,
            "maintenance_unit": "day"
        }
        local_database.upsert_part_from_server(TEST_DB_PATH, TEST_KEY, part_data)
        
        part_data = {
            "id": 3,
            "name": "Chuck Assembly",
            "description": "Main chuck",
            "machine_id": 2,
            "maintenance_frequency": 60,
            "maintenance_unit": "day"
        }
        local_database.upsert_part_from_server(TEST_DB_PATH, TEST_KEY, part_data)
        
        part_data = {
            "id": 4,
            "name": "Grinding Wheel",
            "description": "Main grinding wheel",
            "machine_id": 3,
            "maintenance_frequency": 30,
            "maintenance_unit": "day"
        }
        local_database.upsert_part_from_server(TEST_DB_PATH, TEST_KEY, part_data)
        
        # Create audit tasks
        audit_task_data = {
            "id": 1,
            "name": "Daily Safety Check",
            "description": "Check safety equipment",
            "site_id": 1,
            "created_by": 1,
            "interval": "daily"
        }
        local_database.upsert_audit_task_from_server(TEST_DB_PATH, TEST_KEY, audit_task_data)
        
        audit_task_data = {
            "id": 2,
            "name": "Weekly Oil Check",
            "description": "Check oil levels",
            "site_id": 1,
            "created_by": 1,
            "interval": "weekly"
        }
        local_database.upsert_audit_task_from_server(TEST_DB_PATH, TEST_KEY, audit_task_data)
        
        logger.info("Sample data created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create sample data: {e}")
        return False

def test_maintenance_record_crud():
    """Test CRUD operations for maintenance records"""
    logger.info("Testing maintenance record CRUD operations...")
    try:
        # Get local IDs for FKs
        local_part_id = local_database.get_local_id_from_server_id(TEST_DB_PATH, TEST_KEY, "parts", 1)
        local_user_id = local_database.get_local_id_from_server_id(TEST_DB_PATH, TEST_KEY, "users", 1)
        local_machine_id = local_database.get_local_id_from_server_id(TEST_DB_PATH, TEST_KEY, "machines", 1)
        
        # 1. CREATE: Create a new maintenance record
        record_data = {
            "part_id": local_part_id,
            "user_id": local_user_id,
            "machine_id": local_machine_id,
            "date": "2025-05-09T12:00:00Z",
            "comments": "Initial test maintenance",
            "maintenance_type": "Preventative",
            "description": "Regular maintenance check",
            "performed_by": "Admin User",
            "status": "Completed",
            "notes": "No issues found"
        }
        
        client_id = local_database.create_local_maintenance_record(TEST_DB_PATH, TEST_KEY, record_data)
        if not client_id:
            logger.error("Failed to create maintenance record")
            return False
        
        logger.info(f"Created maintenance record with client_id: {client_id}")
        
        # 2. READ: Verify record exists and fields are correct
        records = local_database.get_all_local_records(TEST_DB_PATH, TEST_KEY, "maintenance_records")
        if not records or len(records) == 0:
            logger.error("No maintenance records found after creation")
            return False
        
        created_record = next((r for r in records if r["client_id"] == client_id), None)
        if not created_record:
            logger.error(f"Couldn't find created record with client_id {client_id}")
            return False
        
        if created_record["comments"] != "Initial test maintenance":
            logger.error(f"Record data mismatch. Expected 'Initial test maintenance', got '{created_record['comments']}'")
            return False
        
        logger.info(f"Successfully read maintenance record: {created_record['id']}")
        
        # 3. UPDATE: Update the record
        update_data = {
            "comments": "Updated maintenance notes",
            "status": "In Progress",
            "notes": "Found issue with bearings"
        }
        
        success = local_database.update_local_maintenance_record(TEST_DB_PATH, TEST_KEY, client_id, update_data)
        if not success:
            logger.error("Failed to update maintenance record")
            return False
        
        # Verify update
        updated_records = local_database.get_all_local_records(TEST_DB_PATH, TEST_KEY, "maintenance_records")
        updated_record = next((r for r in updated_records if r["client_id"] == client_id), None)
        
        if updated_record["comments"] != "Updated maintenance notes" or updated_record["status"] != "In Progress":
            logger.error("Record not updated correctly")
            return False
        
        # Verify record is marked as unsynced
        if updated_record["is_synced"] != 0:
            logger.error("Updated record should be marked as unsynced (is_synced=0)")
            return False
        
        logger.info(f"Successfully updated maintenance record: {updated_record['id']}")
        
        # 4. Test retrieve unsynced records 
        unsynced = local_database.get_unsynced_maintenance_records(TEST_DB_PATH, TEST_KEY)
        if not unsynced or len(unsynced) == 0:
            logger.error("No unsynced maintenance records found")
            return False
            
        logger.info(f"Found {len(unsynced)} unsynced maintenance records")
        
        # 5. Test update_sync_status
        server_id = 1001  # Example server ID that would be returned from server
        current_ts = local_database._get_current_timestamp_iso()
        local_database.update_sync_status(TEST_DB_PATH, TEST_KEY, "maintenance_records", client_id, server_id, current_ts)
        
        # Verify record is now marked as synced
        synced_records = local_database.get_all_local_records(TEST_DB_PATH, TEST_KEY, "maintenance_records")
        synced_record = next((r for r in synced_records if r["client_id"] == client_id), None)
        
        if synced_record["is_synced"] != 1 or synced_record["server_id"] != server_id:
            logger.error("Record not properly marked as synced")
            return False
        
        logger.info(f"Successfully marked record as synced with server_id: {server_id}")
        logger.info("✅ Maintenance record CRUD tests passed")
        return True
        
    except Exception as e:
        logger.error(f"Error in maintenance record CRUD test: {e}")
        return False

def test_audit_task_completion_crud():
    """Test CRUD operations for audit task completions"""
    logger.info("Testing audit task completion CRUD operations...")
    try:
        # Get local IDs for FKs
        local_audit_task_id = local_database.get_local_id_from_server_id(TEST_DB_PATH, TEST_KEY, "audit_tasks", 1)
        local_user_id = local_database.get_local_id_from_server_id(TEST_DB_PATH, TEST_KEY, "users", 2)  # Use tech1 
        local_machine_id = local_database.get_local_id_from_server_id(TEST_DB_PATH, TEST_KEY, "machines", 1)
        
        # 1. CREATE: Create a new audit task completion
        completion_data = {
            "audit_task_id": local_audit_task_id,
            "machine_id": local_machine_id,
            "date": "2025-05-09T14:30:00Z",
            "completed": 1,
            "completed_by": local_user_id,
            "completed_at": "2025-05-09T14:45:00Z"
        }
        
        client_id = local_database.create_local_audit_task_completion(TEST_DB_PATH, TEST_KEY, completion_data)
        if not client_id:
            logger.error("Failed to create audit task completion")
            return False
        
        logger.info(f"Created audit task completion with client_id: {client_id}")
        
        # 2. READ: Verify completion exists
        completions = local_database.get_all_local_records(TEST_DB_PATH, TEST_KEY, "audit_task_completions")
        if not completions or len(completions) == 0:
            logger.error("No audit task completions found after creation")
            return False
        
        created_completion = next((c for c in completions if c["client_id"] == client_id), None)
        if not created_completion:
            logger.error(f"Couldn't find created completion with client_id {client_id}")
            return False
        
        logger.info(f"Successfully read audit task completion: {created_completion['id']}")
        
        # 3. UPDATE: Update the completion
        update_data = {
            "completed": 0,  # Mark as not completed
        }
        
        success = local_database.update_local_audit_task_completion(TEST_DB_PATH, TEST_KEY, client_id, update_data)
        if not success:
            logger.error("Failed to update audit task completion")
            return False
        
        # Verify update
        updated_completions = local_database.get_all_local_records(TEST_DB_PATH, TEST_KEY, "audit_task_completions")
        updated_completion = next((c for c in updated_completions if c["client_id"] == client_id), None)
        
        if updated_completion["completed"] != 0:
            logger.error("Completion not updated correctly")
            return False
        
        # Verify completion is marked as unsynced
        if updated_completion["is_synced"] != 0:
            logger.error("Updated completion should be marked as unsynced (is_synced=0)")
            return False
        
        logger.info(f"Successfully updated audit task completion: {updated_completion['id']}")
        
        # 4. Test retrieve unsynced completions
        unsynced = local_database.get_unsynced_audit_task_completions(TEST_DB_PATH, TEST_KEY)
        if not unsynced or len(unsynced) == 0:
            logger.error("No unsynced audit task completions found")
            return False
            
        logger.info(f"Found {len(unsynced)} unsynced audit task completions")
        
        # 5. Test update_sync_status
        server_id = 2001  # Example server ID
        current_ts = local_database._get_current_timestamp_iso()
        local_database.update_sync_status(TEST_DB_PATH, TEST_KEY, "audit_task_completions", client_id, server_id, current_ts)
        
        # Verify completion is now marked as synced
        synced_completions = local_database.get_all_local_records(TEST_DB_PATH, TEST_KEY, "audit_task_completions")
        synced_completion = next((c for c in synced_completions if c["client_id"] == client_id), None)
        
        if synced_completion["is_synced"] != 1 or synced_completion["server_id"] != server_id:
            logger.error("Completion not properly marked as synced")
            return False
        
        logger.info(f"Successfully marked completion as synced with server_id: {server_id}")
        logger.info("✅ Audit task completion CRUD tests passed")
        return True
        
    except Exception as e:
        logger.error(f"Error in audit task completion CRUD test: {e}")
        return False

def test_queries():
    """Test various query functionality"""
    logger.info("Testing query functionality...")
    try:
        # 1. Test get_local_records_by_fk
        local_machine_id = local_database.get_local_id_from_server_id(TEST_DB_PATH, TEST_KEY, "machines", 1)
        parts = local_database.get_local_records_by_fk(TEST_DB_PATH, TEST_KEY, "parts", "machine_id", local_machine_id)
        
        if not parts or len(parts) != 2:  # We created 2 parts for machine 1
            logger.error(f"Expected 2 parts for machine_id {local_machine_id}, got {len(parts)}")
            return False
            
        logger.info(f"Successfully queried parts by machine_id: {local_machine_id}")
        
        # 2. Test get_all_local_records with ordering
        sites = local_database.get_all_local_records(TEST_DB_PATH, TEST_KEY, "sites", order_by="name DESC")
        if not sites or len(sites) != 2:
            logger.error(f"Expected 2 sites, got {len(sites)}")
            return False
            
        # Secondary should come before Main with DESC ordering
        if sites[0]["name"] != "Secondary Factory" or sites[1]["name"] != "Main Factory":
            logger.error(f"Order by failed. Expected Secondary Factory first, got {sites[0]['name']}")
            return False
            
        logger.info("Successfully queried all sites with ordering")
        
        # 3. Test sync metadata
        current_ts = local_database._get_current_timestamp_iso()
        local_database.update_last_sync_timestamp(TEST_DB_PATH, TEST_KEY, current_ts)
        
        retrieved_ts = local_database.get_last_sync_timestamp(TEST_DB_PATH, TEST_KEY)
        if retrieved_ts != current_ts:
            logger.error(f"Expected sync timestamp {current_ts}, got {retrieved_ts}")
            return False
            
        logger.info("Successfully updated and retrieved sync timestamp")
        logger.info("✅ Query tests passed")
        return True
        
    except Exception as e:
        logger.error(f"Error in query test: {e}")
        return False

# Run all tests
if __name__ == "__main__":
    logger.info("Starting local database tests...")
    
    if not setup_db():
        logger.error("Failed to set up test database")
        sys.exit(1)
    
    if not create_test_data():
        logger.error("Failed to create test data")
        sys.exit(1)
    
    # Run CRUD tests
    maintenance_test_result = test_maintenance_record_crud()
    audit_test_result = test_audit_task_completion_crud()
    query_test_result = test_queries()
    
    # Report results
    logger.info("==== TEST RESULTS ====")
    logger.info(f"Maintenance Record CRUD tests: {'PASSED' if maintenance_test_result else 'FAILED'}")
    logger.info(f"Audit Task Completion CRUD tests: {'PASSED' if audit_test_result else 'FAILED'}")
    logger.info(f"Query tests: {'PASSED' if query_test_result else 'FAILED'}")
    
    if maintenance_test_result and audit_test_result and query_test_result:
        logger.info("🎉 All tests passed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Some tests failed")
        sys.exit(1)
