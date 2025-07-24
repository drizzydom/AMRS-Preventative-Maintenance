"""
Timezone utilities for consistent datetime handling across the application.
This ensures all datetime operations use Eastern Time (EST/EDT) for consistency.
"""

import os
from datetime import datetime, timezone, timedelta
try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False

# Eastern timezone definition
EASTERN_TZ = None
if PYTZ_AVAILABLE:
    try:
        EASTERN_TZ = pytz.timezone('America/New_York')
    except:
        try:
            EASTERN_TZ = pytz.timezone('US/Eastern')
        except:
            EASTERN_TZ = None

def get_eastern_now():
    """
    Get current datetime in Eastern timezone (EST/EDT).
    This ensures consistent datetime handling across online and offline apps.
    """
    if EASTERN_TZ:
        # Use pytz if available for proper DST handling
        return datetime.now(EASTERN_TZ)
    else:
        # Fallback: EST is UTC-5, EDT is UTC-4
        # Simple approximation - assumes EST for now
        utc_now = datetime.utcnow()
        est_offset = timedelta(hours=-5)  # EST is UTC-5
        return utc_now + est_offset

def convert_utc_to_eastern(utc_dt):
    """
    Convert a UTC datetime to Eastern timezone.
    """
    if utc_dt is None:
        return None
        
    if EASTERN_TZ:
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        return utc_dt.astimezone(EASTERN_TZ)
    else:
        # Fallback approximation
        if utc_dt.tzinfo is None:
            # Assume it's UTC if no timezone info
            est_offset = timedelta(hours=-5)  # EST approximation
            return utc_dt + est_offset
        else:
            return utc_dt

def get_eastern_date():
    """
    Get current date in Eastern timezone.
    This ensures audit task completions use consistent date boundaries.
    """
    eastern_now = get_eastern_now()
    return eastern_now.date()

def is_online_server():
    """
    Check if this is the online server (Render, Heroku, etc.)
    """
    return (
        os.environ.get('RENDER') or
        os.environ.get('HEROKU') or
        os.environ.get('RAILWAY') or
        'render.com' in os.environ.get('RENDER_EXTERNAL_URL', '') or
        not os.environ.get('AMRS_ONLINE_URL')
    )

def get_timezone_aware_now():
    """
    Get timezone-aware datetime for the current environment.
    - Online server (Render): Uses Eastern time for consistency
    - Offline client: Uses Eastern time for consistency
    This replaces datetime.now() and datetime.utcnow() for consistent behavior.
    """
    return get_eastern_now()

# For backward compatibility
now = get_timezone_aware_now
today = get_eastern_date
