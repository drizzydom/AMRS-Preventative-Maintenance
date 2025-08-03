"""
fix_user_hashes.py - Recalculate and update username_hash and email_hash for all users in the local SQLite DB

Usage:
    python fix_user_hashes.py [--db <PATH_TO_DB>]

This script will recalculate the username_hash and email_hash fields for all users
using the same logic as the app, and update them in the database.
"""

import sqlite3
import hashlib
import argparse
import os

def hash_value(value):
    if not value:
        return None
    # Use the same normalization as the app (lowercase, strip)
    value = value.strip().lower()
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def fix_hashes(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email FROM users")
    users = cursor.fetchall()
    updated = 0
    for user_id, username, email in users:
        username_hash = hash_value(username)
        email_hash = hash_value(email)
        cursor.execute(
            "UPDATE users SET username_hash = ?, email_hash = ? WHERE id = ?",
            (username_hash, email_hash, user_id)
        )
        updated += 1
    conn.commit()
    conn.close()
    print(f"Updated hashes for {updated} users in {db_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix user hashes in local SQLite DB.")
    parser.add_argument('--db', default=os.path.expanduser('~/Library/Application Support/AMRS_PM/maintenance_secure.db'), help='Path to local SQLite DB')
    args = parser.parse_args()
    fix_hashes(args.db)
