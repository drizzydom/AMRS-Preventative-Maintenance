import pytest
from app import ensure_db_schema

def test_auto_migration_adds_columns(app, db):
    from sqlalchemy import inspect
    ensure_db_schema()
    inspector = inspect(db.engine)
    # Example: Check that 'created_at' column exists in 'users' table
    columns = [col['name'] for col in inspector.get_columns('users')]
    assert 'created_at' in columns
