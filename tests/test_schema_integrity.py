import pytest
from app import app, db
from sqlalchemy import inspect

def test_all_tables_and_columns_exist():
    expected_schema = {
        'users': {'id', 'username', 'email', 'password_hash', 'role_id', 'last_login', 'reset_token', 'reset_token_expiration', 'created_at', 'updated_at', 'full_name'},
        'roles': {'id', 'name', 'description', 'permissions', 'created_at', 'updated_at'},
        'sites': {'id', 'name', 'location', 'contact_email', 'notification_threshold', 'enable_notifications', 'created_at', 'updated_at'},
        'machines': {'id', 'name', 'model', 'machine_number', 'serial_number', 'site_id', 'created_at', 'updated_at'},
        'parts': {'id', 'name', 'description', 'machine_id', 'created_at', 'updated_at'},
        'maintenance_records': {'id', 'machine_id', 'part_id', 'user_id', 'maintenance_type', 'description', 'date', 'performed_by', 'status', 'notes', 'client_id', 'created_at', 'updated_at'},
        'audit_tasks': {'id', 'name', 'description', 'site_id', 'created_by', 'interval', 'custom_interval_days', 'created_at', 'updated_at'},
        'audit_task_completions': {'id', 'audit_task_id', 'machine_id', 'date', 'completed', 'completed_by', 'completed_at', 'created_at', 'updated_at'},
    }
    with app.app_context():
        inspector = inspect(db.engine)
        for table, expected_columns in expected_schema.items():
            assert inspector.has_table(table), f"Missing table: {table}"
            columns = {col['name'] for col in inspector.get_columns(table)}
            missing = expected_columns - columns
            assert not missing, f"Missing columns in {table}: {missing}"