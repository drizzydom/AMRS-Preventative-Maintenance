import os
import logging
import json
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from datetime import datetime

class PostgresAdapter:
    """
    Adapter for PostgreSQL database operations providing an abstraction layer 
    between the application and the database.
    """
    
    def __init__(self, connection_string=None):
        self.logger = logging.getLogger("PostgresAdapter")
        
        # Set up logging
        handler = logging.FileHandler("postgres_adapter.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Connection string setup
        self.connection_string = connection_string or os.environ.get('DATABASE_URL')
        
        if not self.connection_string:
            self.logger.error("No PostgreSQL connection string provided!")
            raise ValueError("PostgreSQL connection string is required")
            
        # Initialize connection pool for better performance
        self._setup_connection_pool()
        
        self.logger.info("PostgresAdapter initialized")
    
    def _setup_connection_pool(self, min_connections=1, max_connections=10):
        """Set up a connection pool for efficient database access"""
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                min_connections,
                max_connections,
                self.connection_string
            )
            self.logger.info(f"Connection pool created with {min_connections}-{max_connections} connections")
        except Exception as e:
            self.logger.error(f"Error creating connection pool: {e}")
            raise
    
    def get_connection(self):
        """Get a connection from the pool"""
        try:
            conn = self.connection_pool.getconn()
            return conn
        except Exception as e:
            self.logger.error(f"Error getting connection from pool: {e}")
            raise
    
    def release_connection(self, conn):
        """Return a connection to the pool"""
        try:
            self.connection_pool.putconn(conn)
        except Exception as e:
            self.logger.error(f"Error returning connection to pool: {e}")
    
    def execute_query(self, query, params=None):
        """Execute a query and return the results as a list of dictionaries"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params or ())
                if cursor.description:
                    return cursor.fetchall()
                else:
                    return None
        except Exception as e:
            self.logger.error(f"Query execution error: {e}")
            raise
        finally:
            if conn:
                self.release_connection(conn)
    
    def execute_update(self, query, params=None):
        """Execute an update query and return the affected row count"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Update execution error: {e}")
            raise
        finally:
            if conn:
                self.release_connection(conn)
    
    def get_sites(self, modified_since=None):
        """Get all sites, optionally only those modified since a specific time"""
        query = "SELECT * FROM sites"
        params = []
        
        if modified_since:
            query += " WHERE updated_at > %s"
            params.append(modified_since)
            
        query += " ORDER BY name"
        
        return self.execute_query(query, params)
    
    def get_machines(self, site_id=None, modified_since=None):
        """Get machines, filtered by site_id if provided"""
        query = "SELECT * FROM machines"
        params = []
        
        where_clauses = []
        if site_id:
            where_clauses.append("site_id = %s")
            params.append(site_id)
            
        if modified_since:
            where_clauses.append("updated_at > %s")
            params.append(modified_since)
            
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        query += " ORDER BY name"
        
        return self.execute_query(query, params)
    
    def get_parts(self, machine_id=None, site_id=None, status=None, modified_since=None):
        """
        Get parts with flexible filtering.
        status can be: 'overdue', 'due_soon', 'ok'
        """
        query = """
            SELECT p.*, m.name as machine_name, s.name as site_name 
            FROM parts p
            JOIN machines m ON p.machine_id = m.id
            JOIN sites s ON m.site_id = s.id
        """
        
        params = []
        where_clauses = []
        
        if machine_id:
            where_clauses.append("p.machine_id = %s")
            params.append(machine_id)
            
        if site_id:
            where_clauses.append("m.site_id = %s")
            params.append(site_id)
            
        if status:
            now = datetime.now()
            if status == 'overdue':
                where_clauses.append("p.next_maintenance < %s")
                params.append(now)
            elif status == 'due_soon':
                where_clauses.append("p.next_maintenance > %s AND p.next_maintenance <= %s")
                params.append(now)
                # "Due soon" means due in the next 30 days
                params.append(now + timedelta(days=30))
            elif status == 'ok':
                where_clauses.append("p.next_maintenance > %s")
                params.append(now + timedelta(days=30))
        
        if modified_since:
            where_clauses.append("p.updated_at > %s")
            params.append(modified_since)
            
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        query += " ORDER BY p.next_maintenance"
        
        return self.execute_query(query, params)
    
    def create_maintenance_record(self, part_id, user_id, notes, timestamp=None):
        """Create a maintenance record in the PostgreSQL database"""
        if not timestamp:
            timestamp = datetime.now()
            
        query = """
            INSERT INTO maintenance_records (part_id, user_id, date, comments, created_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        
        # Handle the part update separately
        part_update_query = """
            UPDATE parts
            SET last_maintenance = %s, 
                next_maintenance = %s + make_interval(days := maintenance_days),
                updated_at = %s
            WHERE id = %s
        """
        
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Create maintenance record
                cursor.execute(query, (part_id, user_id, timestamp, notes, timestamp))
                record_id = cursor.fetchone()['id']
                
                # Update part's maintenance dates
                cursor.execute(part_update_query, (timestamp, timestamp, timestamp, part_id))
                
                # Get updated part information
                cursor.execute("SELECT * FROM parts WHERE id = %s", (part_id,))
                updated_part = cursor.fetchone()
                
                conn.commit()
                
                return {
                    "record_id": record_id,
                    "part": dict(updated_part) if updated_part else None
                }
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Error creating maintenance record: {e}")
            raise
        finally:
            if conn:
                self.release_connection(conn)
    
    def close(self):
        """Close all connections in the pool"""
        if hasattr(self, 'connection_pool'):
            self.connection_pool.closeall()
            self.logger.info("All database connections closed")
