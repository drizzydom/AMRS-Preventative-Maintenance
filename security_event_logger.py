from models import db, SecurityEvent, OfflineSecurityEvent
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
    # Check if logging is enabled (default: enabled)
    try:
        from models import AppSetting
        enabled = AppSetting.get('security_event_logging_enabled', '1') == '1'
    except Exception:
        enabled = True
    if not enabled:
        return
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
    # Try to log online, else fallback to offline queue
    if is_online():
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
    else:
        offline_event = OfflineSecurityEvent(
            event_type=event_type,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            location=location,
            details=details,
            is_critical=is_critical,
            timestamp=datetime.utcnow(),
            synced=False
        )
        db.session.add(offline_event)
        db.session.commit()
        print(f"[OFFLINE SECURITY LOG] {event_type} | User: {username or user_id} | IP: {ip_address} | {details}")


def is_online():
    """Check if the app can reach the online server (returns True if online, False if offline)."""
    import os
    import requests
    online_url = os.environ.get('AMRS_ONLINE_URL')
    if not online_url:
        return False
    try:
        resp = requests.get(online_url.strip("'\"").rstrip('/') + '/api/sync/status', timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def sync_offline_security_events():
    """
    Upload unsynced offline security events to the server and mark them as synced if successful.
    Should be called on app launch or when connectivity is restored.
    """
    import os
    import requests
    from sqlalchemy.orm import load_only
    online_url = os.environ.get('AMRS_ONLINE_URL')
    admin_username = os.environ.get('AMRS_ADMIN_USERNAME')
    admin_password = os.environ.get('AMRS_ADMIN_PASSWORD')
    if not online_url or not admin_username or not admin_password:
        print("[OFFLINE SECURITY SYNC] Missing online credentials; cannot sync offline events.")
        return False
    unsynced_events = OfflineSecurityEvent.query.filter_by(synced=False).all()
    if not unsynced_events:
        print("[OFFLINE SECURITY SYNC] No offline security events to sync.")
        return True
    # Prepare payload
    payload = [
        {
            'event_type': e.event_type,
            'user_id': e.user_id,
            'username': e.username,
            'ip_address': e.ip_address,
            'location': e.location,
            'details': e.details,
            'is_critical': e.is_critical,
            'timestamp': e.timestamp.isoformat() if e.timestamp else None,
            'client_event_id': e.id
        }
        for e in unsynced_events
    ]
    clean_url = online_url.strip("'\"").rstrip('/')
    if clean_url.endswith('/api'):
        clean_url = clean_url[:-4]
    try:
        resp = requests.post(
            f"{clean_url}/api/security-events/upload-offline",
            json=payload,
            headers={"Content-Type": "application/json"},
            auth=(admin_username, admin_password),
            timeout=30
        )
        if resp.status_code == 200:
            # Mark events as synced
            synced_ids = [e.id for e in unsynced_events]
            OfflineSecurityEvent.query.filter(OfflineSecurityEvent.id.in_(synced_ids)).update({OfflineSecurityEvent.synced: True}, synchronize_session=False)
            db.session.commit()
            print(f"[OFFLINE SECURITY SYNC] Successfully uploaded and marked {len(synced_ids)} offline security events as synced.")
            return True
        else:
            print(f"[OFFLINE SECURITY SYNC] Upload failed: {resp.status_code} {resp.text}")
            return False
    except requests.exceptions.ConnectionError as e:
        print(f"[OFFLINE SECURITY SYNC] Connection error during upload: {e}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"[OFFLINE SECURITY SYNC] Timeout during upload: {e}")
        return False
    except Exception as e:
        print(f"[OFFLINE SECURITY SYNC] Exception during upload: {e}")
        return False
