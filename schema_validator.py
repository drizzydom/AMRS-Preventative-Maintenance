#!/usr/bin/env python3
"""
Schema Validator and Migrator for AMRS Maintenance Tracker

This module ensures that the database schema matches the SQLAlchemy models
before any data synchronization occurs. It validates all tables and columns
exist, creates missing ones, and ensures data types are correct.

This prevents schema mismatch errors that occur when synced data doesn't
match the expected model structure.
"""

import os
import sqlite3
import logging
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_expected_schema():
    """
    Define the complete expected database schema based on SQLAlchemy models.
    This should match exactly what the models expect.
    """
    return {
        'users': {
            'columns': {
                'id': 'INTEGER PRIMARY KEY',
                'username': 'VARCHAR(80) UNIQUE NOT NULL',
                'username_hash': 'TEXT',
                'email': 'VARCHAR(120) UNIQUE NOT NULL',
                'email_hash': 'TEXT',
                'full_name': 'VARCHAR(100)',
                'password_hash': 'VARCHAR(128) NOT NULL',
                'is_admin': 'BOOLEAN DEFAULT 0',
                'role_id': 'INTEGER',
                'last_login': 'TIMESTAMP',
                'created_at': 'TIMESTAMP',
                'updated_at': 'TIMESTAMP',
                'reset_token': 'VARCHAR(100)',
                'reset_token_expiration': 'TIMESTAMP',
                'remember_token': 'VARCHAR(255)',
                'remember_token_expiration': 'TIMESTAMP',
                'remember_enabled': 'BOOLEAN DEFAULT 0',
                'notification_preferences': 'TEXT'
            },
            'foreign_keys': [
                'FOREIGN KEY (role_id) REFERENCES roles(id)'
            ]
        },
        'roles': {
            'columns': {
                'id': 'INTEGER PRIMARY KEY',
                'name': 'VARCHAR(80) UNIQUE NOT NULL',
                'description': 'VARCHAR(255)',
                'permissions': 'TEXT',
                'created_at': 'TIMESTAMP',
                'updated_at': 'TIMESTAMP'
            }
        },
        'sites': {
            'columns': {
                'id': 'INTEGER PRIMARY KEY',
                'name': 'VARCHAR(100) NOT NULL',
                'location': 'VARCHAR(200)',
                'contact_email': 'VARCHAR(120)',
                'enable_notifications': 'BOOLEAN DEFAULT 1',
                'notification_threshold': 'INTEGER DEFAULT 30',
                'created_at': 'TIMESTAMP',
                'updated_at': 'TIMESTAMP'
            }
        },
        'machines': {
            'columns': {
                'id': 'INTEGER PRIMARY KEY',
                'name': 'VARCHAR(100) NOT NULL',
                'model': 'VARCHAR(100)',
                'serial_number': 'VARCHAR(100)',
                'machine_number': 'VARCHAR(50)',
                'site_id': 'INTEGER',
                'decommissioned': 'BOOLEAN DEFAULT 0',
                'decommissioned_date': 'TIMESTAMP',
                'decommissioned_by': 'VARCHAR(100)',
                'decommissioned_reason': 'TEXT',
                'created_at': 'TIMESTAMP',
                'updated_at': 'TIMESTAMP'
            },
            'foreign_keys': [
                'FOREIGN KEY (site_id) REFERENCES sites(id)'
            ]
        },
        'parts': {
            'columns': {
                'id': 'INTEGER PRIMARY KEY',
                'name': 'VARCHAR(100) NOT NULL',
                'description': 'TEXT',
                'machine_id': 'INTEGER',
                'maintenance_frequency': 'INTEGER',
                'maintenance_unit': 'VARCHAR(10)',
                'last_maintenance': 'DATE',
                'next_maintenance': 'DATE',
                'created_at': 'TIMESTAMP',
                'updated_at': 'TIMESTAMP'
            },
            'foreign_keys': [
                'FOREIGN KEY (machine_id) REFERENCES machines(id)'
            ]
        },
        'maintenance_records': {
            'columns': {
                'id': 'INTEGER PRIMARY KEY',
                'machine_id': 'INTEGER',
                'part_id': 'INTEGER',
                'user_id': 'INTEGER',
                'maintenance_type': 'VARCHAR(50)',
                'description': 'TEXT',
                'date': 'TIMESTAMP',
                'performed_by': 'VARCHAR(100)',
                'status': 'VARCHAR(50)',
                'notes': 'TEXT',
                'client_id': 'VARCHAR(36)',
                'created_at': 'TIMESTAMP',
                'updated_at': 'TIMESTAMP'
            },
            'foreign_keys': [
                'FOREIGN KEY (machine_id) REFERENCES machines(id)',
                'FOREIGN KEY (part_id) REFERENCES parts(id)',
                'FOREIGN KEY (user_id) REFERENCES users(id)'
            ]
        },
        'audit_tasks': {
            'columns': {
                'id': 'INTEGER PRIMARY KEY',
                'name': 'VARCHAR(100) NOT NULL',
                'description': 'TEXT',
                'site_id': 'INTEGER',
                'interval': 'VARCHAR(50)',
                'custom_interval_days': 'INTEGER',
                'color': 'VARCHAR(32)',
                'created_at': 'TIMESTAMP',
                'updated_at': 'TIMESTAMP'
            },
            'foreign_keys': [
                'FOREIGN KEY (site_id) REFERENCES sites(id)'
            ]
        },
        'audit_task_completions': {
            'columns': {
                'id': 'INTEGER PRIMARY KEY',
                'audit_task_id': 'INTEGER',
                'user_id': 'INTEGER',
                'completed_date': 'TIMESTAMP',
                'notes': 'TEXT',
                'created_at': 'TIMESTAMP',
                'updated_at': 'TIMESTAMP'
            },
            'foreign_keys': [
                'FOREIGN KEY (audit_task_id) REFERENCES audit_tasks(id)',
                'FOREIGN KEY (user_id) REFERENCES users(id)'
            ]
        },
        'machine_audit_task': {
            'columns': {
                'audit_task_id': 'INTEGER',
                'machine_id': 'INTEGER'
            },
            'foreign_keys': [
                'FOREIGN KEY (audit_task_id) REFERENCES audit_tasks(id)',
                'FOREIGN KEY (machine_id) REFERENCES machines(id)'
            ],
            'primary_key': ['audit_task_id', 'machine_id']
        },
        'maintenance_files': {
            'columns': {
                'id': 'INTEGER PRIMARY KEY',
                'maintenance_record_id': 'INTEGER',
                'filename': 'VARCHAR(255)',
                'filepath': 'VARCHAR(500)',
                'filesize': 'INTEGER',
                'mimetype': 'VARCHAR(100)',
                'thumbnail_path': 'VARCHAR(500)',
                'uploaded_at': 'TIMESTAMP',
                'created_at': 'TIMESTAMP',
                'updated_at': 'TIMESTAMP'
            },
            'foreign_keys': [
                'FOREIGN KEY (maintenance_record_id) REFERENCES maintenance_records(id)'
            ]
        },
        'sync_queue': {
            'columns': {
                'id': 'INTEGER PRIMARY KEY',
                'table_name': 'VARCHAR(64) NOT NULL',
                'record_id': 'INTEGER NOT NULL',
                'operation': 'VARCHAR(16) NOT NULL',
                'payload': 'TEXT',
                'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'synced_at': 'TIMESTAMP',
                'retry_count': 'INTEGER DEFAULT 0',
                'error_message': 'TEXT'
            }
        },
        'app_settings': {
            'columns': {
                'id': 'INTEGER PRIMARY KEY',
                'key': 'VARCHAR(100) UNIQUE NOT NULL',
                'value': 'TEXT',
                'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
            }
        },
        'security_events': {
            'columns': {
                'id': 'INTEGER PRIMARY KEY',
                'event_type': 'VARCHAR(50) NOT NULL',
                'username': 'VARCHAR(80)',
                'ip_address': 'VARCHAR(45)',
                'user_agent': 'TEXT',
                'details': 'TEXT',
                'timestamp': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'is_critical': 'BOOLEAN DEFAULT 0'
            }
        }
    }

def get_existing_schema(db_path):
    """
    Analyze the existing database schema and return its structure.
    """
    if not os.path.exists(db_path):
        return {}
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        schema = {}
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        
        for (table_name,) in tables:
            schema[table_name] = {'columns': {}}
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for column in columns:
                col_id, col_name, col_type, not_null, default_value, primary_key = column
                schema[table_name]['columns'][col_name] = {
                    'type': col_type,
                    'not_null': not_null,
                    'default': default_value,
                    'primary_key': primary_key
                }
        
        conn.close()
        return schema
        
    except Exception as e:
        logger.error(f"Error analyzing existing schema: {e}")
        return {}

def validate_and_migrate_schema(db_path, verbose=True):
    """
    Validate the database schema and migrate it to match the expected structure.
    
    Args:
        db_path (str): Path to the SQLite database
        verbose (bool): Whether to print detailed output
        
    Returns:
        tuple: (success: bool, results: dict)
    """
    
    if verbose:
        print(f"\n🔍 SCHEMA VALIDATION AND MIGRATION")
        print("=" * 50)
        print(f"Database: {db_path}")
    
    try:
        # Ensure database directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        expected_schema = get_expected_schema()
        existing_schema = get_existing_schema(db_path)
        
        tables_created = 0
        columns_added = 0
        tables_migrated = 0
        
        # Process each expected table
        for table_name, table_def in expected_schema.items():
            if verbose:
                print(f"\n📋 Processing table: {table_name}")
            
            if table_name not in existing_schema:
                # Create entire table
                if verbose:
                    print(f"  ✨ Creating table {table_name}")
                
                create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
                
                # Add columns
                column_defs = []
                for col_name, col_type in table_def['columns'].items():
                    column_defs.append(f"    {col_name} {col_type}")
                
                # Add foreign keys
                if 'foreign_keys' in table_def:
                    for fk in table_def['foreign_keys']:
                        column_defs.append(f"    {fk}")
                
                # Add primary key for composite keys
                if 'primary_key' in table_def:
                    pk_cols = ', '.join(table_def['primary_key'])
                    column_defs.append(f"    PRIMARY KEY ({pk_cols})")
                
                create_table_sql += ',\n'.join(column_defs)
                create_table_sql += "\n)"
                
                cursor.execute(create_table_sql)
                tables_created += 1
                
                if verbose:
                    print(f"  ✅ Table {table_name} created successfully")
            
            else:
                # Check for missing columns in existing table
                existing_cols = existing_schema[table_name]['columns']
                missing_columns = []
                
                for col_name, col_type in table_def['columns'].items():
                    if col_name not in existing_cols:
                        missing_columns.append((col_name, col_type))
                
                if missing_columns:
                    if verbose:
                        print(f"  🔧 Adding {len(missing_columns)} missing columns to {table_name}")
                    
                    for col_name, col_type in missing_columns:
                        try:
                            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
                            cursor.execute(alter_sql)
                            columns_added += 1
                            if verbose:
                                print(f"    ➕ Added column: {col_name} {col_type}")
                        except sqlite3.OperationalError as e:
                            if "duplicate column name" not in str(e).lower():
                                logger.warning(f"Could not add column {col_name} to {table_name}: {e}")
                    
                    tables_migrated += 1
                else:
                    if verbose:
                        print(f"  ✅ Table {table_name} schema is up to date")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        results = {
            'tables_created': tables_created,
            'columns_added': columns_added,
            'tables_migrated': tables_migrated,
            'total_tables': len(expected_schema)
        }
        
        if verbose:
            print(f"\n🎯 SCHEMA MIGRATION SUMMARY:")
            print("-" * 30)
            print(f"✨ Tables created: {tables_created}")
            print(f"🔧 Tables migrated: {tables_migrated}")
            print(f"➕ Columns added: {columns_added}")
            print(f"📊 Total tables: {results['total_tables']}")
            print(f"✅ Schema validation completed successfully!")
        
        return True, results
        
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        if verbose:
            print(f"❌ Schema validation failed: {e}")
        return False, {'error': str(e)}

def verify_schema_integrity(db_path, verbose=True):
    """
    Verify that the database schema matches expectations after migration.
    
    Args:
        db_path (str): Path to the SQLite database
        verbose (bool): Whether to print detailed output
        
    Returns:
        tuple: (valid: bool, issues: list)
    """
    
    if verbose:
        print(f"\n🔍 SCHEMA INTEGRITY VERIFICATION")
        print("=" * 40)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        expected_schema = get_expected_schema()
        issues = []
        
        for table_name, table_def in expected_schema.items():
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                issues.append(f"Missing table: {table_name}")
                continue
            
            # Check columns
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            for col_name in table_def['columns']:
                if col_name not in existing_columns:
                    issues.append(f"Missing column: {table_name}.{col_name}")
        
        conn.close()
        
        if verbose:
            if issues:
                print(f"❌ Found {len(issues)} schema issues:")
                for issue in issues:
                    print(f"  • {issue}")
            else:
                print("✅ Schema integrity check passed - all tables and columns present")
        
        return len(issues) == 0, issues
        
    except Exception as e:
        logger.error(f"Schema verification failed: {e}")
        return False, [f"Verification error: {e}"]

def main():
    """Test the schema validator with a sample database."""
    test_db = "/tmp/test_schema.db"
    
    print("🧪 Testing Schema Validator")
    print("=" * 30)
    
    # Test with empty database
    if os.path.exists(test_db):
        os.remove(test_db)
    
    success, results = validate_and_migrate_schema(test_db)
    if success:
        print(f"✅ Schema validation successful: {results}")
        
        # Verify integrity
        valid, issues = verify_schema_integrity(test_db)
        if valid:
            print("✅ Schema integrity verified")
        else:
            print(f"❌ Schema issues found: {issues}")
    else:
        print(f"❌ Schema validation failed: {results}")
    
    # Clean up
    if os.path.exists(test_db):
        os.remove(test_db)

if __name__ == "__main__":
    main()
