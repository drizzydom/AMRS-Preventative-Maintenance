import pytest
from models import AuditTask
from datetime import datetime, timedelta

def test_create_audit_task(client, db, login_admin):
    login_admin()
    response = client.post('/audits', data={
        'name': 'Test Audit',
        'site_id': 1,
        'machine_ids': [1],
        'interval': 'daily'
    }, follow_redirects=True)
    assert b'Create Audit Task' in response.data or b'Audit task created' in response.data
    audit = AuditTask.query.filter_by(name='Test Audit').first()
    assert audit is not None

def test_create_audit_task_with_custom_interval(client, db, login_admin):
    login_admin()
    response = client.post('/audits', data={
        'name': 'Custom Interval Audit',
        'site_id': 1,
        'machine_ids': [1],
        'interval': 'custom',
        'custom_interval_days': 5
    }, follow_redirects=True)
    assert b'Create Audit Task' in response.data or b'Audit task created' in response.data
    audit = AuditTask.query.filter_by(name='Custom Interval Audit').first()
    assert audit is not None
    assert audit.interval == 'custom'
    assert audit.custom_interval_days == 5

def test_audit_checkoff_logic(client, db, login_admin):
    # This would simulate the logic for check-off intervals and reminders
    pass  # To be implemented with interval and reminder logic

def test_audit_checkoff_eligibility_custom_interval(client, db, login_admin):
    login_admin()
    # Create a custom interval audit task
    client.post('/audits', data={
        'name': 'Interval Checkoff',
        'site_id': 1,
        'machine_ids': [1],
        'interval': 'custom',
        'custom_interval_days': 3
    }, follow_redirects=True)
    audit = AuditTask.query.filter_by(name='Interval Checkoff').first()
    # Simulate a completion 2 days ago (should not be eligible)
    from models import AuditTaskCompletion
    completion = AuditTaskCompletion(
        audit_task_id=audit.id,
        machine_id=1,
        date=datetime.utcnow().date() - timedelta(days=2),
        completed=True,
        completed_by=1,
        completed_at=datetime.utcnow() - timedelta(days=2)
    )
    db.session.add(completion)
    db.session.commit()
    # Try to check off again today (should not be eligible)
    response = client.post('/audits', data={'checkoff': '1', f'complete_{audit.id}_1': 'on'}, follow_redirects=True)
    assert b'No eligible audit tasks' in response.data or b'checked off successfully' not in response.data
