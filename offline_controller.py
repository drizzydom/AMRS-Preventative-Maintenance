"""
Offline Database Controller

This module provides a high-level interface for managing offline mode database operations,
including synchronization between local SQLite database and server.
"""

import os
import sys
import logging
import json
import sqlite3
import requests
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='[OFFLINE_CONTROLLER] %(levelname)s - %(message)s')
logger = logging.getLogger("offline_controller")

# Import local modules
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

class OfflineController:
    """Controls offline database operations and synchronization"""
    
    def __init__(self, db_path=None, server_url=None):
        """
        Initialize the controller
        
        Args:
            db_path (str): Path to the SQLite database file
            server_url (str): URL of the server API
        """
        self.db_path = db_path or os.path.join(current_dir, 'instance', 'maintenance.db')
        self.server_url = server_url or os.environ.get('SERVER_URL', 'https://amrs-maintenance.example.com/api')
        self.server_available = False
        self.last_sync = None
        
        # Create directory for database if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
    def get_connection(self):
        """Get a connection to the SQLite database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        return conn
        
    def check_server_connection(self):
        """Check if the server is reachable"""
        try:
            response = requests.get(f"{self.server_url}/healthcheck", timeout=5)
            self.server_available = response.status_code == 200
            return self.server_available
        except Exception as e:
            logger.warning(f"Server connection check failed: {e}")
            self.server_available = False
            return False
            
    def get_last_sync_time(self):
        """Get the timestamp of the last successful sync"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if the sync_info table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sync_info'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create the table if it doesn't exist
                cursor.execute("""
                CREATE TABLE sync_info (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                conn.commit()
                return None
                
            # Get the last sync time
            cursor.execute("SELECT value FROM sync_info WHERE key = 'last_sync'")
            result = cursor.fetchone()
            
            if result:
                return result[0]
            return None
        except Exception as e:
            logger.error(f"Error getting last sync time: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
                
    def update_last_sync_time(self):
        """Update the last sync timestamp"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            now = datetime.utcnow().isoformat()
            
            # Check if the sync_info table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sync_info'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create the table if it doesn't exist
                cursor.execute("""
                CREATE TABLE sync_info (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
            # Update the last sync time
            cursor.execute("""
            INSERT INTO sync_info (key, value, updated_at)
            VALUES ('last_sync', ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """, (now,))
            
            conn.commit()
            self.last_sync = now
            return True
        except Exception as e:
            logger.error(f"Error updating last sync time: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
                
    def get_pending_sync_count(self):
        """Get count of records pending synchronization"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            maintenance_count = 0
            audit_count = 0
            
            # Count maintenance records pending sync
            cursor.execute("SELECT COUNT(*) FROM maintenance_records WHERE is_synced = 0")
            result = cursor.fetchone()
            if result:
                maintenance_count = result[0]
                
            # Count audit task completions pending sync
            cursor.execute("SELECT COUNT(*) FROM audit_task_completions WHERE is_synced = 0")
            result = cursor.fetchone()
            if result:
                audit_count = result[0]
                
            return {
                'maintenance': maintenance_count,
                'audit': audit_count,
                'total': maintenance_count + audit_count
            }
        except Exception as e:
            logger.error(f"Error getting pending sync count: {e}")
            return {'maintenance': 0, 'audit': 0, 'total': 0}
        finally:
            if 'conn' in locals():
                conn.close()
                
    def synchronize(self):
        """
        Synchronize local database with server
        
        Returns:
            dict: Result of sync operation
        """
        if not self.check_server_connection():
            logger.warning("Cannot synchronize - server not available")
            return {
                'success': False,
                'message': 'Server not available',
                'synced': {'maintenance': 0, 'audit': 0, 'total': 0}
            }
            
        try:
            # Get records pending sync
            maintenance_records = self.get_unsynced_maintenance_records()
            audit_completions = self.get_unsynced_audit_completions()
            
            # Track sync results
            sync_results = {
                'maintenance': 0,
                'audit': 0,
                'total': 0,
                'failed': 0
            }
            
            # Sync maintenance records
            for record in maintenance_records:
                success = self.sync_maintenance_record(record)
                if success:
                    sync_results['maintenance'] += 1
                    sync_results['total'] += 1
                else:
                    sync_results['failed'] += 1
                    
            # Sync audit completions
            for record in audit_completions:
                success = self.sync_audit_completion(record)
                if success:
                    sync_results['audit'] += 1
                    sync_results['total'] += 1
                else:
                    sync_results['failed'] += 1
                    
            # Update last sync time
            self.update_last_sync_time()
            
            return {
                'success': True,
                'message': 'Synchronization completed',
                'synced': sync_results
            }
        except Exception as e:
            logger.error(f"Error during synchronization: {e}")
            return {
                'success': False,
                'message': f'Error during synchronization: {str(e)}',
                'synced': {'maintenance': 0, 'audit': 0, 'total': 0}
            }
            
    def get_unsynced_maintenance_records(self):
        """Get maintenance records that need to be synced"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT * FROM maintenance_records WHERE is_synced = 0
            """)
            
            records = [dict(row) for row in cursor.fetchall()]
            return records
        except Exception as e:
            logger.error(f"Error getting unsynced maintenance records: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()
                
    def get_unsynced_audit_completions(self):
        """Get audit task completions that need to be synced"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT * FROM audit_task_completions WHERE is_synced = 0
            """)
            
            records = [dict(row) for row in cursor.fetchall()]
            return records
        except Exception as e:
            logger.error(f"Error getting unsynced audit completions: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()
                
    def sync_maintenance_record(self, record):
        """
        Sync a maintenance record with the server
        
        Args:
            record (dict): The maintenance record to sync
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # In a real implementation, this would make an API call to the server
            # For this example, we'll simulate a successful sync
            
            # Prepare the data for the API call
            api_data = {
                'client_id': record['client_id'],
                'part_id': record['part_id'],
                'user_id': record['user_id'],
                'machine_id': record['machine_id'],
                'date': record['date'],
                'comments': record['comments'],
                'maintenance_type': record['maintenance_type'],
                'description': record['description'],
                'performed_by': record['performed_by'],
                'status': record['status'],
                'notes': record['notes']
            }
            
            # Make the API call
            # response = requests.post(f"{self.server_url}/maintenance/sync", json=api_data)
            
            # For this example, simulate a successful response
            # server_id = response.json().get('server_id')
            server_id = 10000 + record['id']  # Simulate a server ID
            
            # Update the local record with the server ID
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
            UPDATE maintenance_records 
            SET server_id = ?, is_synced = 1
            WHERE id = ?
            """, (server_id, record['id']))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"Error syncing maintenance record {record['id']}: {e}")
            return False
            
    def sync_audit_completion(self, record):
        """
        Sync an audit task completion with the server
        
        Args:
            record (dict): The audit completion record to sync
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # In a real implementation, this would make an API call to the server
            # For this example, we'll simulate a successful sync
            
            # Prepare the data for the API call
            api_data = {
                'client_id': record['client_id'],
                'audit_task_id': record['audit_task_id'],
                'machine_id': record['machine_id'],
                'date': record['date'],
                'completed': record['completed'],
                'completed_by': record['completed_by'],
                'completed_at': record['completed_at']
            }
            
            # Make the API call
            # response = requests.post(f"{self.server_url}/audit/completion/sync", json=api_data)
            
            # For this example, simulate a successful response
            # server_id = response.json().get('server_id')
            server_id = 20000 + record['id']  # Simulate a server ID
            
            # Update the local record with the server ID
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
            UPDATE audit_task_completions 
            SET server_id = ?, is_synced = 1
            WHERE id = ?
            """, (server_id, record['id']))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"Error syncing audit completion {record['id']}: {e}")
            return False
            
    def create_maintenance_record(self, record_data):
        """
        Create a new maintenance record in the local database
        
        Args:
            record_data (dict): The maintenance record data
            
        Returns:
            dict: The created record with id and client_id
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Generate a client ID for tracking
            client_id = str(uuid.uuid4())
            
            # Insert the record
            cursor.execute("""
            INSERT INTO maintenance_records (
                client_id,
                part_id,
                user_id,
                machine_id,
                date,
                comments,
                maintenance_type,
                description,
                performed_by,
                status,
                notes,
                is_synced,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                client_id,
                record_data.get('part_id'),
                record_data.get('user_id'),
                record_data.get('machine_id'),
                record_data.get('date'),
                record_data.get('comments'),
                record_data.get('maintenance_type'),
                record_data.get('description'),
                record_data.get('performed_by'),
                record_data.get('status'),
                record_data.get('notes')
            ))
            
            record_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Return the record with ID and client_id
            return {
                'id': record_id,
                'client_id': client_id,
                **record_data
            }
        except Exception as e:
            logger.error(f"Error creating maintenance record: {e}")
            if 'conn' in locals():
                conn.close()
            raise
            
    def create_audit_completion(self, completion_data):
        """
        Create a new audit task completion in the local database
        
        Args:
            completion_data (dict): The audit completion data
            
        Returns:
            dict: The created record with id and client_id
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Generate a client ID for tracking
            client_id = str(uuid.uuid4())
            
            # Insert the record
            cursor.execute("""
            INSERT INTO audit_task_completions (
                client_id,
                audit_task_id,
                machine_id,
                date,
                completed,
                completed_by,
                completed_at,
                is_synced,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                client_id,
                completion_data.get('audit_task_id'),
                completion_data.get('machine_id'),
                completion_data.get('date'),
                completion_data.get('completed', 0),
                completion_data.get('completed_by'),
                completion_data.get('completed_at')
            ))
            
            record_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Return the record with ID and client_id
            return {
                'id': record_id,
                'client_id': client_id,
                **completion_data
            }
        except Exception as e:
            logger.error(f"Error creating audit completion: {e}")
            if 'conn' in locals():
                conn.close()
            raise
