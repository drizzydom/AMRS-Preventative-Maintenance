from datetime import datetime, timedelta

from models import RememberSession, User, hash_value
from remember_session_manager import (
    REMEMBER_DEVICE_COOKIE,
    REMEMBER_SESSION_COOKIE,
    REMEMBER_TOKEN_COOKIE,
    create_or_update_session,
    validate_session,
)


def _login(client, *, device_id: str, remember: bool = True, password: str = 'password'):
    return client.post(
        '/api/v1/auth/login',
        json={
            'username': 'admin',
            'password': password,
            'remember_me': remember,
            'device_id': device_id,
        },
    )


def _get_user(app, username: str = 'admin') -> User:
    with app.app_context():
        return User.query.filter_by(username_hash=hash_value(username)).first()


def test_remember_login_creates_device_session(app, client):
    device_id = 'device-alpha'
    response = _login(client, device_id=device_id)
    assert response.status_code == 200

    cookies = response.headers.getlist('Set-Cookie')
    assert any(REMEMBER_SESSION_COOKIE in cookie for cookie in cookies)
    assert any(REMEMBER_TOKEN_COOKIE in cookie for cookie in cookies)
    assert any(REMEMBER_DEVICE_COOKIE in cookie for cookie in cookies)

    with app.app_context():
        user = _get_user(app)
        session = RememberSession.query.filter_by(user_id=user.id, device_id=device_id).first()
        assert session is not None
        assert session.is_active
        assert len(session.token_hash) == 64
        assert session.expires_at - datetime.utcnow() > timedelta(days=80)


def test_session_limit_enforced(app, client):
    app.config['REMEMBER_MAX_SESSIONS'] = 2
    device_ids = ['device-one', 'device-two', 'device-three']

    for device_id in device_ids:
        response = _login(client, device_id=device_id)
        assert response.status_code == 200

    with app.app_context():
        user = _get_user(app)
        sessions = RememberSession.query.filter_by(user_id=user.id).all()
        assert len(sessions) == 3

        status_by_device = {session.device_id: session.revoked_at is None for session in sessions}
        assert status_by_device['device-one'] is False
        assert status_by_device['device-two'] is True
        assert status_by_device['device-three'] is True


def test_validate_session_rotates_token(app):
    with app.app_context():
        user = _get_user(app)
        session, token = create_or_update_session(
            user,
            'device-rotate',
            user_agent='pytest',
            ip_address='127.0.0.1',
            fingerprint='test-fingerprint',
        )
        original_hash = session.token_hash
        original_last_used = session.last_used_at

        validation_result = validate_session(
            session.id,
            token,
            device_id='device-rotate',
            fingerprint='test-fingerprint',
            user_agent='pytest',
        )

        assert validation_result is not None
        updated_session, rotated_token = validation_result
        assert rotated_token != token
        assert updated_session.token_hash != original_hash
        assert updated_session.last_used_at >= original_last_used
        assert updated_session.expires_at > datetime.utcnow()


def test_login_success_includes_feedback_meta(client):
    response = _login(client, device_id='feedback-success', remember=True)
    payload = response.get_json()

    assert response.status_code == 200
    assert payload['meta']['login_feedback']['final_status'] == 'session_ready'
    context = payload['meta']['login_feedback'].get('context', {})
    assert 'device_hint' in context

    step_keys = {step['key'] for step in payload['meta']['login_feedback']['steps']}
    assert {'credentials', 'session', 'trust_device', 'workspace'}.issubset(step_keys)


def test_login_invalid_credentials_feedback(client):
    response = _login(client, device_id='feedback-failure', remember=True, password='wrong-password')
    payload = response.get_json()

    assert response.status_code == 401
    assert payload['message'] == 'Invalid username or password'
    assert payload['meta']['login_feedback']['final_status'] == 'invalid_credentials'
    first_step = payload['meta']['login_feedback']['steps'][0]
    assert first_step['status'] == 'error'
