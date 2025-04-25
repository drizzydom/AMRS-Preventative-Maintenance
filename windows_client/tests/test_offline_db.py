import os
import sys
import unittest
import tempfile
import shutil
import json
from datetime import datetime, timedelta

# Add parent directory to path to import application modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from offline_db import OfflineDatabase
from security_utils import SecurityUtils

class TestOfflineDatabase(unittest.TestCase):
    """Test cases for the OfflineDatabase class"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Create a temporary directory for test database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_db.sqlite')
        
        # Initialize database with encryption disabled for easier testing
        self.db = OfflineDatabase(self.db_path, encrypt=False)
    
    def tearDown(self):
        """Clean up after each test"""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.temp_dir)
    
    def test_initialize_db(self):
        """Test database initialization"""
        # Check if database file was created
        self.assertTrue(os.path.exists(self.db_path))
        
        # Check if tables were created
        tables = self.db._execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [row[0] for row in tables]
        
        expected_tables = ['pending_operations', 'cached_data', 'machines', 'maintenance_history', 'auth_tokens', 'user_access']
        for table in expected_tables:
            self.assertIn(table, table_names)
    
    def test_store_operation(self):
        """Test storing an operation"""
        method = 'POST'
        endpoint = '/api/test'
        data = {'name': 'test', 'value': 123}
        
        # Store an operation
        op_id = self.db.store_operation(method, endpoint, data)
        
        # Verify it was stored
        self.assertIsNotNone(op_id)
        
        # Check if the operation exists in the database
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT method, endpoint FROM pending_operations WHERE id = ?", (op_id,))
        result = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], method)
        self.assertEqual(result[1], endpoint)
    
    def test_get_pending_operations(self):
        """Test retrieving pending operations"""
        # Store some operations
        op1 = self.db.store_operation('POST', '/api/test1', {'name': 'test1'})
        op2 = self.db.store_operation('PUT', '/api/test2', {'name': 'test2'})
        
        # Get pending operations
        operations = self.db.get_pending_operations()
        
        # Check if we got the expected operations
        self.assertEqual(len(operations), 2)
        self.assertEqual(operations[0]['endpoint'], '/api/test1')
        self.assertEqual(operations[1]['endpoint'], '/api/test2')
    
    def test_mark_operation_synced(self):
        """Test marking an operation as synced"""
        # Store an operation
        op_id = self.db.store_operation('POST', '/api/test', {'name': 'test'})
        
        # Mark it as synced
        self.db.mark_operation_synced(op_id)
        
        # Check that it's no longer in pending operations
        operations = self.db.get_pending_operations()
        op_ids = [op['id'] for op in operations]
        self.assertNotIn(op_id, op_ids)
        
        # Check that it's marked as synced in the database
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT synced FROM pending_operations WHERE id = ?", (op_id,))
        result = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 1)
    
    def test_cache_response(self):
        """Test caching a response"""
        endpoint = '/api/test'
        data = {'result': 'success', 'items': [1, 2, 3]}
        
        # Cache a response
        self.db.cache_response(endpoint, data)
        
        # Get the cached response
        cached_data, timestamp = self.db.get_cached_response(endpoint)
        
        # Check if the data matches
        self.assertEqual(cached_data, data)
        self.assertIsNotNone(timestamp)
    
    def test_get_failed_operations_count(self):
        """Test getting count of failed operations"""
        # Store some operations
        op1 = self.db.store_operation('POST', '/api/test1', {'name': 'test1'})
        op2 = self.db.store_operation('PUT', '/api/test2', {'name': 'test2'})
        
        # Mark one as failed
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE pending_operations SET synced = -1 WHERE id = ?", (op1,))
        conn.commit()
        conn.close()
        
        # Get failed operations count
        count = self.db.get_failed_operations_count()
        self.assertEqual(count, 1)
    
    def test_retry_failed_operation(self):
        """Test retrying a failed operation"""
        # Store an operation
        op_id = self.db.store_operation('POST', '/api/test', {'name': 'test'})
        
        # Mark it as failed
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE pending_operations SET synced = -1 WHERE id = ?", (op_id,))
        conn.commit()
        conn.close()
        
        # Retry the operation
        result = self.db.retry_failed_operation(op_id)
        
        # Check if retry was successful
        self.assertTrue(result)
        
        # Check if operation is now pending again
        operations = self.db.get_pending_operations()
        op_ids = [op['id'] for op in operations]
        self.assertIn(op_id, op_ids)
    
    def test_encrypted_database(self):
        """Test database with encryption enabled"""
        # Create a new encrypted database
        encrypted_db_path = os.path.join(self.temp_dir, 'encrypted_db.sqlite')
        encrypted_db = OfflineDatabase(encrypted_db_path, encrypt=True)
        
        # Store an operation
        test_data = {'name': 'test', 'value': 'sensitive data'}
        op_id = encrypted_db.store_operation('POST', '/api/test', test_data)
        
        # Check that the operation was stored
        operations = encrypted_db.get_pending_operations()
        self.assertEqual(len(operations), 1)
        self.assertEqual(operations[0]['data']['name'], 'test')
        
        # Now access the database file directly to verify data is encrypted
        import sqlite3
        direct_conn = sqlite3.connect(encrypted_db_path)
        cursor = direct_conn.cursor()
        cursor.execute("SELECT data FROM pending_operations WHERE id = ?", (op_id,))
        raw_data = cursor.fetchone()[0]
        direct_conn.close()
        
        # Encrypted data shouldn't contain our plain text value
        self.assertNotIn(b'sensitive data', raw_data)
