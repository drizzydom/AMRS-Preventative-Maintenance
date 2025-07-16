"""
sync_utils.py - Utilities for importing/exporting AMRS data to/from SQLite DB
"""
import sqlite3
import json
import os

def ensure_database_schema(db_path):
    """Ensure the database schema exists by initializing it with Flask-SQLAlchemy"""
    try:
        from app import app, db
        
        # Set the database URI to point to our target database
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.abspath(db_path)}'
        
        with app.app_context():
            print(f"[sync_utils] Creating database schema for: {db_path}")
            db.create_all()
            print(f"[sync_utils] Database schema created successfully")
            return True
    except Exception as e:
        print(f"[sync_utils] Error creating database schema: {e}")
        return False

def import_json_to_sqlite(json_path, db_path):
    """Import data from JSON file into SQLite database."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    abs_db_path = os.path.abspath(db_path)
    print(f"[sync_utils] Importing into database: {abs_db_path}")
    
    # Ensure database schema exists
    if not os.path.exists(abs_db_path):
        print(f"[sync_utils] Database file does not exist, creating schema: {abs_db_path}")
        if not ensure_database_schema(abs_db_path):
            print(f"[sync_utils] FAILED to create database schema")
            return False
    
    conn = sqlite3.connect(abs_db_path)
    c = conn.cursor()
    # Import users
    for u in data.get('users', []):
        try:
            c.execute("""
                INSERT OR REPLACE INTO users (id, username, email, role_id, is_admin, full_name, password_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (u['id'], u['username'], u['email'], u['role_id'], 
                  int(u.get('is_admin', False)), u.get('full_name', ''), 
                  u.get('password_hash', 'default_hash')))
        except Exception as e:
            print(f"[sync_utils] Error inserting user: {u} | {e}")
    # Import roles
    for r in data.get('roles', []):
        try:
            c.execute("""
                INSERT OR REPLACE INTO roles (id, name, permissions)
                VALUES (?, ?, ?)
            """, (r['id'], r['name'], r['permissions']))
        except Exception as e:
            print(f"[sync_utils] Error inserting role: {r} | {e}")
    # Import sites
    for s in data.get('sites', []):
        try:
            c.execute("""
                INSERT OR REPLACE INTO sites (id, name, location)
                VALUES (?, ?, ?)
            """, (s['id'], s['name'], s.get('location', '')))
        except Exception as e:
            print(f"[sync_utils] Error inserting site: {s} | {e}")
    # Import machines
    for m in data.get('machines', []):
        try:
            c.execute("""
                INSERT OR REPLACE INTO machines (id, name, model, serial_number, machine_number, site_id, decommissioned)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (m['id'], m['name'], m['model'], m['serial_number'], 
                  m['machine_number'], m['site_id'], int(m.get('decommissioned', False))))
        except Exception as e:
            print(f"[sync_utils] Error inserting machine: {m} | {e}")
    # Import parts
    for p in data.get('parts', []):
        try:
            c.execute("""
                INSERT OR REPLACE INTO parts (id, name, description, machine_id, maintenance_frequency, maintenance_unit, last_maintenance, next_maintenance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (p['id'], p['name'], p['description'], p['machine_id'], p['maintenance_frequency'], p['maintenance_unit'], p['last_maintenance'], p['next_maintenance']))
        except Exception as e:
            print(f"[sync_utils] Error inserting part: {p} | {e}")
    # Import maintenance_records
    for r in data.get('maintenance_records', []):
        try:
            c.execute("""
                INSERT OR REPLACE INTO maintenance_records (id, machine_id, part_id, user_id, maintenance_type, description, date, performed_by, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (r['id'], r['machine_id'], r['part_id'], r['user_id'], r['maintenance_type'], r['description'], r['date'], r['performed_by'], r['status'], r['notes']))
        except Exception as e:
            print(f"[sync_utils] Error inserting maintenance_record: {r} | {e}")
    conn.commit()
    conn.close()
    print(f"[sync_utils] Successfully imported data from {json_path} into {db_path}")
    return True

# You can add export and merge logic here as needed.
