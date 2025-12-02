from datetime import datetime, timedelta

from models import db, MaintenanceRecord, Part, User


def _login(client, username, password):
    response = client.post('/api/v1/auth/login', json={'username': username, 'password': password})
    assert response.status_code == 200, response.json
    return response


def test_part_detail_includes_history(app, client):
    _login(client, 'admin', 'password')

    with app.app_context():
        part = Part.query.filter_by(name='Filter').first()
        assert part is not None
        part_id = part.id
        machine_id = part.machine_id
        user = User.query.filter_by(is_admin=True).first()
        assert user is not None
        existing = MaintenanceRecord.query.filter_by(part_id=part.id).count()
        for i in range(3):
            record = MaintenanceRecord(
                part_id=part_id,
                machine_id=machine_id,
                user_id=user.id,
                date=datetime.utcnow() - timedelta(days=i),
                maintenance_type=f'Type {i}',
                description=f'Record {i}',
                status='completed',
            )
            db.session.add(record)
        db.session.commit()
        total_expected = existing + 3

    response = client.get(f'/api/v1/maintenance/part/{part_id}?history_limit=2')
    assert response.status_code == 200
    payload = response.get_json()['data']
    history = payload['history']
    assert len(history) == 2
    assert payload['history_total'] == total_expected
    dates = [entry['date'] for entry in history]
    assert dates == sorted(dates, reverse=True)
    assert all(entry['maintenance_type'].startswith('Type') for entry in history)


def test_maintenance_history_api_supports_pagination_and_filters(app, client):
    _login(client, 'admin', 'password')

    with app.app_context():
        part_a = Part.query.filter_by(name='Filter').first()
        part_b = Part.query.filter_by(name='Valve').first()
        assert part_a and part_b
        user = User.query.filter_by(is_admin=True).first()
        assert user is not None

        # Create 20 maintenance records split across parts
        for i in range(15):
            record = MaintenanceRecord(
                part_id=part_a.id,
                machine_id=part_a.machine_id,
                user_id=user.id,
                date=datetime.utcnow() - timedelta(days=i),
                maintenance_type='Scheduled',
                description=f'Filter maintenance {i}',
                performed_by='Tech Alpha',
                status='completed',
            )
            db.session.add(record)

        for i in range(5):
            record = MaintenanceRecord(
                part_id=part_b.id,
                machine_id=part_b.machine_id,
                user_id=user.id,
                date=datetime.utcnow() - timedelta(days=30 + i),
                maintenance_type='Emergency',
                description=f'Valve maintenance {i}',
                performed_by='Tech Beta',
                status='completed',
            )
            db.session.add(record)

        db.session.commit()
        total_records = MaintenanceRecord.query.count()

    # Page through the results
    resp = client.get('/api/v1/maintenance/history?page=1&page_size=7')
    assert resp.status_code == 200
    payload = resp.get_json()['data']
    assert payload['pagination']['page'] == 1
    assert payload['pagination']['page_size'] == 7
    assert payload['pagination']['total_records'] == total_records
    assert len(payload['records']) == 7

    resp_page3 = client.get('/api/v1/maintenance/history?page=3&page_size=7')
    assert resp_page3.status_code == 200
    payload_page3 = resp_page3.get_json()['data']
    assert payload_page3['pagination']['page'] == 3
    assert len(payload_page3['records']) == max(0, total_records - 14)

    # Filter by machine
    machine_id = payload['records'][0]['machine_id']
    resp_machine = client.get(f'/api/v1/maintenance/history?machine_id={machine_id}&page_size=50')
    assert resp_machine.status_code == 200
    machine_payload = resp_machine.get_json()['data']
    assert all(record['machine_id'] == machine_id for record in machine_payload['records'])

    # Search filter should return only matching part names/descriptions
    resp_search = client.get('/api/v1/maintenance/history?search=valve&page_size=50')
    assert resp_search.status_code == 200
    search_payload = resp_search.get_json()['data']
    assert search_payload['records'], 'Expected at least one search result'
    assert all('valve' in (rec['part'].lower() + rec['notes'].lower()) for rec in search_payload['records'])
