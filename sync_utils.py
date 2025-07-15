"""
sync_utils.py - Utilities for importing/exporting AMRS data to/from SQLite DB
"""
import sqlite3
import json
import os

def import_json_to_sqlite(json_path, db_path):
    """Import data from JSON file into SQLite database."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Import users
    for u in data.get('users', []):
        c.execute("""
            INSERT OR REPLACE INTO user (id, username, email, role_id, is_admin, active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (u['id'], u['username'], u['email'], u['role_id'], int(u.get('is_admin', False)), int(u.get('active', True))))
    # Import roles
    for r in data.get('roles', []):
        c.execute("""
            INSERT OR REPLACE INTO role (id, name, permissions)
            VALUES (?, ?, ?)
        """, (r['id'], r['name'], r['permissions']))
    # Import sites
    for s in data.get('sites', []):
        c.execute("""
            INSERT OR REPLACE INTO site (id, name, location)
            VALUES (?, ?, ?)
        """, (s['id'], s['name'], s.get('location', '')))
    # Import machines
    for m in data.get('machines', []):
        c.execute("""
            INSERT OR REPLACE INTO machine (id, name, model, serial_number, machine_number, site_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (m['id'], m['name'], m['model'], m['serial_number'], m['machine_number'], m['site_id']))
    # Import parts
    for p in data.get('parts', []):
        c.execute("""
            INSERT OR REPLACE INTO part (id, name, description, machine_id, maintenance_frequency, maintenance_unit, last_maintenance, next_maintenance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (p['id'], p['name'], p['description'], p['machine_id'], p['maintenance_frequency'], p['maintenance_unit'], p['last_maintenance'], p['next_maintenance']))
    # Import maintenance_records
    for r in data.get('maintenance_records', []):
        c.execute("""
            INSERT OR REPLACE INTO maintenance_record (id, machine_id, part_id, user_id, maintenance_type, description, date, performed_by, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (r['id'], r['machine_id'], r['part_id'], r['user_id'], r['maintenance_type'], r['description'], r['date'], r['performed_by'], r['status'], r['notes']))
    conn.commit()
    conn.close()
    print(f"Imported data from {json_path} into {db_path}")

# You can add export and merge logic here as needed.
