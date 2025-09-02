import sqlite3
import os

# Path to your offline SQLite database (adjust if needed)
DB_PATH = os.path.expanduser('~/Library/Application Support/AMRS_PM/maintenance_secure.db')
if not os.path.exists(DB_PATH):
    DB_PATH = os.path.expanduser('~/.local/share/AMRS_PM/maintenance_secure.db')
if not os.path.exists(DB_PATH):
    DB_PATH = './maintenance_secure.db'  # fallback for test

# List of required tables and their required columns
REQUIRED_SCHEMA = {
    'users': [
        'id', 'username', 'email', 'password_hash', 'role_id', 'created_at', 'updated_at',
        'last_login', 'reset_token', 'reset_token_expiration', 'remember_token',
        'remember_token_expiration', 'remember_enabled', 'username_hash', 'email_hash'
    ],
    'roles': [
        'id', 'name', 'permissions', 'description', 'created_at', 'updated_at'
    ],
    'sites': [
        'id', 'name', 'location', 'created_at', 'updated_at'
    ],
    'machines': [
        'id', 'name', 'site_id', 'created_at', 'updated_at'
    ],
    'parts': [
        'id', 'name', 'machine_id', 'created_at', 'updated_at', 'last_maintenance', 'next_maintenance',
        'maintenance_frequency', 'maintenance_unit'
    ],
    'maintenance_records': [
        'id', 'part_id', 'user_id', 'date', 'comments', 'description', 'machine_id', 'created_at', 'updated_at'
    ],
    'audit_tasks': [
        'id', 'name', 'interval', 'custom_interval_days', 'color', 'created_at', 'updated_at'
    ],
    'audit_task_completions': [
        'id', 'audit_task_id', 'machine_id', 'date', 'completed', 'created_at', 'updated_at'
    ],
    'sync_queue': [
        'id', 'table_name', 'record_id', 'operation', 'payload', 'timestamp', 'synced'
    ],
    # Add any other required tables and columns here
}

def check_schema(db_path):
    print(f"Checking schema for database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    missing = False

    for table, columns in REQUIRED_SCHEMA.items():
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if not cursor.fetchone():
            print(f"❌ Table missing: {table}")
            missing = True
            continue
        cursor.execute(f"PRAGMA table_info({table})")
        existing_cols = {row[1] for row in cursor.fetchall()}
        for col in columns:
            if col not in existing_cols:
                print(f"❌ Column missing in {table}: {col}")
                missing = True

    if not missing:
        print("✅ All required tables and columns are present!")
    else:
        print("⚠️  Some tables/columns are missing. Check your models and migrations.")

    conn.close()

if __name__ == "__main__":
    check_schema(DB_PATH)
