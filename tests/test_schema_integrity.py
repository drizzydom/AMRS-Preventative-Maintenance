import pytest
from sqlalchemy import inspect
from app import db

def test_audit_tasks_columns_exist(app):
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('audit_tasks')]
    assert 'interval' in columns, "Missing 'interval' column in audit_tasks table"
    assert 'custom_interval_days' in columns, "Missing 'custom_interval_days' column in audit_tasks table"

def test_audit_task_completions_columns_exist(app):
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('audit_task_completions')]
    assert 'created_at' in columns, "Missing 'created_at' column in audit_task_completions table"
    assert 'updated_at' in columns, "Missing 'updated_at' column in audit_task_completions table"

def test_manage_roles_template_context(client, login_admin):
    login_admin()
    response = client.get('/manage/roles')
    assert response.status_code == 200
    assert b'all_permissions' not in response.data  # Should not error or be missing context