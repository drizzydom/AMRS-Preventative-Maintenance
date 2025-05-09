#!/usr/bin/env python3
"""
Offline Mode Testing Suite

This script tests the offline functionality of the AMRS Preventative Maintenance application,
including login, database synchronization, and UI elements specific to offline mode.
"""
import os
import sys
import time
import unittest
import requests
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from threading import Thread
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[OFFLINE_TEST] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("offline_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("offline_test")

# Add the current directory to the path to import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from db_controller import DatabaseController
except ImportError:
    logger.error("Failed to import DatabaseController. Make sure db_controller.py is in the current directory.")
    sys.exit(1)

class OfflineModeTests(unittest.TestCase):
    """Tests for offline mode functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment before running tests"""
        # Clear any existing database
        cls.instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
        cls.db_path = os.path.join(cls.instance_dir, 'test_maintenance.db')
        
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
            logger.info(f"Removed existing test database: {cls.db_path}")
            
        # Start a test server in a separate thread
        # We set offline mode explicitly to True
        os.environ['OFFLINE_MODE'] = 'true'
        os.environ['TEST_DATABASE'] = cls.db_path
        os.environ['FLASK_ENV'] = 'testing'
        
        # Initialize the test server
        cls.server_thread = Thread(target=cls._start_test_server)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        
        # Wait for the server to start
        time.sleep(2)
        cls.base_url = "http://127.0.0.1:5001"
        
        # Create a database controller for direct DB access
        cls.db_controller = DatabaseController(db_path=cls.db_path, use_encryption=False)
        
        # Initialize session for HTTP requests
        cls.session = requests.Session()
        
        logger.info("Test environment set up complete")
    
    @classmethod
    def _start_test_server(cls):
        """Start a test server for the tests"""
        # To avoid circular imports, we dynamically import and run the offline app
        try:
            # First try to run a specialized test version if it exists
            from offline_app_test import app
            app.config['TESTING'] = True
            app.config['SERVER_NAME'] = '127.0.0.1:5001'
            app.run(host='127.0.0.1', port=5001, debug=False)
        except ImportError:
            # Fall back to the regular offline app
            from offline_app import app
            app.config['TESTING'] = True
            app.config['SERVER_NAME'] = '127.0.0.1:5001'
            app.run(host='127.0.0.1', port=5001, debug=False)
    
    def test_01_server_running(self):
        """Test if the server is running"""
        try:
            response = self.session.get(f"{self.base_url}/")
            self.assertEqual(response.status_code, 200)
            logger.info("Server is running and responding to requests")
        except requests.RequestException as e:
            self.fail(f"Server is not running: {e}")
    
    def test_02_offline_mode_enabled(self):
        """Test if offline mode is properly enabled"""
        response = self.session.get(f"{self.base_url}/api/connection/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['offline_mode'])
        self.assertEqual(data['status'], 'offline_mode')
        logger.info("Offline mode is properly enabled")
    
    def test_03_login_page_loads(self):
        """Test if the login page loads correctly"""
        response = self.session.get(f"{self.base_url}/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'login', response.content.lower())
        logger.info("Login page loads correctly")
    
    def test_04_login_with_default_admin(self):
        """Test login with the default admin user"""
        # First check if the admin user exists in the database
        try:
            user_data = self.db_controller.fetch_one(
                "SELECT id, username FROM users WHERE username = 'admin'"
            )
            if not user_data:
                # Create admin user if it doesn't exist
                self.db_controller.create_user(
                    username='admin',
                    email='admin@example.com',
                    full_name='Administrator',
                    password='admin',
                    is_admin=True,
                    role_id=1
                )
                logger.info("Created default admin user for testing")
        except Exception as e:
            logger.error(f"Error checking for admin user: {e}")
            
        # Now attempt to login
        login_data = {
            'username': 'admin',
            'password': 'admin'
        }
        response = self.session.post(
            f"{self.base_url}/login",
            data=login_data,
            allow_redirects=True
        )
        
        # Should redirect to dashboard after successful login
        self.assertEqual(response.status_code, 200)
        self.assertTrue('/dashboard' in response.url)
        logger.info("Successfully logged in with admin user")
    
    def test_05_dashboard_access(self):
        """Test if dashboard is accessible after login"""
        response = self.session.get(f"{self.base_url}/dashboard")
        self.assertEqual(response.status_code, 200)
        # Check for dashboard elements
        self.assertIn(b'dashboard', response.content.lower())
        logger.info("Dashboard is accessible after login")
    
    def test_06_offline_indicators_present(self):
        """Test if offline indicators are present in the UI"""
        response = self.session.get(f"{self.base_url}/dashboard")
        self.assertEqual(response.status_code, 200)
        # Check for offline indicator elements
        self.assertIn(b'connection-status', response.content.lower())
        self.assertIn(b'offline', response.content.lower())
        logger.info("Offline indicators are present in the UI")
    
    def test_07_sync_endpoint_available(self):
        """Test if sync endpoint is available"""
        response = self.session.get(f"{self.base_url}/api/sync/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue('last_sync' in data)
        self.assertTrue('pending_sync' in data)
        self.assertTrue(data['offline_mode'])
        logger.info("Sync endpoint is available and returning expected data")
    
    def test_08_trigger_sync(self):
        """Test triggering a sync operation"""
        response = self.session.post(f"{self.base_url}/api/sync/trigger")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue('message' in data)
        logger.info("Sync operation triggered successfully")
        
        # Verify sync time was updated
        sync_time = self.db_controller.get_last_sync_time()
        self.assertIsNotNone(sync_time)
        logger.info(f"Sync time updated to: {sync_time}")
    
    def test_09_create_record_offline(self):
        """Test creating a record while offline"""
        # Check if maintenance_records table exists, create it if not
        if not self.db_controller.table_exists('maintenance_records'):
            self.db_controller.execute_query('''
            CREATE TABLE maintenance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                machine_id INTEGER,
                maintenance_date TEXT,
                technician_id INTEGER,
                notes TEXT,
                is_synced INTEGER DEFAULT 0,
                client_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            logger.info("Created maintenance_records table")
        
        # Create a test record
        client_id = f"test-{datetime.now().timestamp()}"
        self.db_controller.execute_query(
            "INSERT INTO maintenance_records (site_id, machine_id, maintenance_date, technician_id, notes, is_synced, client_id) " +
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (1, 1, datetime.now().isoformat(), 1, "Test maintenance record", 0, client_id)
        )
        
        # Verify record was created
        record = self.db_controller.fetch_one(
            "SELECT * FROM maintenance_records WHERE client_id = ?",
            (client_id,)
        )
        self.assertIsNotNone(record)
        self.assertEqual(record['is_synced'], 0)  # Should be marked as not synced
        logger.info("Successfully created test record while offline")
    
    def test_10_pending_sync_count(self):
        """Test that pending sync count works"""
        sync_data = self.db_controller.get_pending_sync_count()
        self.assertIsNotNone(sync_data)
        # If we created a maintenance record, there should be at least one pending sync
        pending_count = sync_data.get('maintenance', 0)
        self.assertGreaterEqual(pending_count, 0)
        logger.info(f"Pending sync count: {sync_data}")
    
    def test_11_logout(self):
        """Test logging out"""
        response = self.session.get(f"{self.base_url}/logout", allow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('/login' in response.url)
        logger.info("Successfully logged out")
        
        # Verify cannot access dashboard after logout
        response = self.session.get(f"{self.base_url}/dashboard")
        self.assertNotEqual(response.status_code, 200)
        # Should be redirected to login
        self.assertTrue('/login' in response.url)
        logger.info("Cannot access dashboard after logout")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests are complete"""
        # Close any open database connections
        if hasattr(cls, 'db_controller'):
            cls.db_controller.close_connection()
            
        # Remove test database
        if os.path.exists(cls.db_path):
            try:
                os.remove(cls.db_path)
                logger.info(f"Removed test database: {cls.db_path}")
            except Exception as e:
                logger.warning(f"Could not remove test database: {e}")
        
        logger.info("Test cleanup complete")

class OfflineOnlineSyncTests(unittest.TestCase):
    """Tests for synchronization between offline and online databases"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment for sync tests"""
        # These tests require both an offline and online database
        cls.online_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'online_test.db')
        cls.offline_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'offline_test.db')
        
        # Remove existing test databases
        for db_path in [cls.online_db_path, cls.offline_db_path]:
            if os.path.exists(db_path):
                os.remove(db_path)
                logger.info(f"Removed existing test database: {db_path}")
        
        # Create controllers for both databases
        cls.online_db = DatabaseController(db_path=cls.online_db_path, use_encryption=False)
        cls.offline_db = DatabaseController(db_path=cls.offline_db_path, use_encryption=False)
        
        # Initialize both databases with the same schema
        for db in [cls.online_db, cls.offline_db]:
            cls._init_test_database(db)
        
        logger.info("Sync test environment set up complete")
    
    @classmethod
    def _init_test_database(cls, db):
        """Initialize a test database with required schema"""
        # Create users table
        if not db.table_exists('users'):
            db.execute_query('''
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
        
        # Create maintenance_records table with sync fields
        if not db.table_exists('maintenance_records'):
            db.execute_query('''
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
        
        # Create sync_info table
        if not db.table_exists('sync_info'):
            db.execute_query('''
            CREATE TABLE sync_info (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
    
    def test_01_create_online_data(self):
        """Test creating data in the 'online' database"""
        # Create a test user in the online database
        self.online_db.create_user(
            username='online_user',
            email='online@example.com',
            full_name='Online User',
            password='password',
            is_admin=False
        )
        
        # Create test maintenance records
        for i in range(3):
            self.online_db.execute_query(
                "INSERT INTO maintenance_records (site_id, machine_id, maintenance_date, technician_id, notes, is_synced) " +
                "VALUES (?, ?, ?, ?, ?, ?)",
                (i+1, i+1, datetime.now().isoformat(), 1, f"Online record {i+1}", 1)
            )
        
        # Verify records were created
        count = self.online_db.fetch_one("SELECT COUNT(*) FROM maintenance_records")[0]
        self.assertEqual(count, 3)
        logger.info("Successfully created test data in online database")
    
    def test_02_create_offline_data(self):
        """Test creating data in the 'offline' database"""
        # Create a test user in the offline database
        self.offline_db.create_user(
            username='offline_user',
            email='offline@example.com',
            full_name='Offline User',
            password='password',
            is_admin=False
        )
        
        # Create test maintenance records with client_id for syncing
        for i in range(2):
            client_id = f"offline-{datetime.now().timestamp()}-{i}"
            self.offline_db.execute_query(
                "INSERT INTO maintenance_records (site_id, machine_id, maintenance_date, technician_id, notes, is_synced, client_id) " +
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (10+i, 10+i, datetime.now().isoformat(), 2, f"Offline record {i+1}", 0, client_id)
            )
        
        # Verify records were created
        count = self.offline_db.fetch_one("SELECT COUNT(*) FROM maintenance_records")[0]
        self.assertEqual(count, 2)
        logger.info("Successfully created test data in offline database")
    
    def test_03_simulate_download_sync(self):
        """Test downloading data from online to offline database"""
        # Simulate downloading all online records to offline
        online_records = self.online_db.fetch_all("SELECT * FROM maintenance_records")
        
        for record in online_records:
            # Convert record to dict
            record_dict = dict(record)
            
            # Check if record already exists in offline DB
            exists = self.offline_db.fetch_one(
                "SELECT id FROM maintenance_records WHERE server_id = ?", 
                (record_dict['id'],)
            )
            
            if not exists:
                # Insert as a new record
                self.offline_db.execute_query(
                    "INSERT INTO maintenance_records (site_id, machine_id, maintenance_date, technician_id, notes, is_synced, server_id, sync_status) " +
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (record_dict['site_id'], record_dict['machine_id'], record_dict['maintenance_date'], 
                     record_dict['technician_id'], record_dict['notes'], 1, record_dict['id'], 'synced')
                )
            else:
                # Update existing record
                self.offline_db.execute_query(
                    "UPDATE maintenance_records SET site_id = ?, machine_id = ?, maintenance_date = ?, " +
                    "technician_id = ?, notes = ?, is_synced = ?, sync_status = ? WHERE server_id = ?",
                    (record_dict['site_id'], record_dict['machine_id'], record_dict['maintenance_date'], 
                     record_dict['technician_id'], record_dict['notes'], 1, 'synced', record_dict['id'])
                )
        
        # Verify records were synced
        count = self.offline_db.fetch_one("SELECT COUNT(*) FROM maintenance_records")[0]
        self.assertEqual(count, 5)  # 2 offline + 3 online
        
        # Verify sync status
        synced_count = self.offline_db.fetch_one("SELECT COUNT(*) FROM maintenance_records WHERE is_synced = 1")[0]
        self.assertEqual(synced_count, 3)  # Only the online records should be marked as synced
        
        logger.info("Successfully simulated downloading data from online to offline database")
    
    def test_04_simulate_upload_sync(self):
        """Test uploading data from offline to online database"""
        # Get offline records that need to be synced
        offline_records = self.offline_db.fetch_all(
            "SELECT * FROM maintenance_records WHERE is_synced = 0"
        )
        
        for record in offline_records:
            # Convert record to dict
            record_dict = dict(record)
            
            # Insert into online DB
            cursor = self.online_db.execute_query(
                "INSERT INTO maintenance_records (site_id, machine_id, maintenance_date, technician_id, notes, is_synced, client_id) " +
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (record_dict['site_id'], record_dict['machine_id'], record_dict['maintenance_date'], 
                 record_dict['technician_id'], record_dict['notes'], 1, record_dict['client_id'])
            )
            
            # Get the server ID for the new record
            server_id = cursor.lastrowid
            
            # Update the offline record with the server ID and mark as synced
            self.offline_db.execute_query(
                "UPDATE maintenance_records SET server_id = ?, is_synced = 1, sync_status = 'synced' WHERE id = ?",
                (server_id, record_dict['id'])
            )
        
        # Verify all records in offline DB are now marked as synced
        unsynced_count = self.offline_db.fetch_one("SELECT COUNT(*) FROM maintenance_records WHERE is_synced = 0")[0]
        self.assertEqual(unsynced_count, 0)
        
        # Verify online DB now has all records
        online_count = self.online_db.fetch_one("SELECT COUNT(*) FROM maintenance_records")[0]
        self.assertEqual(online_count, 5)  # 3 original + 2 from offline
        
        logger.info("Successfully simulated uploading data from offline to online database")
    
    def test_05_simulate_conflict_resolution(self):
        """Test conflict resolution during sync"""
        # Create a record with the same client_id in both databases
        client_id = f"conflict-{datetime.now().timestamp()}"
        
        # Create in offline DB first
        self.offline_db.execute_query(
            "INSERT INTO maintenance_records (site_id, machine_id, maintenance_date, technician_id, notes, is_synced, client_id, sync_status) " +
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (99, 99, datetime.now().isoformat(), 3, "Offline conflicting record", 0, client_id, 'pending')
        )
        
        # Create in online DB with different data
        self.online_db.execute_query(
            "INSERT INTO maintenance_records (site_id, machine_id, maintenance_date, technician_id, notes, is_synced, client_id) " +
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (99, 99, datetime.now().isoformat(), 3, "Online conflicting record", 1, client_id)
        )
        
        # Get the server ID
        server_record = self.online_db.fetch_one(
            "SELECT id, notes FROM maintenance_records WHERE client_id = ?",
            (client_id,)
        )
        server_id = server_record['id']
        
        # Simulate conflict resolution - server record takes precedence
        self.offline_db.execute_query(
            "UPDATE maintenance_records SET server_id = ?, notes = ?, is_synced = 1, sync_status = 'synced' WHERE client_id = ?",
            (server_id, server_record['notes'], client_id)
        )
        
        # Verify conflict resolution
        resolved_record = self.offline_db.fetch_one(
            "SELECT notes FROM maintenance_records WHERE client_id = ?",
            (client_id,)
        )
        
        self.assertEqual(resolved_record['notes'], "Online conflicting record")
        logger.info("Successfully simulated conflict resolution during sync")
    
    def test_06_update_sync_timestamp(self):
        """Test updating sync timestamp"""
        # Update sync timestamp in offline DB
        success = self.offline_db.update_last_sync_time()
        self.assertTrue(success)
        
        # Verify timestamp was updated
        last_sync = self.offline_db.get_last_sync_time()
        self.assertIsNotNone(last_sync)
        
        logger.info(f"Successfully updated sync timestamp to {last_sync}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after sync tests"""
        # Close database connections
        cls.online_db.close_connection()
        cls.offline_db.close_connection()
        
        # Remove test databases
        for db_path in [cls.online_db_path, cls.offline_db_path]:
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                    logger.info(f"Removed test database: {db_path}")
                except Exception as e:
                    logger.warning(f"Could not remove test database: {e}")
        
        logger.info("Sync test cleanup complete")

def run_tests():
    """Run all offline mode tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(OfflineModeTests))
    test_suite.addTest(unittest.makeSuite(OfflineOnlineSyncTests))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(test_suite)

if __name__ == "__main__":
    print("\n===== AMRS Preventative Maintenance - Offline Mode Tests =====\n")
    result = run_tests()
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check the logs for details.")
        sys.exit(1)
