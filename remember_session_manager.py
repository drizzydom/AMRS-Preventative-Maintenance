from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

from flask import current_app, g

from models import RememberSession, db

REMEMBER_SESSION_COOKIE = 'remember_session_id'
REMEMBER_TOKEN_COOKIE = 'remember_token'
REMEMBER_DEVICE_COOKIE = 'remember_device_id'


def _token_ttl() -> timedelta:
    days = int(current_app.config.get('REMEMBER_TOKEN_DAYS', 90))
    return timedelta(days=max(days, 1))


def _max_sessions_per_user() -> int:
    return max(int(current_app.config.get('REMEMBER_MAX_SESSIONS', 5)), 1)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def build_fingerprint(device_id: str, user_agent: str = '', ip_fragment: str = '') -> str:
    payload = f"{device_id or ''}|{user_agent or ''}|{ip_fragment or ''}"
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def create_or_update_session(
    user,
    device_id: str,
    *,
    user_agent: str = '',
    ip_address: str = '',
    fingerprint: Optional[str] = None,
) -> Tuple[RememberSession, str]:
    now = datetime.utcnow()
    session = RememberSession.query.filter_by(user_id=user.id, device_id=device_id).first()
    if not session:
        session = RememberSession(user_id=user.id, device_id=device_id)
        db.session.add(session)

    raw_token = secrets.token_urlsafe(48)
    session.token_hash = _hash_token(raw_token)
    session.device_fingerprint = fingerprint
    session.user_agent = (user_agent or '')[:500]
    session.ip_address = (ip_address or '')[:64]
    session.issued_at = now
    session.last_used_at = now
    session.expires_at = now + _token_ttl()
    session.revoked_at = None

    db.session.commit()
    _enforce_session_limit(user.id)
    return session, raw_token


def _enforce_session_limit(user_id: int) -> None:
    limit = _max_sessions_per_user()
    sessions = (
        RememberSession.query
        .filter_by(user_id=user_id)
        .order_by(RememberSession.last_used_at.desc())
        .all()
    )

    if len(sessions) <= limit:
        return

    for session in sessions[limit:]:
        if not session.revoked_at:
            session.revoke()
    db.session.commit()


def revoke_session_by_id(session_id: int) -> None:
    session = RememberSession.query.get(session_id)
    if not session:
        return
    session.revoke()
    db.session.commit()


def revoke_user_sessions(user_id: int, device_id: Optional[str] = None) -> None:
    query = RememberSession.query.filter_by(user_id=user_id)
    if device_id:
        query = query.filter_by(device_id=device_id)
    sessions = query.all()
    if not sessions:
        return
    for session in sessions:
        session.revoke()
    db.session.commit()


def validate_session(
    session_id: int,
    raw_token: str,
    *,
    device_id: Optional[str] = None,
    fingerprint: Optional[str] = None,
    user_agent: str = '',
) -> Optional[Tuple[RememberSession, str]]:
    session = RememberSession.query.get(session_id)
    if not session:
        return None

    if not session.is_active:
        session.revoke()
        db.session.commit()
        return None

    if device_id and session.device_id != device_id:
        session.revoke()
        db.session.commit()
        return None

    hashed = _hash_token(raw_token)
    if not hmac.compare_digest(hashed, session.token_hash or ''):
        session.revoke()
        db.session.commit()
        return None

    if fingerprint and session.device_fingerprint and session.device_fingerprint != fingerprint:
        session.revoke()
        db.session.commit()
        return None

    # Rotate token to prevent replay
    new_token = secrets.token_urlsafe(48)
    session.token_hash = _hash_token(new_token)
    session.device_fingerprint = fingerprint or session.device_fingerprint
    session.user_agent = (user_agent or '')[:500]
    session.mark_used()
    session.expires_at = datetime.utcnow() + _token_ttl()

    db.session.commit()
    return session, new_token


def session_cookie_max_age() -> int:
    return int(_token_ttl().total_seconds())


def queue_cookie_refresh(session_id: int, token: str, device_id: str, *, clear_legacy: bool = True) -> None:
    g.remember_cookie_payload = {
        'session_id': str(session_id),
        'token': token,
        'device_id': device_id,
        'clear': False,
        'clear_legacy': clear_legacy,
    }


def queue_cookie_clear() -> None:
    g.remember_cookie_payload = {'clear': True, 'clear_legacy': True}


def apply_cookie_payload(response):
    payload = getattr(g, 'remember_cookie_payload', None)
    if not payload:
        return response

    if payload.get('clear'):
        response.delete_cookie(REMEMBER_SESSION_COOKIE)
        response.delete_cookie(REMEMBER_TOKEN_COOKIE)
        response.delete_cookie(REMEMBER_DEVICE_COOKIE)
        response.delete_cookie('remember_token')
        return response

    max_age = session_cookie_max_age()
    same_site = current_app.config.get('REMEMBER_COOKIE_SAMESITE', 'Lax')
    secure_flag = current_app.config.get('REMEMBER_COOKIE_SECURE', False)

    response.set_cookie(
        REMEMBER_SESSION_COOKIE,
        payload['session_id'],
        max_age=max_age,
        httponly=True,
        samesite=same_site,
        secure=secure_flag,
    )
    response.set_cookie(
        REMEMBER_TOKEN_COOKIE,
        payload['token'],
        max_age=max_age,
        httponly=True,
        samesite=same_site,
        secure=secure_flag,
    )
    response.set_cookie(
        REMEMBER_DEVICE_COOKIE,
        payload['device_id'],
        max_age=max_age,
        httponly=False,
        samesite=same_site,
        secure=secure_flag,
    )
    if payload.get('clear_legacy'):
        response.delete_cookie('remember_token')
    return response


def sanitize_device_id(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    trimmed = value.strip()
    if not trimmed:
        return None
    return trimmed[:64]