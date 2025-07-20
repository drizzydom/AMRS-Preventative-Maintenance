"""
Script to ensure 'api_token' and 'api_token_expiration' columns exist on the 'users' table
for both SQLite (offline/local) and PostgreSQL (online/Render) environments.

Usage:
    python fix_user_token_columns.py

Set DATABASE_URL in your environment for PostgreSQL, or run in the project directory for SQLite.
"""
import os
import sys
from sqlalchemy import create_engine, text

# Try to import db config if available
try:
    from config import Config
    DB_URI = os.environ.get('DATABASE_URL') or getattr(Config, 'SQLALCHEMY_DATABASE_URI', None)
except Exception:
    DB_URI = os.environ.get('DATABASE_URL')

if not DB_URI:
    # Default to local SQLite
    DB_URI = 'sqlite:///maintenance.db'

print(f"[INFO] Using database URI: {DB_URI}")
engine = create_engine(DB_URI)

with engine.connect() as conn:
    # Detect DB type
    db_type = 'sqlite' if DB_URI.startswith('sqlite') else 'postgresql'
    print(f"[INFO] Detected DB type: {db_type}")

    # Check for api_token column
    if db_type == 'sqlite':
        # SQLite pragma table_info returns a list of columns
        result = conn.execute(text("PRAGMA table_info(users)")).fetchall()
        columns = {row[1] for row in result}
        if 'api_token' not in columns:
            print("[MIGRATE] Adding 'api_token' column to users (SQLite)...")
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN api_token VARCHAR(256)"))
                print("[OK] 'api_token' column added.")
            except Exception as e:
                print(f"[WARN] Could not add 'api_token': {e}")
        else:
            print("[OK] 'api_token' column already exists.")
        if 'api_token_expiration' not in columns:
            print("[MIGRATE] Adding 'api_token_expiration' column to users (SQLite)...")
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN api_token_expiration TIMESTAMP"))
                print("[OK] 'api_token_expiration' column added.")
            except Exception as e:
                print(f"[WARN] Could not add 'api_token_expiration': {e}")
        else:
            print("[OK] 'api_token_expiration' column already exists.")
    else:
        # PostgreSQL: use information_schema
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'users' AND column_name IN ('api_token', 'api_token_expiration')
        """)).fetchall()
        columns = {row[0] for row in result}
        if 'api_token' not in columns:
            print("[MIGRATE] Adding 'api_token' column to users (PostgreSQL)...")
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS api_token VARCHAR(256);"))
                print("[OK] 'api_token' column added.")
            except Exception as e:
                print(f"[WARN] Could not add 'api_token': {e}")
        else:
            print("[OK] 'api_token' column already exists.")
        if 'api_token_expiration' not in columns:
            print("[MIGRATE] Adding 'api_token_expiration' column to users (PostgreSQL)...")
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS api_token_expiration TIMESTAMP;"))
                print("[OK] 'api_token_expiration' column added.")
            except Exception as e:
                print(f"[WARN] Could not add 'api_token_expiration': {e}")
        else:
            print("[OK] 'api_token_expiration' column already exists.")

print("[DONE] Migration check complete.")
