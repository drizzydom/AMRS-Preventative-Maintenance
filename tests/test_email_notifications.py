import pytest
from models import AuditTask, AuditTaskCompletion, User
from datetime import datetime, timedelta

def test_audit_reminder_email_logic(monkeypatch, client, db, login_admin):
    login_admin()
    sent = {}
    def fake_send_email(*args, **kwargs):
        sent['called'] = True
    monkeypatch.setattr('app.mail.send', fake_send_email)
    # Create audit task and incomplete completion
    client.post('/audits', data={
        'name': 'Reminder Audit',
        'site_id': 1,
        'machine_ids': [1],
        'interval': 'daily'
    }, follow_redirects=True)
    audit = AuditTask.query.filter_by(name='Reminder Audit').first()
    # No completion for today, should trigger reminder
    from notification_scheduler import send_audit_reminders
    send_audit_reminders()
    assert sent.get('called')

def test_audit_reminder_respects_site_preferences(monkeypatch, client, db, login_admin):
    login_admin()
    sent = {'count': 0}
    def fake_send_email(*args, **kwargs):
        sent['count'] += 1
    monkeypatch.setattr('app.mail.send', fake_send_email)
    # Set user notification preferences to disable site 1
    user = User.query.get(1)
    user.notification_preferences = {
        'enable_email': True,
        'notification_frequency': 'daily',
        'audit_reminders': True,
        'site_notifications': {'1': False}
    }
    db.session.commit()
    # Create audit task for site 1
    client.post('/audits', data={
        'name': 'No Reminder Audit',
        'site_id': 1,
        'machine_ids': [1],
        'interval': 'daily'
    }, follow_redirects=True)
    from notification_scheduler import send_audit_reminders
    send_audit_reminders()
    assert sent['count'] == 0
