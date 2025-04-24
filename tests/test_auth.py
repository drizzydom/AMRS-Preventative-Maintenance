import pytest

def test_login_logout(client, db, login_admin):
    login_admin()
    response = client.get('/dashboard')
    assert b'Dashboard' in response.data
    client.get('/logout')
    response = client.get('/dashboard', follow_redirects=True)
    assert b'Login' in response.data

def test_protected_route_requires_login(client):
    response = client.get('/dashboard', follow_redirects=True)
    assert b'Login' in response.data
