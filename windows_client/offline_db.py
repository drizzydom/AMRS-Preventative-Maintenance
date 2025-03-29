import sqlite3
import os
import json
from datetime import datetime
import uuid

class OfflineDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.initialize_db()
        
    def initialize_db(self):
        """Initialize the database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for storing operations to sync
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_operations (
            id TEXT PRIMARY KEY,
            endpoint TEXT NOT NULL,
            method TEXT NOT NULL,
            data TEXT,
            timestamp TEXT,
            synced INTEGER DEFAULT 0
        )
        ''')
        
        # Table for caching GET responses
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cached_data (
            endpoint TEXT PRIMARY KEY,
            data TEXT,
            timestamp TEXT
        )
        ''')
        
        # Table for maintaining machine state
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS machines (
            id TEXT PRIMARY KEY,
            data TEXT,
            last_updated TEXT
        )
        ''')
        
        # Table for maintenance history
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance_history (
            id TEXT PRIMARY KEY,
            machine_id TEXT,
            part_id TEXT,
            timestamp TEXT,
            data TEXT,
            synced INTEGER DEFAULT 0,
            FOREIGN KEY (machine_id) REFERENCES machines (id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_operation(self, method, endpoint, data):
        """Store an operation to be performed when back online"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        op_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        data_json = json.dumps(data) if data else None
        
        cursor.execute('''
        INSERT INTO pending_operations (id, endpoint, method, data, timestamp, synced)
        VALUES (?, ?, ?, ?, ?, 0)
        ''', (op_id, endpoint, method, data_json, timestamp))
        
        conn.commit()
        conn.close()
        
        return op_id
    
    def cache_response(self, endpoint, data):
        """Cache a response for later offline use"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        data_json = json.dumps(data) if data else None
        
        cursor.execute('''
        INSERT OR REPLACE INTO cached_data (endpoint, data, timestamp)
        VALUES (?, ?, ?)
        ''', (endpoint, data_json, timestamp))
        
        conn.commit()
        conn.close()
    
    def get_cached_response(self, endpoint):
        """Retrieve a cached response"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT data, timestamp FROM cached_data WHERE endpoint = ?', (endpoint,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result and result[0]:
            return json.loads(result[0]), result[1]
        return None, None
    
    def get_pending_operations(self):
        """Get all pending operations that need to be synced"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, endpoint, method, data, timestamp
        FROM pending_operations
        WHERE synced = 0
        ORDER BY timestamp
        ''')
        
        operations = []
        for row in cursor.fetchall():
            op = {
                'id': row[0],
                'endpoint': row[1],
                'method': row[2],
                'data': json.loads(row[3]) if row[3] else None,
                'timestamp': row[4]
            }
            operations.append(op)
        
        conn.close()
        return operations
    
    def mark_operation_synced(self, op_id):
        """Mark an operation as successfully synced"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE pending_operations SET synced = 1 WHERE id = ?', (op_id,))
        
        conn.commit()
        conn.close()
    
    def store_machine_data(self, machine_id, data):
        """Store machine data for offline access"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        data_json = json.dumps(data)
        
        cursor.execute('''
        INSERT OR REPLACE INTO machines (id, data, last_updated)
        VALUES (?, ?, ?)
        ''', (machine_id, data_json, timestamp))
        
        conn.commit()
        conn.close()
    
    def get_machine_data(self, machine_id):
        """Get cached machine data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT data FROM machines WHERE id = ?', (machine_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result and result[0]:
            return json.loads(result[0])
        return None
    
    def record_maintenance(self, machine_id, part_id, data):
        """Record maintenance operation while offline"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        maintenance_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        data_json = json.dumps(data)
        
        cursor.execute('''
        INSERT INTO maintenance_history (id, machine_id, part_id, timestamp, data, synced)
        VALUES (?, ?, ?, ?, ?, 0)
        ''', (maintenance_id, machine_id, part_id, timestamp, data_json))
        
        conn.commit()
        conn.close()
        
        return maintenance_id
    
    def get_pending_maintenance(self):
        """Get maintenance records that need to be synced"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, machine_id, part_id, timestamp, data
        FROM maintenance_history
        WHERE synced = 0
        ORDER BY timestamp
        ''')
        
        records = []
        for row in cursor.fetchall():
            record = {
                'id': row[0],
                'machine_id': row[1],
                'part_id': row[2],
                'timestamp': row[3],
                'data': json.loads(row[4])
            }
            records.append(record)
        
        conn.close()
        return records
    
    def mark_maintenance_synced(self, maintenance_id):
        """Mark a maintenance record as synced"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE maintenance_history SET synced = 1 WHERE id = ?', (maintenance_id,))
        
        conn.commit()
        conn.close()
