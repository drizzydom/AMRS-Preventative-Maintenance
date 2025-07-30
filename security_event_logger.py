from models import db, SecurityEvent
from flask import request, has_request_context
from flask_login import current_user
from datetime import datetime
import requests

# Utility to get general location from IP (using ipinfo.io, can be replaced)
def get_location_from_ip(ip):
    try:
        if not ip or ip.startswith('127.') or ip.startswith('192.168.') or ip == '::1':
            return 'Local'
        resp = requests.get(f'https://ipinfo.io/{ip}/json', timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            return f"{data.get('city', '')}, {data.get('region', '')}, {data.get('country', '')}".strip(', ')
    except Exception:
        pass
    return 'Unknown'

def log_security_event(event_type, details=None, is_critical=False):
    user_id = None
    username = None
    ip_address = None
    location = None
    if has_request_context():
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        location = get_location_from_ip(ip_address)
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            user_id = current_user.id
            username = getattr(current_user, 'username', None)
    event = SecurityEvent(
        event_type=event_type,
        user_id=user_id,
        username=username,
        ip_address=ip_address,
        location=location,
        details=details,
        is_critical=is_critical,
        timestamp=datetime.utcnow()
    )
    db.session.add(event)
    db.session.commit()
    print(f"[SECURITY LOG] {event_type} | User: {username or user_id} | IP: {ip_address} | {details}")
