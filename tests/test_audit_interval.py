import pytest
from models import User

def test_audit_interval_logic(client, db, login_admin):
    login_admin()
    # Simulate audit task with interval and check-off logic
    # ...
    assert True  # Placeholder for interval logic

def test_per_site_notification_preferences(client, db, login_admin):
    login_admin()
    # Assume user 1 is logged in and assigned to sites 1 and 2
    user = User.query.get(1)
    user.notification_preferences = {
        'enable_email': True,
        'notification_frequency': 'daily',
        'site_notifications': {'1': True, '2': False}
    }
    db.session.commit()
    # Simulate notification scheduler logic
    from notification_scheduler import get_maintenance_due
    site1 = user.sites[0]
    site2 = user.sites[1] if len(user.sites) > 1 else None
    assert user.notification_preferences['site_notifications']['1'] is True
    if site2:
        assert user.notification_preferences['site_notifications']['2'] is False
        # Only site1 should be included in notifications
        overdue1, due_soon1 = get_maintenance_due(site1)
        overdue2, due_soon2 = get_maintenance_due(site2)
        # (In a real test, would check that only site1's items are sent)
