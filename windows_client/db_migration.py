import os
import sqlite3
import logging
from datetime import datetime

class DatabaseMigration:
    """Handles database schema migrations for the offline database"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.logger = logging.getLogger("DatabaseMigration")
        
        # Set up logging
        handler = logging.FileHandler("db_migration.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def run_migrations(self):
        """Run all necessary migrations"""
        self.logger.info(f"Starting database migrations on {self.db_path}")
        
        # Check if database exists
        if not os.path.exists(self.db_path):
            self.logger.info("Database file doesn't exist. No migrations needed.")
            return True
            
        # Connect to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Create versions table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS schema_versions (
                version INTEGER PRIMARY KEY,
                applied_at TEXT,
                description TEXT
            )
            ''')
            
            # Get current version
            cursor.execute("SELECT MAX(version) FROM schema_versions")
            result = cursor.fetchone()
            current_version = result[0] if result and result[0] is not None else 0
            
            self.logger.info(f"Current schema version: {current_version}")
            
            # Run migrations based on current version
            migrations_run = 0
            
            # Migration 1: Add failure tracking columns
            if current_version < 1:
                self.logger.info("Running migration 1: Add failure tracking columns")
                self._run_migration_1(cursor)
                self._record_migration(cursor, 1, "Add failure tracking columns")
                migrations_run += 1
            
            # Migration 2: Add version tracking and data hash columns
            if current_version < 2:
                self.logger.info("Running migration 2: Add version tracking and data hash columns")
                self._run_migration_2(cursor)
                self._record_migration(cursor, 2, "Add version tracking and data hash columns")
                migrations_run += 1
                
            # Migration 3: Create sites and parts tables
            if current_version < 3:
                self.logger.info("Running migration 3: Create sites and parts tables")
                self._run_migration_3(cursor)
                self._record_migration(cursor, 3, "Create sites and parts tables")
                migrations_run += 1
            
            # Migration 4: Add settings table
            if current_version < 4:
                self.logger.info("Running migration 4: Add settings table")
                self._run_migration_4(cursor)
                self._record_migration(cursor, 4, "Add settings table")
                migrations_run += 1
                
            # Commit changes
            conn.commit()
            
            self.logger.info(f"Database migration completed. Ran {migrations_run} migrations.")
            return True
            
        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            conn.rollback()
            return False
            
        finally:
            conn.close()
    
    def _record_migration(self, cursor, version, description):
        """Record that a migration was applied"""
        cursor.execute('''
        INSERT INTO schema_versions (version, applied_at, description)
        VALUES (?, ?, ?)
        ''', (version, datetime.now().isoformat(), description))
    
    def _run_migration_1(self, cursor):
        """Migration 1: Add failure tracking columns"""
        # Add failure tracking to pending_operations
        self._add_column_if_not_exists(cursor, "pending_operations", "failure_data", "TEXT")
        self._add_column_if_not_exists(cursor, "pending_operations", "sync_attempts", "INTEGER DEFAULT 0")
        
        # Add failure tracking to maintenance_history
        self._add_column_if_not_exists(cursor, "maintenance_history", "failure_data", "TEXT")
        self._add_column_if_not_exists(cursor, "maintenance_history", "sync_attempts", "INTEGER DEFAULT 0")
        
    def _run_migration_2(self, cursor):
        """Migration 2: Add version tracking and data hash columns"""
        # Add version tracking to tables
        self._add_column_if_not_exists(cursor, "pending_operations", "version", "INTEGER DEFAULT 1")
        self._add_column_if_not_exists(cursor, "maintenance_history", "version", "INTEGER DEFAULT 1")
        self._add_column_if_not_exists(cursor, "machines", "version", "INTEGER DEFAULT 1")
        
        # Add data hash for integrity checking
        self._add_column_if_not_exists(cursor, "pending_operations", "data_hash", "TEXT")
        self._add_column_if_not_exists(cursor, "maintenance_history", "data_hash", "TEXT")
        self._add_column_if_not_exists(cursor, "machines", "data_hash", "TEXT")
        self._add_column_if_not_exists(cursor, "cached_data", "data_hash", "TEXT")
    
    def _run_migration_3(self, cursor):
        """Migration 3: Create sites and parts tables"""
        # Create sites table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sites (
            id TEXT PRIMARY KEY,
            data TEXT,
            data_hash TEXT,
            last_updated TEXT,
            version INTEGER DEFAULT 1
        )
        ''')
        
        # Create parts table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS parts (
            id TEXT PRIMARY KEY,
            data TEXT,
            data_hash TEXT,
            last_updated TEXT,
            version INTEGER DEFAULT 1
        )
        ''')
    
    def _run_migration_4(self, cursor):
        """Migration 4: Add settings table"""
        # Create settings table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        )
        ''')
    
    def _add_column_if_not_exists(self, cursor, table, column, definition):
        """Add a column to a table if it doesn't exist"""
        try:
            # Check if column exists
            cursor.execute(f"SELECT {column} FROM {table} LIMIT 0")
            # If we get here, column exists
            self.logger.info(f"Column {column} already exists in {table}")
            return False
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            self.logger.info(f"Adding column {column} to {table}")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            return True
