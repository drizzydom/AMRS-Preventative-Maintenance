import pytest

def test_login_logout(client, db, login_admin):
    login_admin()
    response = client.get('/dashboard')
    assert b'Dashboard' in response.data
    # Check that the user is authenticated (session contains _user_id)
    with client.session_transaction() as sess:
        assert '_user_id' in sess
    client.get('/logout')
    response = client.get('/dashboard', follow_redirects=True)
    assert b'Login' in response.data
    # Check that the user is logged out (session does not contain _user_id)
    with client.session_transaction() as sess:
        assert '_user_id' not in sess

def test_protected_route_requires_login(client):
    response = client.get('/dashboard', follow_redirects=True)
    assert b'Login' in response.data
