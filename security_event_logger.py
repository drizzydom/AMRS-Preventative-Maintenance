from models import db, SecurityEvent, OfflineSecurityEvent
from flask import request, has_request_context
from flask_login import current_user
from datetime import datetime
import requests
import json
import threading
import time

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

def redact_security_details(details):
    """
    Automatically redact sensitive data from security event details before storage.
    Uses the centralized api_utils redaction helper.
    """
    if not details:
        return details
    
    try:
        from api_utils import redact_dict_for_logging
        
        # If details is a string, try to parse as JSON
        if isinstance(details, str):
            try:
                details_dict = json.loads(details)
                redacted = redact_dict_for_logging(details_dict)
                return json.dumps(redacted)
            except (json.JSONDecodeError, TypeError):
                # If not JSON, return as-is (it's plain text)
                return details
        
        # If details is a dict, redact and return as JSON string
        elif isinstance(details, dict):
            redacted = redact_dict_for_logging(details)
            return json.dumps(redacted)
        
        # For other types, convert to string
        return str(details)
    except ImportError:
        # If api_utils not available, return details as-is
        # This shouldn't happen in production but provides fallback
        return details if isinstance(details, str) else json.dumps(details) if isinstance(details, dict) else str(details)

def anonymize_ip(ip_address):
    """
    Anonymize IP address by masking last octet for IPv4, last 64 bits for IPv6.
    This balances privacy with useful geolocation data.
    """
    if not ip_address:
        return None
    
    try:
        # IPv4: mask last octet
        if '.' in ip_address and ':' not in ip_address:
            parts = ip_address.split('.')
            if len(parts) == 4:
                return f"{parts[0]}.{parts[1]}.{parts[2]}.0"
        
        # IPv6: mask last 64 bits
        elif ':' in ip_address:
            parts = ip_address.split(':')
            if len(parts) >= 4:
                return ':'.join(parts[:4]) + '::'
    except Exception:
        pass
    
    return ip_address  # Return original if anonymization fails

def log_security_event(event_type, details=None, is_critical=False, severity=None, source=None, correlation_id=None):
    # Check if logging is enabled (default: enabled)
    try:
        from models import AppSetting
        enabled = AppSetting.get('security_event_logging_enabled', '1') == '1'
    except Exception:
        enabled = True
    if not enabled:
        return
    
    # Automatically redact sensitive data from details
    redacted_details = redact_security_details(details)
    
    # Determine severity if not provided
    if severity is None:
        if is_critical:
            severity = 3  # critical
        else:
            severity = 0  # info
    
    # Determine source if not provided
    if source is None:
        source = 'offline-client' if not is_online() else 'web'
    
    user_id = None
    username = None
    ip_address = None
    raw_ip = None
    location = None
    actor_metadata = {}
    
    if has_request_context():
        raw_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        ip_address = anonymize_ip(raw_ip)  # Store anonymized IP
        location = get_location_from_ip(raw_ip)  # Use raw IP for geolocation
        
        # Store non-sensitive metadata
        user_agent = request.headers.get('User-Agent', '')
        if user_agent:
            # Store only first 100 chars of user agent to avoid excessive data
            actor_metadata['user_agent_prefix'] = user_agent[:100]
        
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            user_id = current_user.id
            # Try to get decrypted username, fallback to user ID if decryption fails
            try:
                username = getattr(current_user, 'username', None)
                # If username looks like encrypted data (starts with gAAAAAB), try to use a fallback
                if username and username.startswith('gAAAAAB'):
                    print(f"[SECURITY LOG WARNING] Username appears to be encrypted: {username[:20]}...")
                    username = f"user_{user_id}"  # Fallback to user ID
            except Exception as e:
                print(f"[SECURITY LOG WARNING] Error getting username: {e}")
                username = f"user_{user_id}"  # Fallback to user ID
    
    # Serialize actor_metadata to JSON string
    actor_metadata_json = json.dumps(actor_metadata) if actor_metadata else None
    
    # TIMESTAMP: Capture once to ensure both records match
    now_utc = datetime.utcnow()

    # 1. ALWAYS log to the local SecurityEvent table (for local dashboard visibility)
    # This works for both Server (Main DB) and Client (Local DB)
    event = SecurityEvent(
        event_type=event_type,
        user_id=user_id,
        username=username,
        ip_address=ip_address,
        location=location,
        details=redacted_details,
        is_critical=is_critical,
        severity=severity,
        source=source,
        correlation_id=correlation_id,
        actor_metadata=actor_metadata_json,
        timestamp=now_utc
    )
    db.session.add(event)
    
    # 2. CLIENT MODE CHECK: If we have an upstream server configured
    # We must queue this event for persistence and upload
    import os
    online_url = os.environ.get('AMRS_ONLINE_URL')
    
    if online_url:
        # We are a client -> Queue for sync
        offline_event = OfflineSecurityEvent(
            event_type=event_type,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            location=location,
            details=redacted_details,
            is_critical=is_critical,
            severity=severity,
            source=source,
            correlation_id=correlation_id,
            actor_metadata=actor_metadata_json,
            timestamp=now_utc,
            synced=False
        )
        db.session.add(offline_event)
        
        # Log to console
        print(f"[SECURITY LOG] {event_type} | User: {username or user_id} | Client Mode (Queued for Sync)")
    else:
        # We are the server -> Direct DB write only
        print(f"[SECURITY LOG] {event_type} | User: {username or user_id} | Server Mode (Direct Write)")

    db.session.commit()

    # 3. IMMEDIATE SYNC TRIGGER (Client Only)
    # If we are a client and currently online, try to push immediately for real-time visibility
    if online_url and is_online():
        try:
            # Run sync in background thread to avoid blocking the request
            t = threading.Thread(target=sync_offline_security_events)
            t.start()
        except Exception:
            pass  # Background agent will catch it later if this fails


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
    # Prepare payload with enhanced fields
    payload = [
        {
            'event_type': e.event_type,
            'user_id': e.user_id,
            'username': e.username,
            'ip_address': e.ip_address,
            'location': e.location,
            'details': e.details,
            'is_critical': e.is_critical,
            'severity': getattr(e, 'severity', 0),
            'source': getattr(e, 'source', 'offline-client'),
            'correlation_id': getattr(e, 'correlation_id', None),
            'actor_metadata': getattr(e, 'actor_metadata', None),
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

def start_security_event_sync_agent(app_instance, interval=300):
    """
    Start a background thread to sync offline security events periodically.
    Runs every `interval` seconds (default: 5 minutes).
    Ensures that admins can see all events regardless of when connectivity is restored.
    """
    def sync_job():
        # Initial delay to let the app startup
        time.sleep(10)
        print(f"[SECURITY SYNC AGENT] Started background sync agent. Interval: {interval}s")
        
        while True:
            try:
                # Check online status before attempting full sync to avoid log noise
                if is_online():
                    with app_instance.app_context():
                        sync_offline_security_events()
            except Exception as e:
                print(f"[SECURITY SYNC AGENT] Error in sync loop: {e}")
            
            time.sleep(interval)

    t = threading.Thread(target=sync_job, daemon=True, name="SecurityEventSyncAgent")
    t.start()
