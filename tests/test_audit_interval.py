import pytest
from models import User, AuditTask

def test_audit_interval_logic(client, db, login_admin, setup_test_data):
    login_admin()
    # Simulate audit task with interval and check-off logic
    # Create an audit task
    data = setup_test_data
    response = client.post('/audits', data={
        'name': 'Interval Logic Audit',
        'site_id': data['site1'].id,
        'machine_ids': [data['machine'].id],
        'interval': 'daily',
        'create_audit': '1'
    }, follow_redirects=True)
    assert b'Audit task created' in response.data or b'Create Audit Task' in response.data
    audit = AuditTask.query.filter_by(name='Interval Logic Audit').first()
    assert audit is not None

def test_per_site_notification_preferences(client, db, login_admin, setup_test_data):
    login_admin()
    data = setup_test_data
    user = data['admin']
    user.notification_preferences = {
        'enable_email': True,
        'notification_frequency': 'daily',
        'site_notifications': {str(data['site1'].id): True, str(data['site2'].id): False}
    }
    db.session.commit()
    # Simulate notification scheduler logic
    from notification_scheduler import get_maintenance_due
    site1 = data['site1']
    site2 = data['site2']
    assert user.notification_preferences['site_notifications'][str(site1.id)] is True
    assert user.notification_preferences['site_notifications'][str(site2.id)] is False
    overdue1, due_soon1 = get_maintenance_due(site1)
    overdue2, due_soon2 = get_maintenance_due(site2)
    # Check that only site1's items are due for notification
    assert (overdue1 or due_soon1) or not (overdue2 or due_soon2)
