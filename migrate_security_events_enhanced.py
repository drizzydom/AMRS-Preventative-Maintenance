"""
Migration script to enhance security_events and offline_security_events tables
with additional fields for better tracking, filtering, and correlation.

Adds:
- severity (smallint): 0=info, 1=notice, 2=warning, 3=critical
- source (varchar): 'web', 'offline-client', 'sync-agent', 'installer', etc.
- correlation_id (varchar): UUID for grouping related events
- actor_metadata (text/jsonb): Non-sensitive metadata (sanitized IP, user_agent, device_id)

Run with: python migrate_security_events_enhanced.py
"""

from models import db
from sqlalchemy import Column, Integer, String, Text, inspect
import sys

def column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def upgrade():
    """Add new columns to security_events and offline_security_events tables."""
    print("[MIGRATION] Starting security events enhancement migration...")
    
    tables_to_migrate = ['security_events', 'offline_security_events']
    
    for table_name in tables_to_migrate:
        print(f"\n[MIGRATION] Processing table: {table_name}")
        
        # Check if table exists
        inspector = inspect(db.engine)
        if table_name not in inspector.get_table_names():
            print(f"[MIGRATION] Table {table_name} does not exist. Skipping.")
            continue
        
        # Add severity column (0=info, 1=notice, 2=warning, 3=critical)
        if not column_exists(table_name, 'severity'):
            print(f"[MIGRATION] Adding 'severity' column to {table_name}...")
            try:
                # SQLite and PostgreSQL compatible syntax
                db.engine.execute(f"ALTER TABLE {table_name} ADD COLUMN severity INTEGER DEFAULT 0")
                print(f"[MIGRATION] ✓ Added 'severity' column to {table_name}")
            except Exception as e:
                print(f"[MIGRATION] ✗ Error adding 'severity' to {table_name}: {e}")
        else:
            print(f"[MIGRATION] 'severity' column already exists in {table_name}")
        
        # Add source column ('web', 'offline-client', 'sync-agent', etc.)
        if not column_exists(table_name, 'source'):
            print(f"[MIGRATION] Adding 'source' column to {table_name}...")
            try:
                db.engine.execute(f"ALTER TABLE {table_name} ADD COLUMN source VARCHAR(32) DEFAULT 'web'")
                print(f"[MIGRATION] ✓ Added 'source' column to {table_name}")
            except Exception as e:
                print(f"[MIGRATION] ✗ Error adding 'source' to {table_name}: {e}")
        else:
            print(f"[MIGRATION] 'source' column already exists in {table_name}")
        
        # Add correlation_id column (UUID for grouping related events)
        if not column_exists(table_name, 'correlation_id'):
            print(f"[MIGRATION] Adding 'correlation_id' column to {table_name}...")
            try:
                db.engine.execute(f"ALTER TABLE {table_name} ADD COLUMN correlation_id VARCHAR(36)")
                print(f"[MIGRATION] ✓ Added 'correlation_id' column to {table_name}")
            except Exception as e:
                print(f"[MIGRATION] ✗ Error adding 'correlation_id' to {table_name}: {e}")
        else:
            print(f"[MIGRATION] 'correlation_id' column already exists in {table_name}")
        
        # Add actor_metadata column (JSON text for non-sensitive metadata)
        if not column_exists(table_name, 'actor_metadata'):
            print(f"[MIGRATION] Adding 'actor_metadata' column to {table_name}...")
            try:
                db.engine.execute(f"ALTER TABLE {table_name} ADD COLUMN actor_metadata TEXT")
                print(f"[MIGRATION] ✓ Added 'actor_metadata' column to {table_name}")
            except Exception as e:
                print(f"[MIGRATION] ✗ Error adding 'actor_metadata' to {table_name}: {e}")
        else:
            print(f"[MIGRATION] 'actor_metadata' column already exists in {table_name}")
    
    print("\n[MIGRATION] Security events enhancement migration complete!")
    return True

def downgrade():
    """Remove the new columns (use with caution)."""
    print("[MIGRATION] Starting downgrade of security events enhancement...")
    
    tables_to_migrate = ['security_events', 'offline_security_events']
    columns_to_remove = ['severity', 'source', 'correlation_id', 'actor_metadata']
    
    for table_name in tables_to_migrate:
        print(f"\n[MIGRATION] Processing table: {table_name}")
        
        # Check if table exists
        inspector = inspect(db.engine)
        if table_name not in inspector.get_table_names():
            print(f"[MIGRATION] Table {table_name} does not exist. Skipping.")
            continue
        
        for column_name in columns_to_remove:
            if column_exists(table_name, column_name):
                print(f"[MIGRATION] Dropping '{column_name}' column from {table_name}...")
                try:
                    # Note: SQLite doesn't support DROP COLUMN before version 3.35.0
                    # This will work in PostgreSQL and newer SQLite versions
                    db.engine.execute(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")
                    print(f"[MIGRATION] ✓ Dropped '{column_name}' column from {table_name}")
                except Exception as e:
                    print(f"[MIGRATION] ✗ Error dropping '{column_name}' from {table_name}: {e}")
                    print(f"[MIGRATION] Note: SQLite < 3.35.0 doesn't support DROP COLUMN")
            else:
                print(f"[MIGRATION] '{column_name}' column doesn't exist in {table_name}")
    
    print("\n[MIGRATION] Security events enhancement downgrade complete!")
    return True

if __name__ == '__main__':
    # Import app to get database context
    try:
        from app import app
        with app.app_context():
            if len(sys.argv) > 1 and sys.argv[1] == 'downgrade':
                downgrade()
            else:
                upgrade()
    except Exception as e:
        print(f"[MIGRATION] Error running migration: {e}")
        print(f"[MIGRATION] Make sure to run this script with app context available.")
        sys.exit(1)
