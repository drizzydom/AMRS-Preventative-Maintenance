
def _login(client, username, password):
    response = client.post('/api/v1/auth/login', json={'username': username, 'password': password})
    assert response.status_code == 200, response.json
    return response


def test_machines_scope_limited_user(client):
    _login(client, 'limited', 'password')

    response = client.get('/api/v1/machines')
    assert response.status_code == 200
    payload = response.get_json()['data']
    assert len(payload) == 1
    assert payload[0]['site_name'] == 'Alpha Plant'


def test_sites_requires_permission(client):
    _login(client, 'limited', 'password')
    forbidden = client.get('/api/v1/sites')
    assert forbidden.status_code == 403

    client.post('/api/v1/auth/logout')

    _login(client, 'manager', 'password')
    allowed = client.get('/api/v1/sites')
    assert allowed.status_code == 200
    sites = allowed.get_json()['data']
    assert {site['name'] for site in sites} == {'Alpha Plant'}


def test_audits_permission_and_site_scope(client):
    _login(client, 'basic', 'password')
    no_perm = client.get('/api/v1/audits')
    assert no_perm.status_code == 403

    client.post('/api/v1/auth/logout')

    _login(client, 'limited', 'password')
    scoped = client.get('/api/v1/audits')
    assert scoped.status_code == 200
    audits = scoped.get_json()['data']
    assert len(audits) == 1
    assert audits[0]['site_id'] == 1