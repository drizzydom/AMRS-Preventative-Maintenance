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
    
    An online server is identified by:
    1. Running on a known cloud platform (RENDER, HEROKU, RAILWAY set by the platform)
    2. Having IS_ONLINE_SERVER explicitly set to 'true'
    3. Using PostgreSQL database (not SQLite)
    
    IMPORTANT: Offline applications should NEVER return True here, even if they have
    bootstrap credentials. Those credentials are for CONNECTING to the online server,
    not for BEING the online server.
    """
    # First check: explicit platform environment variables (most reliable)
    render_check = os.environ.get('RENDER')
    heroku_check = os.environ.get('HEROKU')
    railway_check = os.environ.get('RAILWAY')
    
    if render_check or heroku_check or railway_check:
        print(f"[DEBUG] Online server detected by platform: RENDER={render_check}, HEROKU={heroku_check}, RAILWAY={railway_check}")
        return True
    
    # Second check: explicit override
    is_online_env = os.environ.get('IS_ONLINE_SERVER', '').lower()
    if is_online_env == 'true':
        print(f"[DEBUG] Online server detected by IS_ONLINE_SERVER={is_online_env}")
        return True
    
    # Third check: database type - online servers use PostgreSQL
    database_url = os.environ.get('DATABASE_URL', '')
    if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
        print(f"[DEBUG] Online server detected by PostgreSQL DATABASE_URL={database_url[:50]}...")
        return True
    
    # Fourth check: if running locally with SQLite, definitely offline
    if (database_url.startswith('sqlite://') or 
        not database_url or 
        'maintenance.db' in database_url or
        'maintenance_secure.db' in database_url):
        print(f"[DEBUG] Offline client detected by SQLite/empty DATABASE_URL={database_url}")
        return False
    
    # Default: assume offline for safety
    print(f"[DEBUG] Default offline detection with DATABASE_URL={database_url}")
    return False

def is_offline_mode():
    """
    Check if running in true offline mode (SQLite database, local testing).
    This is the inverse of is_online_server() but specifically checks for SQLite usage.
    """
    # If it's the online server, it's not offline mode
    online_server_check = is_online_server()
    if online_server_check:
        print(f"[DEBUG] is_offline_mode=False because is_online_server=True")
        return False
    
    # Check database type
    database_url = os.environ.get('DATABASE_URL', '')
    is_offline = (
        database_url.startswith('sqlite://') or 
        not database_url or  # No DATABASE_URL means SQLite fallback
        'maintenance.db' in database_url or
        'maintenance_secure.db' in database_url
    )
    
    print(f"[DEBUG] is_offline_mode={is_offline} with DATABASE_URL={database_url}")
    return is_offline

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
