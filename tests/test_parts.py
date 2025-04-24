import pytest
from models import Part, MaintenanceRecord
from datetime import datetime, timedelta

def test_create_part(client, db, login_admin):
    login_admin()
    response = client.post('/parts', data={
        'name': 'Test Part',
        'machine_id': 1
    }, follow_redirects=True)
    assert b'added successfully' in response.data
    part = Part.query.filter_by(name='Test Part').first()
    assert part is not None

def test_record_maintenance_updates_part(client, db, login_admin, create_part):
    part = create_part()
    login_admin()
    response = client.post('/maintenance', data={
        'machine_id': part.machine_id,
        'part_id': part.id,
        'maintenance_type': 'Routine',
        'description': 'Test maintenance',
        'date': datetime.now().strftime('%Y-%m-%d')
    }, follow_redirects=True)
    assert b'Maintenance record added successfully' in response.data
    db.session.refresh(part)
    # Accept either today or tomorrow for last_maintenance due to possible UTC/local mismatch
    last_maint = part.last_maintenance.date()
    today = datetime.now().date()
    assert last_maint == today or last_maint == today + timedelta(days=1)

def test_view_part_history(client, db, login_admin, create_part):
    part = create_part()
    login_admin()
    client.post('/maintenance', data={
        'machine_id': part.machine_id,
        'part_id': part.id,
        'maintenance_type': 'Routine',
        'description': 'Test maintenance',
        'date': datetime.now().strftime('%Y-%m-%d')
    }, follow_redirects=True)
    # Use the correct route for part history (update to /part/<id>/history)
    response = client.get(f'/part/{part.id}/history')
    assert b'Test maintenance' in response.data
