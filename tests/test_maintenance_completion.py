from datetime import datetime, timedelta

from models import db, Part


def _login(client, username, password):
    response = client.post('/api/v1/auth/login', json={'username': username, 'password': password})
    assert response.status_code == 200, response.json
    return response


def test_complete_multiple_advances_schedule(app, client):
    _login(client, 'admin', 'password')

    with app.app_context():
        part = Part.query.filter_by(name='Filter').first()
        assert part is not None
        part.maintenance_frequency = 30
        part.maintenance_unit = 'day'
        part.last_maintenance = datetime.utcnow() - timedelta(days=120)
        part.next_maintenance = part.last_maintenance - timedelta(days=30)
        db.session.commit()
        machine_id = part.machine_id
        part_id = part.id

    completion_date = datetime.utcnow().date()
    response = client.post(
        '/api/v1/maintenance/complete-multiple',
        json={
            'machine_id': machine_id,
            'part_ids': [part_id],
            'date': completion_date.isoformat(),
            'type': 'Scheduled',
            'description': 'Cycle clean',
            'notes': '',
            'po_number': 'TEST-PO-123',
            'work_order_number': 'WO-2025-0001',
        },
    )
    assert response.status_code == 200, response.get_json()

    with app.app_context():
        part = db.session.get(Part, part_id)
        assert part is not None
        assert part.last_maintenance.date() == completion_date
        assert part.next_maintenance.date() == completion_date + timedelta(days=30)

    maintenance_response = client.get('/api/v1/maintenance')
    assert maintenance_response.status_code == 200
    payload = maintenance_response.get_json()['data']
    record = next(task for task in payload if task['id'] == part_id)
    assert record['status'] != 'overdue'
