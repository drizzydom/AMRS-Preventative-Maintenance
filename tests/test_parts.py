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
    response = client.post(f'/parts/{part.id}/update_maintenance', data={
        'comments': 'Test maintenance',
        'description': 'Test maintenance description'
    }, follow_redirects=True)
    assert b'Maintenance for' in response.data or b'updated successfully' in response.data
    db.session.refresh(part)
    # Accept either today or tomorrow for last_maintenance due to possible UTC/local mismatch
    last_maint = part.last_maintenance.date()
    today = datetime.now().date()
    assert last_maint == today or last_maint == today + timedelta(days=1)
    # Check that a MaintenanceRecord was created
    record = MaintenanceRecord.query.filter_by(part_id=part.id).order_by(MaintenanceRecord.date.desc()).first()
    assert record is not None
    assert record.comments == 'Test maintenance'

def test_view_part_history(client, db, login_admin, create_part):
    part = create_part()
    login_admin()
    client.post(f'/parts/{part.id}/update_maintenance', data={
        'comments': 'Test maintenance',
        'description': 'Test maintenance description'
    }, follow_redirects=True)
    response = client.get(f'/part/{part.id}/history')
    assert b'Test maintenance' in response.data
    assert b'Test maintenance description' in response.data
