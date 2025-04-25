import pytest

def test_ui_updates_after_action(client, db, login_admin, create_part):
    part = create_part()
    login_admin()
    # Record maintenance
    response = client.post('/maintenance', data={
        'machine_id': part.machine_id,
        'part_id': part.id,
        'maintenance_type': 'Routine',
        'description': 'UI test maintenance',
        'date': '2025-04-23'
    }, follow_redirects=True)
    assert b'Maintenance record added successfully' in response.data
    # Check that the maintenance record appears in the part history UI
    response = client.get(f'/part/{part.id}/history')
    assert b'UI test maintenance' in response.data
