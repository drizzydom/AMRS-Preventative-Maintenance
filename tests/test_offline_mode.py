import os
import sys
import unittest
import shutil
import tempfile
from pathlib import Path
import uuid
from datetime import datetime, timedelta, timezone

# Add the parent directory to the Python path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from local_database import (
    get_db_connection, close_db_connection, create_tables,
    create_local_maintenance_record, update_local_maintenance_record,
    create_local_audit_task_completion, update_local_audit_task_completion,
    soft_delete_local_maintenance_record, hard_delete_local_maintenance_record,
    soft_delete_local_audit_task_completion, hard_delete_local_audit_task_completion,
    get_deleted_maintenance_records, get_deleted_audit_task_completions,
    clean_up_synced_deletions, get_unsynced_maintenance_records, get_unsynced_audit_task_completions,
    get_all_local_records, get_local_records_by_fk, _generate_client_id
)

class TestOfflineMode(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for our test database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / 'test_local.db'
        self.encryption_key = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"  # 64-char test key
        
        # Initialize the database
        create_tables(self.db_path, self.encryption_key)
        
        # Insert test data for foreign key references
        self._create_test_data()
    
    def tearDown(self):
        # Close connection and remove temporary directory
        close_db_connection()
        shutil.rmtree(self.temp_dir)
    
    def _create_test_data(self):
        """Create test data for roles, users, sites, machines, parts, and audit tasks"""
        conn = get_db_connection(self.db_path, self.encryption_key)
        cursor = conn.cursor()
        
        # Insert test role
        cursor.execute("""
        INSERT INTO roles (server_id, name, description, permissions)
        VALUES (1, 'Tester', 'Test Role', 'test.permission')
        """)
        
        # Insert test user 
        cursor.execute("""
        INSERT INTO users (client_id, server_id, username, email, full_name, role_id)
        VALUES (?, 1, 'testuser', 'test@example.com', 'Test User', 1)
        """, (_generate_client_id(),))
        
        # Insert test site
        cursor.execute("""
        INSERT INTO sites (client_id, server_id, name, location)
        VALUES (?, 1, 'Test Site', 'Test Location')
        """, (_generate_client_id(),))
        
        # Insert test machine
        cursor.execute("""
        INSERT INTO machines (client_id, server_id, name, model, site_id)
        VALUES (?, 1, 'Test Machine', 'Test Model', 1)
        """, (_generate_client_id(),))
        
        # Insert test part
        cursor.execute("""
        INSERT INTO parts (client_id, server_id, name, description, machine_id)
        VALUES (?, 1, 'Test Part', 'Test Part Description', 1)
        """, (_generate_client_id(),))
        
        # Insert test audit task
        cursor.execute("""
        INSERT INTO audit_tasks (client_id, server_id, name, description, site_id)
        VALUES (?, 1, 'Test Audit Task', 'Test Audit Task Description', 1)
        """, (_generate_client_id(),))
        
        conn.commit()
        self.user_id = 1
        self.site_id = 1
        self.machine_id = 1
        self.part_id = 1
        self.audit_task_id = 1
    
    def test_create_maintenance_record(self):
        """Test creating a maintenance record"""
        data = {
            'part_id': self.part_id,
            'user_id': self.user_id,
            'machine_id': self.machine_id,
            'date': datetime.now().isoformat(),
            'comments': 'Test comments',
            'maintenance_type': 'preventative',
            'description': 'Test maintenance',
            'performed_by': 'Test User',
            'status': 'completed',
            'notes': 'Test notes'
        }
        
        client_id = create_local_maintenance_record(self.db_path, self.encryption_key, data)
        self.assertIsNotNone(client_id)
        
        # Verify the record was created
        conn = get_db_connection(self.db_path, self.encryption_key)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM maintenance_records WHERE client_id = ?", (client_id,))
        record = cursor.fetchone()
        
        self.assertIsNotNone(record)
        self.assertEqual(record['part_id'], self.part_id)
        self.assertEqual(record['is_synced'], 0)  # Should not be synced yet
    
    def test_update_maintenance_record(self):
        """Test updating a maintenance record"""
        # First create a record
        data = {
            'part_id': self.part_id,
            'user_id': self.user_id,
            'machine_id': self.machine_id,
            'date': datetime.now().isoformat(),
            'comments': 'Original comments',
            'maintenance_type': 'preventative',
            'description': 'Original maintenance',
            'performed_by': 'Test User',
            'status': 'completed',
            'notes': 'Original notes'
        }
        
        client_id = create_local_maintenance_record(self.db_path, self.encryption_key, data)
        
        # Now update it
        update_data = {
            'comments': 'Updated comments',
            'description': 'Updated maintenance',
            'notes': 'Updated notes'
        }
        
        success = update_local_maintenance_record(self.db_path, self.encryption_key, client_id, update_data)
        self.assertTrue(success)
        
        # Verify the record was updated
        conn = get_db_connection(self.db_path, self.encryption_key)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM maintenance_records WHERE client_id = ?", (client_id,))
        record = cursor.fetchone()
        
        self.assertEqual(record['comments'], 'Updated comments')
        self.assertEqual(record['description'], 'Updated maintenance')
        self.assertEqual(record['notes'], 'Updated notes')
        self.assertEqual(record['is_synced'], 0)  # Should still not be synced
    
    def test_soft_delete_maintenance_record(self):
        """Test soft-deleting a maintenance record"""
        # First create a record
        data = {
            'part_id': self.part_id,
            'user_id': self.user_id,
            'machine_id': self.machine_id,
            'date': datetime.now().isoformat(),
            'description': 'Test maintenance to delete',
            'maintenance_type': 'preventative',
        }
        
        client_id = create_local_maintenance_record(self.db_path, self.encryption_key, data)
        
        # Soft delete the record
        success = soft_delete_local_maintenance_record(self.db_path, self.encryption_key, client_id)
        self.assertTrue(success)
        
        # Verify the record was marked for deletion
        conn = get_db_connection(self.db_path, self.encryption_key)
        cursor = conn.cursor()
        cursor.execute("SELECT deleted, is_synced FROM maintenance_records WHERE client_id = ?", (client_id,))
        record = cursor.fetchone()
        
        self.assertEqual(record['deleted'], 1)
        self.assertEqual(record['is_synced'], 0)  # Should not be synced
        
        # Verify it appears in the deleted records list
        deleted_records = get_deleted_maintenance_records(self.db_path, self.encryption_key)
        self.assertEqual(len(deleted_records), 0)  # No server_id so not in sync list yet
        
        # Add a server_id and test again
        cursor.execute("UPDATE maintenance_records SET server_id = 1001 WHERE client_id = ?", (client_id,))
        conn.commit()
        
        deleted_records = get_deleted_maintenance_records(self.db_path, self.encryption_key)
        self.assertEqual(len(deleted_records), 1)
        self.assertEqual(deleted_records[0]['client_id'], client_id)
    
    def test_hard_delete_maintenance_record(self):
        """Test hard-deleting a maintenance record"""
        # First create a record
        data = {
            'part_id': self.part_id,
            'user_id': self.user_id,
            'machine_id': self.machine_id,
            'date': datetime.now().isoformat(),
            'description': 'Test maintenance to hard delete',
            'maintenance_type': 'preventative',
        }
        
        client_id = create_local_maintenance_record(self.db_path, self.encryption_key, data)
        
        # Hard delete the record
        success = hard_delete_local_maintenance_record(self.db_path, self.encryption_key, client_id)
        self.assertTrue(success)
        
        # Verify the record is gone
        conn = get_db_connection(self.db_path, self.encryption_key)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM maintenance_records WHERE client_id = ?", (client_id,))
        count = cursor.fetchone()[0]
        
        self.assertEqual(count, 0)
    
    def test_clean_up_synced_deletions(self):
        """Test cleaning up synced deletions"""
        # Create multiple records
        client_ids = []
        for i in range(3):
            data = {
                'part_id': self.part_id,
                'user_id': self.user_id,
                'machine_id': self.machine_id,
                'date': datetime.now().isoformat(),
                'description': f'Test maintenance {i}',
                'maintenance_type': 'preventative',
            }
            
            client_id = create_local_maintenance_record(self.db_path, self.encryption_key, data)
            client_ids.append(client_id)
        
        # Mark all as deleted and add server_ids
        conn = get_db_connection(self.db_path, self.encryption_key)
        cursor = conn.cursor()
        
        for i, client_id in enumerate(client_ids):
            # Soft delete and add server_id
            soft_delete_local_maintenance_record(self.db_path, self.encryption_key, client_id)
            cursor.execute("UPDATE maintenance_records SET server_id = ? WHERE client_id = ?", (2000 + i, client_id))
        
        conn.commit()
        
        # Clean up the first two records
        deleted_count = clean_up_synced_deletions(self.db_path, self.encryption_key, 'maintenance_records', client_ids[:2])
        self.assertEqual(deleted_count, 2)
        
        # Verify only the third record remains
        cursor.execute("SELECT COUNT(*) FROM maintenance_records")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)
        
        cursor.execute("SELECT client_id FROM maintenance_records")
        remaining_client_id = cursor.fetchone()[0]
        self.assertEqual(remaining_client_id, client_ids[2])
    
    def test_audit_task_completion_operations(self):
        """Test CRUD operations for audit task completions"""
        # Create
        data = {
            'audit_task_id': self.audit_task_id,
            'machine_id': self.machine_id,
            'date': datetime.now().isoformat(),
            'completed': 1,
            'completed_by': self.user_id,
            'completed_at': datetime.now().isoformat()
        }
        
        client_id = create_local_audit_task_completion(self.db_path, self.encryption_key, data)
        self.assertIsNotNone(client_id)
        
        # Update
        update_data = {
            'completed': 0,
            'completed_at': (datetime.now() + timedelta(minutes=30)).isoformat()
        }
        
        success = update_local_audit_task_completion(self.db_path, self.encryption_key, client_id, update_data)
        self.assertTrue(success)
        
        # Verify update
        conn = get_db_connection(self.db_path, self.encryption_key)
        cursor = conn.cursor()
        cursor.execute("SELECT completed FROM audit_task_completions WHERE client_id = ?", (client_id,))
        record = cursor.fetchone()
        self.assertEqual(record['completed'], 0)
        
        # Soft delete
        success = soft_delete_local_audit_task_completion(self.db_path, self.encryption_key, client_id)
        self.assertTrue(success)
        
        # Add server_id for deletion sync
        cursor.execute("UPDATE audit_task_completions SET server_id = 1001 WHERE client_id = ?", (client_id,))
        conn.commit()
        
        # Verify it appears in deleted list
        deleted_records = get_deleted_audit_task_completions(self.db_path, self.encryption_key)
        self.assertEqual(len(deleted_records), 1)
        
        # Hard delete
        success = hard_delete_local_audit_task_completion(self.db_path, self.encryption_key, client_id)
        self.assertTrue(success)
        
        # Verify it's gone
        cursor.execute("SELECT COUNT(*) FROM audit_task_completions WHERE client_id = ?", (client_id,))
        count = cursor.fetchone()[0]
        self.assertEqual(count, 0)
    
    def test_get_unsynced_records(self):
        """Test getting unsynced records for sync operations"""
        # Create a few maintenance records
        for i in range(3):
            data = {
                'part_id': self.part_id,
                'user_id': self.user_id,
                'machine_id': self.machine_id,
                'date': datetime.now().isoformat(),
                'description': f'Test maintenance {i}',
                'maintenance_type': 'preventative',
            }
            create_local_maintenance_record(self.db_path, self.encryption_key, data)
        
        # Create a couple audit task completions
        for i in range(2):
            data = {
                'audit_task_id': self.audit_task_id,
                'machine_id': self.machine_id,
                'date': datetime.now().isoformat(),
                'completed': 1,
                'completed_by': self.user_id,
                'completed_at': datetime.now().isoformat()
            }
            create_local_audit_task_completion(self.db_path, self.encryption_key, data)
        
        # Get unsynced records
        unsynced_mrs = get_unsynced_maintenance_records(self.db_path, self.encryption_key)
        unsynced_atcs = get_unsynced_audit_task_completions(self.db_path, self.encryption_key)
        
        self.assertEqual(len(unsynced_mrs), 3)
        self.assertEqual(len(unsynced_atcs), 2)
        
        # Verify the format of unsynced records (server_ids should be replaced)
        for record in unsynced_mrs:
            self.assertEqual(record['part_id'], 1)  # Should be server_id of part
            self.assertEqual(record['user_id'], 1)  # Should be server_id of user
            self.assertEqual(record['machine_id'], 1)  # Should be server_id of machine
            self.assertNotIn('id', record)  # Local id should be removed
            self.assertNotIn('server_id', record)  # server_id should be removed for new records
            self.assertIn('client_id', record)  # client_id should be present


if __name__ == '__main__':
    unittest.main()
