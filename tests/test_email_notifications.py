import pytest
from models import AuditTask, AuditTaskCompletion, User
from datetime import datetime, timedelta

def test_audit_reminder_email_logic(monkeypatch, client, db, login_admin, setup_test_data):
    login_admin()
    data = setup_test_data
    sent = {}
    def fake_send_email(*args, **kwargs):
        sent['called'] = True
    monkeypatch.setattr('app.mail.send', fake_send_email)
    client.post('/audits', data={
        'name': 'Reminder Audit',
        'site_id': data['site1'].id,
        'machine_ids': [data['machine'].id],
        'interval': 'daily',
        'create_audit': '1'
    }, follow_redirects=True)
    audit = AuditTask.query.filter_by(name='Reminder Audit').first()
    from notification_scheduler import send_audit_reminders
    send_audit_reminders()
    assert sent.get('called')

def test_audit_reminder_respects_site_preferences(monkeypatch, client, db, login_admin, setup_test_data):
    login_admin()
    data = setup_test_data
    sent = {'count': 0}
    def fake_send_email(*args, **kwargs):
        sent['count'] += 1
    monkeypatch.setattr('app.mail.send', fake_send_email)
    user = data['admin']
    user.notification_preferences = {
        'enable_email': True,
        'notification_frequency': 'daily',
        'audit_reminders': True,
        'site_notifications': {str(data['site1'].id): False}
    }
    db.session.commit()
    client.post('/audits', data={
        'name': 'No Reminder Audit',
        'site_id': data['site1'].id,
        'machine_ids': [data['machine'].id],
        'interval': 'daily',
        'create_audit': '1'
    }, follow_redirects=True)
    from notification_scheduler import send_audit_reminders
    send_audit_reminders()
    assert sent['count'] == 0
