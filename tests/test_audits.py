import pytest
from models import AuditTask
from datetime import datetime, timedelta

def test_create_audit_task(client, db, login_admin, setup_test_data):
    login_admin()
    data = setup_test_data
    response = client.post('/audits', data={
        'name': 'Test Audit',
        'site_id': data['site1'].id,
        'machine_ids': [data['machine'].id],
        'interval': 'daily',
        'create_audit': '1'
    }, follow_redirects=True)
    assert b'Create Audit Task' in response.data or b'Audit task created' in response.data
    audit = AuditTask.query.filter_by(name='Test Audit').first()
    assert audit is not None

def test_create_audit_task_with_custom_interval_days(client, db, login_admin, setup_test_data):
    login_admin()
    data = setup_test_data
    response = client.post('/audits', data={
        'name': 'Custom Interval Audit Days',
        'site_id': data['site1'].id,
        'machine_ids': [data['machine'].id],
        'interval': 'custom',
        'custom_interval_value': 5,
        'custom_interval_unit': 'day',
        'create_audit': '1'
    }, follow_redirects=True)
    audit = AuditTask.query.filter_by(name='Custom Interval Audit Days').first()
    assert audit is not None
    assert audit.interval == 'custom'
    assert audit.custom_interval_days == 5

def test_create_audit_task_with_custom_interval_weeks(client, db, login_admin, setup_test_data):
    login_admin()
    data = setup_test_data
    response = client.post('/audits', data={
        'name': 'Custom Interval Audit Weeks',
        'site_id': data['site1'].id,
        'machine_ids': [data['machine'].id],
        'interval': 'custom',
        'custom_interval_value': 2,
        'custom_interval_unit': 'week',
        'create_audit': '1'
    }, follow_redirects=True)
    audit = AuditTask.query.filter_by(name='Custom Interval Audit Weeks').first()
    assert audit is not None
    assert audit.interval == 'custom'
    assert audit.custom_interval_days == 14

def test_create_audit_task_with_custom_interval_months(client, db, login_admin, setup_test_data):
    login_admin()
    data = setup_test_data
    response = client.post('/audits', data={
        'name': 'Custom Interval Audit Months',
        'site_id': data['site1'].id,
        'machine_ids': [data['machine'].id],
        'interval': 'custom',
        'custom_interval_value': 1,
        'custom_interval_unit': 'month',
        'create_audit': '1'
    }, follow_redirects=True)
    audit = AuditTask.query.filter_by(name='Custom Interval Audit Months').first()
    assert audit is not None
    assert audit.interval == 'custom'
    assert audit.custom_interval_days == 30

def test_audit_checkoff_logic(client, db, login_admin, setup_test_data):
    # This would simulate the logic for check-off intervals and reminders
    pass  # To be implemented with interval and reminder logic

def test_audit_checkoff_eligibility_custom_interval(client, db, login_admin, setup_test_data):
    login_admin()
    data = setup_test_data
    # Create a custom interval audit task
    client.post('/audits', data={
        'name': 'Interval Checkoff',
        'site_id': data['site1'].id,
        'machine_ids': [data['machine'].id],
        'interval': 'custom',
        'custom_interval_days': 3,
        'create_audit': '1'
    }, follow_redirects=True)
    audit = AuditTask.query.filter_by(name='Interval Checkoff').first()
    # Simulate a completion 2 days ago (should not be eligible)
    from models import AuditTaskCompletion
    completion = AuditTaskCompletion(
        audit_task_id=audit.id,
        machine_id=data['machine'].id,
        date=datetime.utcnow().date() - timedelta(days=2),
        completed=True,
        completed_by=data['admin'].id,
        completed_at=datetime.utcnow() - timedelta(days=2)
    )
    db.session.add(completion)
    db.session.commit()
    # Try to check off again today (should not be eligible)
    response = client.post('/audits', data={'checkoff': '1', f'complete_{audit.id}_{data["machine"].id}': 'on'}, follow_redirects=False)
    assert response.status_code in (302, 303)
    redirected_response = client.get('/audits')
    # Check for the message in the HTML response (raw bytes)
    found_in_html = b'No eligible audit tasks were checked off' in redirected_response.data
    # Use BeautifulSoup to search for the message in alert divs
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(redirected_response.data, 'html.parser')
    found_in_alert = False
    for alert in soup.find_all(class_='alert'):
        if 'No eligible audit tasks were checked off' in alert.get_text():
            found_in_alert = True
            break
    # Debug output if not found
    if not (found_in_html or found_in_alert):
        print('---DEBUG: audits.html response---')
        print(redirected_response.data.decode(errors='replace'))
        print('---END DEBUG---')
    # Check for the message in the session's flashed messages (should be consumed, but check anyway)
    with client.session_transaction() as sess:
        flashed = False
        flashes = sess.get('_flashes', [])
        for category, message in flashes:
            if 'No eligible audit tasks were checked off' in message:
                flashed = True
                break
    assert found_in_html or found_in_alert or flashed
