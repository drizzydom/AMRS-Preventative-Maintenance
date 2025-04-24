import pytest

def test_api_sync_status(client):
    response = client.get('/api/sync/status')
    assert response.status_code == 200
    assert b'online' in response.data
    # Check the JSON structure and content
    data = response.get_json()
    assert data['status'] == 'online'
    assert 'server_time' in data
    assert 'version' in data
