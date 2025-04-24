import pytest
from models import User

def test_create_user(client, db, login_admin):
    login_admin()
    response = client.post('/admin/users', data={
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password': 'testpassword',
        'role': 'user'
    }, follow_redirects=True)
    assert b'created successfully' in response.data
    user = User.query.filter_by(username='testuser').first()
    assert user is not None

def test_update_profile(client, db, login_admin):
    login_admin()
    client.post('/admin/users', data={
        'username': 'profileuser',
        'email': 'profileuser@example.com',
        'password': 'testpassword',
        'role': 'user'
    }, follow_redirects=True)
    client.post('/login', data={'username': 'profileuser', 'password': 'testpassword'}, follow_redirects=True)
    response = client.post('/profile', data={
        'email': 'newemail@example.com',
        'current_password': '',
        'new_password': '',
        'confirm_password': ''
    }, follow_redirects=True)
    assert b'updated successfully' in response.data
    user = User.query.filter_by(username='profileuser').first()
    assert user.email == 'newemail@example.com'
