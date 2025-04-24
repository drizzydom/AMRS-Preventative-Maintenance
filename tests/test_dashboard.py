import pytest

def test_dashboard_stats(client, db, login_admin, create_part):
    part = create_part()
    login_admin()
    response = client.get('/dashboard')
    assert b'Total Parts' in response.data
    # Add more assertions as dashboard logic is improved
