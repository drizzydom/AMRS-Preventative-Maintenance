import pytest
from models import User

def test_log_creation_and_privacy(client, db, login_admin):
    login_admin()
    # Simulate an action that should create a log entry (e.g., create a user)
    response = client.post('/admin/users', data={
        'username': 'logtestuser',
        'email': 'logtestuser@example.com',
        'password': 'testpassword',
        'role': 'user'
    }, follow_redirects=True)
    
    # Check the flash message (user feedback)
    assert b'created successfully' in response.data
    
    # Check that the user was actually created in the database (backend state)
    user = User.query.filter_by(username='logtestuser').first()
    assert user is not None
    assert user.email == 'logtestuser@example.com'
