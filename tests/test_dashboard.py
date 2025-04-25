import pytest
from models import Part

def test_dashboard_stats(client, db, login_admin, create_part):
    part = create_part()
    login_admin()
    response = client.get('/dashboard')
    assert b'Total Parts' in response.data
    # Check that the part count in the database matches the dashboard
    part_count = Part.query.count()
    assert str(part_count).encode() in response.data
    # Check for overdue, due soon, and ok counts in the dashboard
    assert b'Overdue' in response.data
    assert b'Due Soon' in response.data
    assert b'OK' in response.data
