import pytest

def test_api_sync_status(client):
    response = client.get('/api/sync/status')
    assert response.status_code == 200
    assert b'online' in response.data
