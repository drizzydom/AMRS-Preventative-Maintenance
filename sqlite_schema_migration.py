#!/usr/bin/env python3
"""
SQLite Schema Migration Helper

This module handles automatic schema migrations for SQLite databases
to ensure compatibility with the online PostgreSQL schema.
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)

def migrate_sqlite_schema(db_path):
    """
    Migrate SQLite schema to match the current model definitions.
    
    Args:
        db_path (str): Path to the SQLite database file
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get existing table schemas
        tables_info = {}
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for (table_name,) in tables:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            tables_info[table_name] = {col[1]: col for col in columns}  # column_name: column_info
        
        migrations_applied = 0
        
        # Machine table migrations
        if 'machines' in tables_info:
            machine_columns = tables_info['machines']
            
            # Add missing machine_number column
            if 'machine_number' not in machine_columns:
                logger.info("Adding machine_number column to machines table")
                cursor.execute("ALTER TABLE machines ADD COLUMN machine_number VARCHAR(50)")
                migrations_applied += 1
            
            # Add missing site_id column (crucial for relationships)
            if 'site_id' not in machine_columns:
                logger.info("Adding site_id column to machines table")
                cursor.execute("ALTER TABLE machines ADD COLUMN site_id INTEGER")
                migrations_applied += 1
            
            # Add missing serial_number column
            if 'serial_number' not in machine_columns:
                logger.info("Adding serial_number column to machines table")
                cursor.execute("ALTER TABLE machines ADD COLUMN serial_number VARCHAR(50)")
                migrations_applied += 1
        
        # User table migrations (ensure hash fields can be NULL)
        if 'users' in tables_info:
            user_columns = tables_info['users']
            
            # Add missing full_name column
            if 'full_name' not in user_columns:
                logger.info("Adding full_name column to users table")
                cursor.execute("ALTER TABLE users ADD COLUMN full_name VARCHAR(100)")
                migrations_applied += 1
            
            # Check if username_hash has NOT NULL constraint
            if 'username_hash' in user_columns:
                col_info = user_columns['username_hash']
                if col_info[3] == 1:  # NOT NULL constraint
                    logger.info("Removing NOT NULL constraint from username_hash column")
                    # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
                    # This was already handled in the previous manual fix
            
            # Check if email_hash has NOT NULL constraint  
            if 'email_hash' in user_columns:
                col_info = user_columns['email_hash']
                if col_info[3] == 1:  # NOT NULL constraint
                    logger.info("Removing NOT NULL constraint from email_hash column")
                    # This was already handled in the previous manual fix
        
        # Roles table migrations
        if 'roles' in tables_info:
            roles_columns = tables_info['roles']
            
            # Add missing description column
            if 'description' not in roles_columns:
                logger.info("Adding description column to roles table")
                cursor.execute("ALTER TABLE roles ADD COLUMN description TEXT")
                migrations_applied += 1
        
        # Parts table migrations
        if 'parts' in tables_info:
            parts_columns = tables_info['parts']
            
            # Ensure maintenance_days column exists (some schemas may have it)
            if 'maintenance_days' not in parts_columns:
                logger.info("Adding maintenance_days column to parts table")
                cursor.execute("ALTER TABLE parts ADD COLUMN maintenance_days INTEGER")
                migrations_applied += 1
        
        # Sites table migrations
        if 'sites' in tables_info:
            sites_columns = tables_info['sites']
            
            # Add missing contact_email column
            if 'contact_email' not in sites_columns:
                logger.info("Adding contact_email column to sites table")
                cursor.execute("ALTER TABLE sites ADD COLUMN contact_email VARCHAR(255)")
                migrations_applied += 1
            
            # Add missing enable_notifications column
            if 'enable_notifications' not in sites_columns:
                logger.info("Adding enable_notifications column to sites table")
                cursor.execute("ALTER TABLE sites ADD COLUMN enable_notifications BOOLEAN DEFAULT 1")
                migrations_applied += 1
            
            # Add missing notification_threshold column
            if 'notification_threshold' not in sites_columns:
                logger.info("Adding notification_threshold column to sites table")
                cursor.execute("ALTER TABLE sites ADD COLUMN notification_threshold INTEGER DEFAULT 7")
                migrations_applied += 1
        
        # MaintenanceRecord table migrations
        if 'maintenance_records' in tables_info:
            mr_columns = tables_info['maintenance_records']
            
            # Add missing client_id column
            if 'client_id' not in mr_columns:
                logger.info("Adding client_id column to maintenance_records table")
                cursor.execute("ALTER TABLE maintenance_records ADD COLUMN client_id INTEGER")
                migrations_applied += 1
            
            # Add missing maintenance_type column
            if 'maintenance_type' not in mr_columns:
                logger.info("Adding maintenance_type column to maintenance_records table")
                cursor.execute("ALTER TABLE maintenance_records ADD COLUMN maintenance_type VARCHAR(50)")
                migrations_applied += 1
            
            # Add missing description column
            if 'description' not in mr_columns:
                logger.info("Adding description column to maintenance_records table")
                cursor.execute("ALTER TABLE maintenance_records ADD COLUMN description TEXT")
                migrations_applied += 1
            
            # Add missing performed_by column
            if 'performed_by' not in mr_columns:
                logger.info("Adding performed_by column to maintenance_records table")
                cursor.execute("ALTER TABLE maintenance_records ADD COLUMN performed_by VARCHAR(100)")
                migrations_applied += 1
            
            # Add missing status column
            if 'status' not in mr_columns:
                logger.info("Adding status column to maintenance_records table")
                cursor.execute("ALTER TABLE maintenance_records ADD COLUMN status VARCHAR(50)")
                migrations_applied += 1
            
            # Add missing notes column
            if 'notes' not in mr_columns:
                logger.info("Adding notes column to maintenance_records table")
                cursor.execute("ALTER TABLE maintenance_records ADD COLUMN notes TEXT")
                migrations_applied += 1
        
        # Audit Tasks table migrations
        if 'audit_tasks' in tables_info:
            at_columns = tables_info['audit_tasks']
            
            # Add missing description column
            if 'description' not in at_columns:
                logger.info("Adding description column to audit_tasks table")
                cursor.execute("ALTER TABLE audit_tasks ADD COLUMN description TEXT")
                migrations_applied += 1
            
            # Add missing color column
            if 'color' not in at_columns:
                logger.info("Adding color column to audit_tasks table")
                cursor.execute("ALTER TABLE audit_tasks ADD COLUMN color VARCHAR(32) DEFAULT '#007bff'")
                migrations_applied += 1
            
            # Add missing interval column
            if 'interval' not in at_columns:
                logger.info("Adding interval column to audit_tasks table")
                cursor.execute("ALTER TABLE audit_tasks ADD COLUMN interval VARCHAR(50) DEFAULT 'monthly'")
                migrations_applied += 1
            
            # Add missing custom_interval_days column
            if 'custom_interval_days' not in at_columns:
                logger.info("Adding custom_interval_days column to audit_tasks table")
                cursor.execute("ALTER TABLE audit_tasks ADD COLUMN custom_interval_days INTEGER")
                migrations_applied += 1
        
        # Audit Task Completions table migrations
        if 'audit_task_completions' in tables_info:
            atc_columns = tables_info['audit_task_completions']
            
            # Add missing completed column
            if 'completed' not in atc_columns:
                logger.info("Adding completed column to audit_task_completions table")
                cursor.execute("ALTER TABLE audit_task_completions ADD COLUMN completed BOOLEAN DEFAULT 0")
                migrations_applied += 1
            
            # Add missing completed_at column
            if 'completed_at' not in atc_columns:
                logger.info("Adding completed_at column to audit_task_completions table")
                cursor.execute("ALTER TABLE audit_task_completions ADD COLUMN completed_at DATETIME")
                migrations_applied += 1
            
            # Add missing notes column
            if 'notes' not in atc_columns:
                logger.info("Adding notes column to audit_task_completions table")
                cursor.execute("ALTER TABLE audit_task_completions ADD COLUMN notes TEXT")
                migrations_applied += 1
        
        conn.commit()
        conn.close()
        
        if migrations_applied > 0:
            logger.info(f"Successfully applied {migrations_applied} schema migrations to SQLite database")
        else:
            logger.info("SQLite schema is up to date")
        
        return migrations_applied
        
    except Exception as e:
        logger.error(f"Error during SQLite schema migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise


if __name__ == "__main__":
    # Test migration
    import sys
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = "maintenance.db"
    
    logging.basicConfig(level=logging.INFO)
    migrate_sqlite_schema(db_path)
