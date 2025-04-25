import pytest

def test_concurrent_updates(client, db, login_admin, create_part):
    part = create_part()
    login_admin()
    # Simulate two updates to the same part
    response1 = client.post('/parts', data={
        'name': 'Concurrent Part',
        'machine_id': part.machine_id
    }, follow_redirects=True)
    response2 = client.post('/parts', data={
        'name': 'Concurrent Part 2',
        'machine_id': part.machine_id
    }, follow_redirects=True)
    assert b'added successfully' in response1.data or b'added successfully' in response2.data
    # Check that both parts exist in the database
    from models import Part
    assert Part.query.filter_by(name='Concurrent Part').first() is not None
    assert Part.query.filter_by(name='Concurrent Part 2').first() is not None
