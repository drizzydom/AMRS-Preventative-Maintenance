# === CRITICAL: Apply SQLAlchemy datetime parsing patch FIRST ===
# This must be imported before any SQLAlchemy operations to fix Python 3.11.0 compatibility
try:
    import sqlalchemy_datetime_patch
    print("[PATCH] SQLAlchemy datetime patch applied successfully")
except ImportError as e:
    print(f"[PATCH] SQLAlchemy datetime patch not available: {e}")
    # Continue without patch - may cause issues on Python 3.11.0 with certain datetime formats

# --- ALWAYS use secure SQLite database for offline mode ---
import os
from pathlib import Path
import sqlite3

def get_secure_database_path():
    import platform
    os_name = platform.system().lower()
    if os_name == "darwin":
        base_path = Path.home() / "Library" / "Application Support" / "AMRS_PM"
    elif os_name == "windows":
        base_path = Path(os.environ.get('APPDATA', '~')).expanduser() / "AMRS_PM"
    else:
        base_path = Path.home() / ".local" / "share" / "AMRS_PM"
    base_path.mkdir(parents=True, exist_ok=True)
    return str(base_path / "maintenance_secure.db")

def get_upload_folder_path():
    """
    Get the appropriate upload folder path for maintenance files.
    Uses the same cross-platform strategy as the database path.
    """
    import platform
    os_name = platform.system().lower()
    if os_name == "darwin":
        base_path = Path.home() / "Library" / "Application Support" / "AMRS_PM"
    elif os_name == "windows":
        base_path = Path(os.environ.get('APPDATA', '~')).expanduser() / "AMRS_PM"
    else:
        base_path = Path.home() / ".local" / "share" / "AMRS_PM"
    
    upload_path = base_path / "maintenance_files"
    upload_path.mkdir(parents=True, exist_ok=True)
    return str(upload_path)

def safe_parse_datetime(datetime_str):
    """
    Safely parse datetime strings from client data.
    Handles multiple formats and returns None for invalid dates.
    """
    if not datetime_str or datetime_str in ('NULL', 'None', '', 'null'):
        return None
    
    try:
        from datetime import datetime
        
        # First normalize the format
        normalized = normalize_datetime_format(datetime_str)
        if not normalized:
            return None
        
        # Try to parse the normalized datetime
        # Handle various formats
        formats_to_try = [
            '%Y-%m-%d %H:%M:%S.%f',  # With microseconds
            '%Y-%m-%d %H:%M:%S',     # Without microseconds
            '%Y-%m-%d',              # Date only
        ]
        
        for fmt in formats_to_try:
            try:
                return datetime.strptime(normalized, fmt)
            except ValueError:
                continue
        
        # If all standard formats fail, try fromisoformat as last resort
        try:
            return datetime.fromisoformat(normalized.replace('Z', '+00:00'))
        except ValueError:
            pass
        
        print(f"[DATETIME] Warning: Could not parse datetime '{datetime_str}' -> '{normalized}'")
        return None
        
    except Exception as e:
        print(f"[DATETIME] Error parsing datetime '{datetime_str}': {e}")
        return None

def sanitize_sync_record(record, datetime_fields):
    """
    Sanitize a sync record by normalizing datetime fields and handling errors gracefully.
    """
    if not record:
        return record
    
    sanitized = record.copy()
    
    for field in datetime_fields:
        if field in sanitized and sanitized[field]:
            # Parse and re-format datetime to ensure consistency
            parsed_dt = safe_parse_datetime(sanitized[field])
            if parsed_dt:
                sanitized[field] = parsed_dt
            else:
                # If parsing fails, remove the field rather than crash
                print(f"[SYNC] Warning: Removing invalid datetime field '{field}': {sanitized[field]}")
                sanitized[field] = None
    
    return sanitized

def fix_datetime_fields_in_record(record, datetime_fields):
    """
    Fix datetime format issues in a single record during sync operations.
    Uses the comprehensive normalize_datetime_format function.
    """
    if not record or not datetime_fields:
        return record
    
    for field in datetime_fields:
        if field in record and record[field]:
            record[field] = normalize_datetime_format(record[field])
    
    return record

def normalize_datetime_format(datetime_str):
    """
    Normalize any datetime string to SQLite-compatible format.
    Handles multiple input formats and ensures consistent output.
    
    Supported input formats:
    - '2025-04-28T18:17:52.547667' (ISO with microseconds)
    - '2025-04-28T18:17:52' (ISO without microseconds)
    - '2025-04-28 18:17:52.547667' (SQLite format with microseconds)
    - '2025-04-28 18:17:52' (SQLite format without microseconds)
    - '2025-04-28' (Date only)
    
    Output format: '2025-04-28 18:17:52.547667' or '2025-04-28 18:17:52'
    """
    if not datetime_str or datetime_str in ('NULL', 'None', '', 'null'):
        return None
    
    try:
        # Handle string input
        if isinstance(datetime_str, str):
            datetime_str = datetime_str.strip()
            
            # Convert ISO format (T separator) to space separator
            if 'T' in datetime_str:
                datetime_str = datetime_str.replace('T', ' ')
            
            # Remove timezone info if present (Z or +/-offset)
            if datetime_str.endswith('Z'):
                datetime_str = datetime_str[:-1]
            elif '+' in datetime_str and datetime_str.count('+') == 1:
                datetime_str = datetime_str.split('+')[0]
            elif datetime_str.count('-') > 2:  # More than date separators
                # Handle negative timezone offset
                parts = datetime_str.split('-')
                if len(parts) > 3:
                    datetime_str = '-'.join(parts[:-1])
            
            return datetime_str
            
        # Handle datetime object input
        elif hasattr(datetime_str, 'strftime'):
            return datetime_str.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Truncate to 3 decimal places
            
        # Handle other types by converting to string first
        else:
            return normalize_datetime_format(str(datetime_str))
            
    except Exception as e:
        print(f"[DATETIME] Warning: Could not normalize datetime '{datetime_str}': {e}")
        return str(datetime_str) if datetime_str else None

def run_comprehensive_datetime_fix(cursor):
    """
    Run comprehensive datetime format fix on all tables after sync.
    This ensures all datetime values are in SQLite-compatible format.
    """
    datetime_fix_count = 0
    
    # Define tables and their datetime columns
    tables_columns = {
        'users': ['last_login', 'created_at', 'updated_at', 'reset_token_expiration', 'remember_token_expiration'],
        'machines': ['created_at', 'updated_at', 'decommissioned_date'],
        'maintenance_records': ['date', 'created_at', 'updated_at'],
        'audit_tasks': ['created_at', 'updated_at'],
        'audit_task_completions': ['date', 'completed_at', 'created_at', 'updated_at', 'completed_date'],
        'sites': ['created_at', 'updated_at'],
        'roles': ['created_at', 'updated_at'],
        'parts': ['last_maintenance', 'next_maintenance', 'created_at', 'updated_at'],
        'maintenance_files': ['uploaded_at'],
        'sync_queue': ['created_at', 'updated_at', 'synced_at'],
        'security_events': ['timestamp']
    }
    
    for table_name, columns in tables_columns.items():
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            continue
        
        for column in columns:
            # Check if column exists
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            column_exists = any(col[1] == column for col in columns_info)
            
            if not column_exists:
                continue
            
            # Get all non-null datetime values that might need fixing
            cursor.execute(f"""
                SELECT rowid, {column} FROM {table_name} 
                WHERE {column} IS NOT NULL 
                AND {column} != '' 
                AND ({column} LIKE '%T%' OR {column} LIKE '%Z' OR {column} LIKE '%+%' OR {column} LIKE '%--%')
            """)
            
            rows_to_fix = cursor.fetchall()
            
            for rowid, datetime_val in rows_to_fix:
                normalized_datetime = normalize_datetime_format(datetime_val)
                
                if normalized_datetime and normalized_datetime != datetime_val:
                    cursor.execute(f"""
                        UPDATE {table_name} 
                        SET {column} = ? 
                        WHERE rowid = ?
                    """, (normalized_datetime, rowid))
                    
                    datetime_fix_count += 1
    
    return datetime_fix_count

SECURE_DB_PATH = get_secure_database_path()
os.environ['DATABASE_URL'] = f"sqlite:///{SECURE_DB_PATH}"
print(f"[BOOT] Using secure database: {SECURE_DB_PATH}")

# --- Ensure schema is created before any data import or hash fix ---
import sqlite3
try:
    conn = sqlite3.connect(SECURE_DB_PATH)
    cursor = conn.cursor()
    # Comprehensive schema creation for all tables/columns used in the app
    schema_sql = [
        '''CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            permissions TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            active BOOLEAN DEFAULT 1,
            is_admin BOOLEAN DEFAULT 0,
            role_id INTEGER,
            last_login TIMESTAMP,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            reset_token TEXT,
            reset_token_expiration TIMESTAMP,
            username_hash TEXT,
            email_hash TEXT,
            remember_token TEXT,
            remember_token_expiration TIMESTAMP,
            remember_enabled BOOLEAN DEFAULT 0,
            notification_preferences TEXT,
            FOREIGN KEY (role_id) REFERENCES roles(id)
        )''',
        '''CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT,
            contact_email TEXT,
            enable_notifications BOOLEAN DEFAULT 1,
            notification_threshold INTEGER DEFAULT 30,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS machines (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            model TEXT,
            serial_number TEXT,
            machine_number TEXT,
            site_id INTEGER,
            decommissioned BOOLEAN DEFAULT 0,
            decommissioned_date TIMESTAMP,
            decommissioned_by TEXT,
            decommissioned_reason TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites(id)
        )''',
        '''CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            machine_id INTEGER,
            maintenance_frequency INTEGER,
            maintenance_unit TEXT,
            last_maintenance TIMESTAMP,
            next_maintenance TIMESTAMP,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (machine_id) REFERENCES machines(id)
        )''',
        '''CREATE TABLE IF NOT EXISTS audit_tasks (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            site_id INTEGER,
            created_by INTEGER,
            interval TEXT,
            custom_interval_days INTEGER,
            color TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )''',
        '''CREATE TABLE IF NOT EXISTS machine_audit_task (
            machine_id INTEGER NOT NULL,
            audit_task_id INTEGER NOT NULL,
            PRIMARY KEY (machine_id, audit_task_id),
            FOREIGN KEY (machine_id) REFERENCES machines(id),
            FOREIGN KEY (audit_task_id) REFERENCES audit_tasks(id)
        )''',
        '''CREATE TABLE IF NOT EXISTS maintenance_records (
            id INTEGER PRIMARY KEY,
            machine_id INTEGER,
            part_id INTEGER,
            user_id INTEGER,
            maintenance_type TEXT,
            description TEXT,
            date TIMESTAMP,
            performed_by TEXT,
            status TEXT,
            notes TEXT,
            comments TEXT,
            client_id INTEGER,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (machine_id) REFERENCES machines(id),
            FOREIGN KEY (part_id) REFERENCES parts(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''',
        '''CREATE TABLE IF NOT EXISTS audit_task_completions (
            id INTEGER PRIMARY KEY,
            audit_task_id INTEGER,
            machine_id INTEGER,
            date TIMESTAMP,
            completed BOOLEAN DEFAULT 0,
            completed_by INTEGER,
            completed_at TIMESTAMP,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (audit_task_id) REFERENCES audit_tasks(id),
            FOREIGN KEY (machine_id) REFERENCES machines(id),
            FOREIGN KEY (completed_by) REFERENCES users(id)
        )''',
        '''CREATE TABLE IF NOT EXISTS maintenance_files (
            id INTEGER PRIMARY KEY,
            maintenance_record_id INTEGER,
            filename TEXT,
            filedata BLOB,
            filepath TEXT,
            filetype TEXT,
            filesize INTEGER,
            thumbnail_path TEXT,
            uploaded_by INTEGER,
            uploaded_at TIMESTAMP,
            FOREIGN KEY (maintenance_record_id) REFERENCES maintenance_records(id),
            FOREIGN KEY (uploaded_by) REFERENCES users(id)
        )''',
        '''CREATE TABLE IF NOT EXISTS sync_queue (
            id INTEGER PRIMARY KEY,
            table_name TEXT,
            record_id INTEGER,
            operation TEXT,
            payload TEXT,
            status TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            synced_at TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS app_settings (
            id INTEGER PRIMARY KEY,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            updated_at TIMESTAMP
        )'''
    ]
    for sql in schema_sql:
        cursor.execute(sql)
    conn.commit()
    conn.close()
    print(f"[SCHEMA] Ensured all tables and columns exist in {SECURE_DB_PATH}")
except Exception as e:
    print(f"[SCHEMA] Error ensuring schema: {e}")

from datetime import datetime, timedelta
from flask import Flask, request, render_template, redirect, url_for, flash, current_app, jsonify, Response, abort
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf, validate_csrf
# Don't import db here - we'll import it after Flask app creation
from models import SecurityEvent, AppSetting
from sqlalchemy import or_

# Initialize Flask app at the very top

app = Flask(__name__, instance_relative_config=True)

# --- Update Server Endpoints (merged from update_server.py) ---
import yaml
import subprocess

B2_KEY_ID = os.environ.get("B2_KEY_ID")
B2_APP_KEY = os.environ.get("B2_APP_KEY")
B2_BUCKET = os.environ.get("B2_BUCKET")
SIGNED_URL_TTL = int(os.environ.get("SIGNED_URL_TTL", "600"))
UPDATES_API_KEY = os.environ.get("UPDATES_API_KEY")
BOOTSTRAP_URL = os.environ.get("BOOTSTRAP_URL", "https://your-bootstrap-url.example.com")

# Try to use B2 SDK, fall back to CLI if not available
try:
    from b2sdk.v2 import InMemoryAccountInfo, B2Api
    from b2sdk.exception import B2Error
    B2_SDK_AVAILABLE = True
    print("[B2] B2 SDK available - using API")
except ImportError:
    B2_SDK_AVAILABLE = False
    print("[B2] B2 SDK not available - falling back to CLI")

# Initialize B2 API client (only if SDK is available)
b2_api = None
b2_bucket_obj = None

def get_b2_api():
    global b2_api, b2_bucket_obj
    if not B2_SDK_AVAILABLE:
        raise Exception("B2 SDK not available")
    
    if b2_api is None:
        try:
            info = InMemoryAccountInfo()
            b2_api = B2Api(info)
            b2_api.authorize_account("production", B2_KEY_ID, B2_APP_KEY)
            b2_bucket_obj = b2_api.get_bucket_by_name(B2_BUCKET)
            print(f"[B2] Successfully initialized B2 API for bucket: {B2_BUCKET}")
        except Exception as e:
            print(f"[B2] Error initializing B2 API: {e}")
            raise
    return b2_api, b2_bucket_obj

def get_signed_url_sdk(bucket, filename, ttl=SIGNED_URL_TTL):
    try:
        _, bucket_obj = get_b2_api()
        # Get file info
        file_info = bucket_obj.get_file_info_by_name(filename)
        # Generate signed download URL
        download_url = bucket_obj.get_download_url_by_name(filename)
        # For signed URLs, we need to add authorization
        auth_token = b2_api.account_info.get_auth_token()
        signed_url = f"{download_url}?Authorization={auth_token}"
        return signed_url
    except Exception as e:
        print(f"[B2] Error getting signed URL for {filename}: {e}")
        raise

def get_signed_url_cli(bucket, filename, ttl=SIGNED_URL_TTL):
    try:
        # Authorize first
        cmd = ["b2", "authorize-account", B2_KEY_ID, B2_APP_KEY]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Get signed URL
        cmd = ["b2", "get-download-url-with-auth", bucket, filename]
        p = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return p.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[B2] CLI error getting signed URL for {filename}: {e.stderr}")
        raise

def get_signed_url(bucket, filename, ttl=SIGNED_URL_TTL):
    if B2_SDK_AVAILABLE and B2_KEY_ID and B2_APP_KEY:
        try:
            return get_signed_url_sdk(bucket, filename, ttl)
        except Exception as e:
            print(f"[B2] SDK failed, falling back to CLI: {e}")
            return get_signed_url_cli(bucket, filename, ttl)
    else:
        return get_signed_url_cli(bucket, filename, ttl)

def get_latest_available_version():
    """
    Determine the latest version available for download.
    This function should check what installer files actually exist on the server/storage.
    """
    print("[UPDATE] Checking for latest available version...")
    
    # Method 1: Check environment variable for latest available version
    latest_from_env = os.environ.get("LATEST_AVAILABLE_VERSION")
    if latest_from_env:
        print(f"[UPDATE] Using latest version from environment: {latest_from_env}")
        return latest_from_env
    
    # Method 2: Check a versions.json file that lists available versions
    versions_file_path = os.path.join(os.path.dirname(__file__), 'versions.json')
    if os.path.exists(versions_file_path):
        try:
            import json
            with open(versions_file_path, 'r') as f:
                versions_data = json.load(f)
                latest_version = versions_data.get('latest')
                if latest_version:
                    print(f"[UPDATE] Using latest version from versions.json: {latest_version}")
                    return latest_version
        except Exception as e:
            print(f"[UPDATE] Error reading versions.json: {e}")
    
    # Method 3: Try to check B2 bucket for available files (if configured)
    # This would require listing bucket contents and parsing filenames
    # For now, we'll skip this as it requires additional B2 permissions
    
    # Method 4: Default to current app version (no update available)
    try:
        # Get current app version as fallback
        package_json_path = os.path.join(os.path.dirname(__file__), 'package.json')
        app_package_json_path = os.path.join(os.path.dirname(__file__), 'app-package.json')
        
        current_version = None
        if os.path.exists(package_json_path):
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
                current_version = package_data.get('version')
        elif os.path.exists(app_package_json_path):
            with open(app_package_json_path, 'r') as f:
                package_data = json.load(f)
                current_version = package_data.get('version')
        
        if current_version:
            print(f"[UPDATE] No remote version info available, using current version: {current_version}")
            return current_version
            
    except Exception as e:
        print(f"[UPDATE] Error getting current version: {e}")
    
    # Final fallback
    fallback_version = "1.4.4"
    print(f"[UPDATE] Using fallback version: {fallback_version}")
    return fallback_version

@app.route("/latest.yml")
def latest_yml():
    print(f"[UPDATE] Request to /latest.yml from {request.remote_addr}")
    print(f"[UPDATE] User-Agent: {request.headers.get('User-Agent', 'Unknown')}")
    
    # For update checking, we need to serve the NEWER version information
    # Instead of reading from bundled file, get current version from the app itself
    
    # Try to read the current version from package.json or environment
    current_version = None
    
    # Method 1: Try to read from package.json if available
    package_json_path = os.path.join(os.path.dirname(__file__), 'package.json')
    if os.path.exists(package_json_path):
        try:
            import json
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
                current_version = package_data.get('version')
                print(f"[UPDATE] Found current version from package.json: {current_version}")
        except Exception as e:
            print(f"[UPDATE] Error reading package.json: {e}")
    
    # Method 1b: Try to read from app-package.json (bundled version)
    if not current_version:
        app_package_json_path = os.path.join(os.path.dirname(__file__), 'app-package.json')
        if os.path.exists(app_package_json_path):
            try:
                import json
                with open(app_package_json_path, 'r') as f:
                    package_data = json.load(f)
                    current_version = package_data.get('version')
                    print(f"[UPDATE] Found current version from app-package.json: {current_version}")
            except Exception as e:
                print(f"[UPDATE] Error reading app-package.json: {e}")
    
    # Method 2: Fall back to environment variable
    if not current_version:
        current_version = os.environ.get("APP_VERSION", "1.4.4")
        print(f"[UPDATE] Using version from environment/default: {current_version}")
    
    # Determine the latest available version from the server
    # This should check what versions are actually available for download
    latest_available_version = get_latest_available_version()
    
    print(f"[UPDATE] App version: {current_version}")
    print(f"[UPDATE] Latest available version: {latest_available_version}")
    
    # Only serve update info if there's actually a newer version available
    from packaging import version as version_parser
    
    try:
        if version_parser.parse(latest_available_version) > version_parser.parse(current_version):
            print(f"[UPDATE] Update available: {latest_available_version} > {current_version}")
            target_version = latest_available_version
        else:
            print(f"[UPDATE] No update needed: {latest_available_version} <= {current_version}")
            # Return current version to indicate no update
            target_version = current_version
    except Exception as e:
        print(f"[UPDATE] Error comparing versions: {e}")
        # If we can't compare, assume no update to be safe
        target_version = current_version
    
    print(f"[UPDATE] Serving version info: target={target_version}")
    
    # Generate the update metadata
    latest_yml_content = f"""version: {target_version}
files:
  - url: https://your-b2-bucket.s3.amazonaws.com/Accurate-Machine-Repair-Maintenance-Tracker-Win10-Setup-{target_version}.exe
    sha512: target-version-sha512-hash-placeholder
    size: 140000000
path: Accurate-Machine-Repair-Maintenance-Tracker-Win10-Setup-{target_version}.exe
sha512: target-version-sha512-hash-placeholder
releaseDate: '{datetime.now().isoformat()}Z'
"""
    
    print(f"[UPDATE] Serving update latest.yml content:")
    print(latest_yml_content)
    
    return Response(latest_yml_content.strip(), mimetype="text/yaml", headers={
        'Content-Type': 'text/yaml',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    })

@app.route("/update-test")
def update_test():
    """Test endpoint to verify update server is reachable and check version detection"""
    
    # Test version detection logic
    current_version = None
    package_json_path = os.path.join(os.path.dirname(__file__), 'package.json')
    app_package_json_path = os.path.join(os.path.dirname(__file__), 'app-package.json')
    
    if os.path.exists(package_json_path):
        try:
            import json
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
                current_version = package_data.get('version')
        except Exception as e:
            current_version = f"Error reading package.json: {e}"
    elif os.path.exists(app_package_json_path):
        try:
            import json
            with open(app_package_json_path, 'r') as f:
                package_data = json.load(f)
                current_version = package_data.get('version')
        except Exception as e:
            current_version = f"Error reading app-package.json: {e}"
    else:
        current_version = "No package.json or app-package.json found"
    
    # Test latest.yml path
    latest_yml_path = os.path.join(os.path.dirname(__file__), 'latest.yml')
    latest_yml_exists = os.path.exists(latest_yml_path)
    
    # Test versions.json path
    versions_json_path = os.path.join(os.path.dirname(__file__), 'versions.json')
    versions_json_exists = os.path.exists(versions_json_path)
    
    # Get latest available version
    latest_available = get_latest_available_version()
    
    return jsonify({
        "status": "ok",
        "message": "Update server is reachable",
        "current_time": datetime.now().isoformat(),
        "version_detection": {
            "package_json_path": package_json_path,
            "package_json_exists": os.path.exists(package_json_path),
            "app_package_json_path": app_package_json_path,
            "app_package_json_exists": os.path.exists(app_package_json_path),
            "detected_version": current_version,
            "env_app_version": os.environ.get("APP_VERSION", "not set"),
            "latest_yml_path": latest_yml_path,
            "latest_yml_exists": latest_yml_exists,
            "versions_json_path": versions_json_path,
            "versions_json_exists": versions_json_exists,
            "latest_available_version": latest_available,
            "update_needed": latest_available != current_version if current_version else False
        }
    })

@app.route("/bootstrap-config")
def bootstrap_config():
    api_key = request.headers.get("X-API-KEY") or request.args.get("api_key")
    if UPDATES_API_KEY and api_key != UPDATES_API_KEY:
        abort(401)
    config = {
        "bootstrap_url": BOOTSTRAP_URL,
        "update_server_url": request.url_root,
        "venv_packages": os.environ.get("VENV_PACKAGES", ""),
        "b2_key_id": os.environ.get("B2_KEY_ID", ""),
        "b2_bucket": os.environ.get("B2_BUCKET", ""),
        "app_version": os.environ.get("APP_VERSION", ""),
        "release_file": os.environ.get("RELEASE_FILE", "")
    }
    return jsonify(config)

# Import the database instance but don't initialize it yet
from models import db
# Database will be initialized after configuration is set up


# --- Initialize Flask-Mail before using it ---
from flask_mail import Mail
mail = Mail(app)


# --- Start Security Event Email Batcher on App Startup (inside app context) ---
@app.before_first_request
def start_security_event_batcher():
    try:
        from security_event_batcher import SecurityEventBatcher
        admin_email = os.environ.get('ADMIN_EMAIL') or app.config.get('MAIL_DEFAULT_SENDER')
        if admin_email:
            batcher = SecurityEventBatcher(mail, admin_email)
            batcher.start()
            print('[STARTUP] SecurityEventBatcher started.')
        else:
            print('[STARTUP] SecurityEventBatcher not started: No admin email set.')
    except Exception as e:
        print(f'[STARTUP] Error starting SecurityEventBatcher: {e}')


# --- Security Event Log Retention Policy ---
import threading
from datetime import datetime, timedelta
from models import SecurityEvent, db

def delete_old_security_events():
    retention_days = int(getattr(current_app.config, 'SECURITY_EVENT_LOG_RETENTION_DAYS', 90))
    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    num_deleted = SecurityEvent.query.filter(SecurityEvent.timestamp < cutoff).delete()
    if num_deleted:
        db.session.commit()
        print(f"[SECURITY LOG RETENTION] Deleted {num_deleted} security events older than {retention_days} days.")

def start_security_event_retention_job():
    def job():
        while True:
            try:
                with current_app.app_context():
                    delete_old_security_events()
            except Exception as e:
                print(f"[SECURITY LOG RETENTION] Error: {e}")
            time.sleep(24 * 3600)  # Run once per day
    t = threading.Thread(target=job, daemon=True)
    t.start()

# Start the retention job after app is initialized
@app.before_first_request
def start_retention_job():
    start_security_event_retention_job()

    # Sync offline security events on app startup
    try:
        from security_event_logger import sync_offline_security_events
        sync_offline_security_events()
    except Exception as e:
        print(f"[OFFLINE SECURITY SYNC] Error during startup sync: {e}")
    
    # NOTE: Bootstrap trigger moved to initialize_database_and_bootstrap() function
    # This prevents double execution and ensures proper app context
        try:
            print("[APP] Triggering initial database sync after successful bootstrap...")
            # Import sync_db function for initial data download
            import subprocess
            import sys
            
            # Check if we have required credentials
            online_url = os.environ.get('AMRS_ONLINE_URL')
            admin_username = os.environ.get('AMRS_ADMIN_USERNAME')
            admin_password = os.environ.get('AMRS_ADMIN_PASSWORD')
            
            if online_url and admin_username and admin_password:
                # Try sync_db.py script for comprehensive data download
                try:
                    script_path = os.path.join(BASE_DIR, 'sync_db.py')
                    if os.path.exists(script_path):
                        print("[APP] Running sync_db.py for initial data sync...")
                        result = subprocess.run([
                            sys.executable, script_path,
                            '--url', online_url.strip('"\''),
                            '--username', admin_username,
                            '--password', admin_password
                        ], capture_output=True, text=True, timeout=120)
                        
                        if result.returncode == 0:
                            print("[APP] Initial database sync completed successfully")
                        else:
                            print(f"[APP] Initial database sync failed: {result.stderr}")
                    else:
                        print("[APP] sync_db.py not found, skipping initial sync")
                        
                except subprocess.TimeoutExpired:
                    print("[APP] Initial database sync timed out")
                except Exception as sync_error:
                    print(f"[APP] Error during initial database sync: {sync_error}")
            else:
                print("[APP] Missing credentials for initial database sync")
                
        except Exception as e:
            print(f"[APP] Error setting up initial sync: {e}")
    else:
        print("[APP] Bootstrap was not successful or not attempted - skipping initial sync")
from flask import request, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user


# --- API endpoint to receive offline security events from clients ---
from flask import request, jsonify
from models import SecurityEvent, db
import datetime

@app.route('/api/security-events/upload-offline', methods=['POST'])
def upload_offline_security_events():
    """
    Receives a batch of offline security events from a client and inserts them into the SecurityEvent table.
    Requires admin or sync service permissions.
    """
    if not check_sync_auth():
        return jsonify({'error': 'Unauthorized - Admin or sync service permissions required'}), 403

    events = request.get_json(force=True)
    if not isinstance(events, list):
        return jsonify({'error': 'Invalid payload'}), 400
    inserted = 0
    for e in events:
        try:
            # Prevent duplicate insertions by checking for unique (timestamp, event_type, user_id, details)
            exists = SecurityEvent.query.filter_by(
                timestamp=datetime.datetime.fromisoformat(e['timestamp']) if e.get('timestamp') else None,
                event_type=e.get('event_type'),
                user_id=e.get('user_id'),
                details=e.get('details')
            ).first()
            if exists:
                continue
            event = SecurityEvent(
                event_type=e.get('event_type'),
                user_id=e.get('user_id'),
                username=e.get('username'),
                ip_address=e.get('ip_address'),
                location=e.get('location'),
                details=e.get('details'),
                is_critical=e.get('is_critical', False),
                timestamp=datetime.datetime.fromisoformat(e['timestamp']) if e.get('timestamp') else datetime.datetime.utcnow()
            )
            db.session.add(event)
            inserted += 1
        except Exception as ex:
            print(f"[SECURITY EVENT UPLOAD] Error processing event: {ex}")
            continue
    db.session.commit()
    return jsonify({'status': 'ok', 'inserted': inserted}), 200


# --- Utility: Fix user hashes in the secure database ---
import hashlib
def fix_user_hashes(db_path):
    import sqlite3
    def hash_value(value):
        if not value:
            return None
        value = value.strip().lower()
        return hashlib.sha256(value.encode('utf-8')).hexdigest()
    
    def decrypt_field(encrypted_value):
        """Try to decrypt a field to see if it's encrypted or plain text."""
        try:
            from models import decrypt_value
            return decrypt_value(encrypted_value)
        except:
            # If decryption fails, assume it's already plain text
            return encrypted_value
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username, email, username_hash, email_hash FROM users")
        users = cursor.fetchall()
        updates_made = 0
        
        for user_id, username, email, existing_username_hash, existing_email_hash in users:
            # Try to decrypt the stored username/email to get the plain text for hashing
            try:
                plain_username = decrypt_field(username) if username else None
                plain_email = decrypt_field(email) if email else None
            except:
                # If decryption fails, it might already be plain text
                plain_username = username
                plain_email = email
            
            # Only update hashes if they're missing or if we can verify they're wrong
            update_needed = False
            new_username_hash = existing_username_hash
            new_email_hash = existing_email_hash
            
            # Check username hash
            if not existing_username_hash and plain_username:
                new_username_hash = hash_value(plain_username)
                update_needed = True
                print(f"[HASH FIX] User {user_id}: computed missing username hash")
            elif existing_username_hash and plain_username:
                # Verify the existing hash is correct for the plain text
                expected_hash = hash_value(plain_username)
                if existing_username_hash != expected_hash:
                    # Only update if the current hash is clearly wrong (too short, invalid format, etc.)
                    if len(existing_username_hash) < 32:  # SHA256 should be 64 chars
                        new_username_hash = expected_hash
                        update_needed = True
                        print(f"[HASH FIX] User {user_id}: fixed invalid username hash")
                    else:
                        print(f"[HASH FIX] User {user_id}: preserving existing username hash (likely from server)")
            
            # Check email hash
            if not existing_email_hash and plain_email:
                new_email_hash = hash_value(plain_email)
                update_needed = True
                print(f"[HASH FIX] User {user_id}: computed missing email hash")
            elif existing_email_hash and plain_email:
                # Verify the existing hash is correct for the plain text
                expected_hash = hash_value(plain_email)
                if existing_email_hash != expected_hash:
                    # Only update if the current hash is clearly wrong
                    if len(existing_email_hash) < 32:  # SHA256 should be 64 chars
                        new_email_hash = expected_hash
                        update_needed = True
                        print(f"[HASH FIX] User {user_id}: fixed invalid email hash")
                    else:
                        print(f"[HASH FIX] User {user_id}: preserving existing email hash (likely from server)")
            
            if update_needed:
                cursor.execute(
                    "UPDATE users SET username_hash = ?, email_hash = ? WHERE id = ?",
                    (new_username_hash, new_email_hash, user_id)
                )
                updates_made += 1
        
        conn.commit()
        print(f"[HASH FIX] Made {updates_made} hash updates out of {len(users)} users in {db_path}")
    except Exception as e:
        print(f"[HASH FIX] Error updating user hashes: {e}")
    finally:
        conn.close()

# --- Load environment variables FIRST (before any other imports) ---
import os
import sys
import json as _json
from dotenv import load_dotenv

# Get the directory of this file and load .env immediately
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)
print(f"[APP] Loaded .env from: {dotenv_path}")

# Load bootstrap environment variables from keyring (BEFORE importing models)
def load_bootstrap_environment():
    """Load bootstrap environment variables from keyring storage to prevent encryption key errors."""
    try:
        from load_bootstrap_env import load_bootstrap_env
        return load_bootstrap_env()
    except Exception as e:
        print(f"[APP] Note: Could not load bootstrap environment: {e}")
        return False

# Load bootstrap environment before any models are imported
load_bootstrap_environment()
try:
    fix_user_hashes(SECURE_DB_PATH)
except Exception as e:
    print(f"[HASH FIX] Error running on startup: {e}")

# Import models AFTER loading bootstrap environment
from models import db, User, Role, Site, Machine, Part, MaintenanceRecord, AuditTask, AuditTaskCompletion, MaintenanceFile, encrypt_value, hash_value, SecurityEvent, AppSetting

# --- Load and bootstrap secrets from keyring or remote if missing ---
def get_secure_storage_service():
    """Get the appropriate secure storage service name based on OS."""
    import platform
    os_name = platform.system().lower()
    
    if os_name == "windows":
        return "amrs_pm_windows"
    elif os_name == "darwin":  # macOS
        return "amrs_pm_macos"
    elif os_name == "linux":
        return "amrs_pm_linux"
    else:
        return "amrs_pm_unknown"

def test_secure_storage():
    """Test secure storage functionality and provide platform-specific notes."""
    import platform
    os_name = platform.system()
    
    print(f"[STORAGE] Testing secure storage on {os_name}...")
    
    try:
        import keyring
        service = get_secure_storage_service()
        
        # Test write/read/delete
        test_key = "test_bootstrap_key"
        test_value = "test_bootstrap_value"
        
        keyring.set_password(service, test_key, test_value)
        retrieved = keyring.get_password(service, test_key)
        
        if retrieved == test_value:
            print(f"[STORAGE] SUCCESS: Secure storage working on {os_name}")
            keyring.delete_password(service, test_key)  # Cleanup
            
            # Platform-specific notes
            if os_name == "Darwin":  # macOS
                print("[STORAGE] macOS Note: Using Keychain Access for secure storage")
                print("[STORAGE] Windows Deployment: Will use Windows Credential Manager")
            elif os_name == "Windows":
                print("[STORAGE] Windows Note: Using Windows Credential Manager")
            elif os_name == "Linux":
                print("[STORAGE] Linux Note: Using Secret Service API (GNOME Keyring)")
                
            return True
        else:
            print(f"[STORAGE] ERROR: Secure storage test failed: {retrieved} != {test_value}")
            return False
            
    except Exception as e:
        print(f"[STORAGE] ERROR: Secure storage error: {e}")
        return False

def bootstrap_secrets_from_remote():
    """
    Enhanced bootstrap function that downloads secrets and triggers database sync.
    This is the main entry point for offline applications to get fully configured.
    """
    try:
        import keyring
        import requests
        import sqlite3
        import json
        from pathlib import Path
        
        # Test secure storage first
        if not test_secure_storage():
            print("[BOOTSTRAP] Warning: Secure storage test failed, continuing anyway...")
        
        KEYRING_SERVICE = get_secure_storage_service()
        KEYRING_KEYS = [
            "USER_FIELD_ENCRYPTION_KEY",
            "RENDER_EXTERNAL_URL", 
            "SYNC_URL",
            "SYNC_USERNAME",
            "AMRS_ONLINE_URL",
            "AMRS_ADMIN_USERNAME",
            "AMRS_ADMIN_PASSWORD",
            "MAIL_SERVER",
            "MAIL_PORT",
            "MAIL_USE_TLS",
            "MAIL_USERNAME",
            "MAIL_PASSWORD",
            "MAIL_DEFAULT_SENDER",
            "SECRET_KEY",
            "BOOTSTRAP_SECRET_TOKEN",
        ]
        
        loaded_any = False
        missing_keys = []
        
        print(f"[BOOTSTRAP] Starting comprehensive bootstrap process...")
        print(f"[BOOTSTRAP] Secure storage service: {KEYRING_SERVICE}")
        
        # First, try to load all secrets from keyring
        for key in KEYRING_KEYS:
            value = keyring.get_password(KEYRING_SERVICE, key)
            if value:
                os.environ[key] = value
                loaded_any = True
            else:
                missing_keys.append(key)
        
        # Always attempt bootstrap if we have credentials, even if some secrets exist
        bootstrap_url = os.environ.get("BOOTSTRAP_URL")
        bootstrap_token = os.environ.get("BOOTSTRAP_SECRET_TOKEN")
        
        bootstrap_attempted = False
        if bootstrap_url and bootstrap_token:
            try:
                print(f"[BOOTSTRAP] Downloading configuration from: {bootstrap_url}")
                resp = requests.post(
                    bootstrap_url,
                    headers={"Authorization": f"Bearer {bootstrap_token}"},
                    timeout=15
                )
                
                if resp.status_code == 200:
                    secrets = resp.json()
                    print(f"[BOOTSTRAP] Retrieved {len(secrets)} secrets from remote")
                    
                    # Store ALL secrets from response
                    stored_count = 0
                    for k, v in secrets.items():
                        if k in KEYRING_KEYS and v:
                            try:
                                keyring.set_password(KEYRING_SERVICE, k, v)
                                os.environ[k] = v
                                stored_count += 1
                                print(f"[BOOTSTRAP] Stored secret: {k}")
                            except Exception as store_error:
                                print(f"[BOOTSTRAP] Failed to store {k}: {store_error}")
                    
                    print(f"[BOOTSTRAP] SUCCESS: Configuration downloaded and stored ({stored_count} secrets)")
                    bootstrap_attempted = True
                    
                else:
                    print(f"[BOOTSTRAP] Configuration download failed: {resp.status_code} {resp.text}")
                    
            except Exception as e:
                print(f"[BOOTSTRAP] Configuration download error: {e}")
        
        # Now attempt database sync if we have the necessary credentials
        sync_success = attempt_database_sync()
        
        if bootstrap_attempted or loaded_any:
            if sync_success:
                print("[BOOTSTRAP] SUCCESS: Complete bootstrap successful - configuration + database sync completed")
                
                # Clean up temporary bootstrap file if it exists
                try:
                    from load_bootstrap_env import cleanup_bootstrap_file
                    if cleanup_bootstrap_file():
                        print("[BOOTSTRAP] SUCCESS: Temporary bootstrap file cleaned up")
                except Exception as e:
                    print(f"[BOOTSTRAP] WARNING: Could not clean up bootstrap file: {e}")
                    
            else:
                print("[BOOTSTRAP] WARNING: Partial bootstrap - configuration downloaded but database sync failed")
            return True
        else:
            print("[BOOTSTRAP] ERROR: Bootstrap failed - no configuration available")
            return False
            
    except ImportError as e:
        print(f"[BOOTSTRAP] Missing required packages: {e}")
        return False
    except Exception as e:
        print(f"[BOOTSTRAP] Bootstrap error: {e}")
        return False

def attempt_database_sync():
    """
    Attempt to download and import database from online server.
    Returns True if successful, False otherwise.
    """
    try:
        import requests
        import sqlite3
        import json
        from pathlib import Path
        
        # Get sync credentials from environment (now loaded from bootstrap)
        sync_url = os.environ.get('SYNC_URL') or os.environ.get('AMRS_ONLINE_URL')
        sync_username = os.environ.get('SYNC_USERNAME') or os.environ.get('AMRS_ADMIN_USERNAME')
        sync_password = os.environ.get('AMRS_ADMIN_PASSWORD')
        
        if not all([sync_url, sync_username, sync_password]):
            print("[SYNC] Missing sync credentials - skipping database sync")
            return False
        
        # Clean up URL
        clean_url = sync_url.rstrip('/')
        if clean_url.endswith('/api'):
            clean_url = clean_url[:-4]
        
        print(f"[SYNC] Downloading database from: {clean_url}")
        
        # Create session and login
        session = requests.Session()
        
        # Try to login
        login_resp = session.post(f"{clean_url}/login", data={
            'username': sync_username,
            'password': sync_password
        }, timeout=30)
        
        if login_resp.status_code != 200:
            print(f"[SYNC] Login failed: {login_resp.status_code}")
            return False
        
        # Download sync data
        data_resp = session.get(f"{clean_url}/api/sync/data", timeout=60)
        if data_resp.status_code != 200:
            print(f"[SYNC] Data download failed: {data_resp.status_code}")
            return False
        
        sync_data = data_resp.json()
        print(f"[SYNC] Downloaded data: {list(sync_data.keys())}")
        
        # Get secure database path
        db_path = get_secure_database_path()
        print(f"[SYNC] Importing to secure database: {db_path}")
        
        # Import data into secure database
        import_success = import_sync_data_to_database(sync_data, db_path)
        
        if import_success:
            # Ensure audit tasks have machine associations for proper UI display
            ensure_audit_task_machine_associations(db_path)
            
            # Update the app to use the secure database
            update_database_configuration(db_path)
            print("[SYNC] SUCCESS: Database sync completed successfully")
            return True
        else:
            print("[SYNC] ERROR: Database import failed")
            return False
            
    except Exception as e:
        print(f"[SYNC] Database sync error: {e}")
        return False

def get_secure_database_path():
    """Get platform-appropriate secure location for database storage."""
    import platform
    from pathlib import Path
    
    os_name = platform.system().lower()
    
    if os_name == "windows":
        # Windows: Use %APPDATA%\AMRS_PM\
        base_path = Path(os.environ.get('APPDATA', '~')).expanduser()
        secure_dir = base_path / "AMRS_PM"
    elif os_name == "darwin":  # macOS
        # macOS: Use ~/Library/Application Support/AMRS_PM/
        base_path = Path.home() / "Library" / "Application Support"
        secure_dir = base_path / "AMRS_PM"
    else:  # Linux and others
        # Linux: Use ~/.local/share/AMRS_PM/
        base_path = Path.home() / ".local" / "share"
        secure_dir = base_path / "AMRS_PM"
    
    # Create directory if it doesn't exist
    secure_dir.mkdir(parents=True, exist_ok=True)
    
    db_path = secure_dir / "maintenance_secure.db"
    print(f"[STORAGE] Secure database location: {db_path}")
    
    return str(db_path)

def import_sync_data_to_database(sync_data, db_path):
    """Import downloaded sync data into the secure database."""
    try:
        import sqlite3
        
        # Connect to secure database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist (basic schema)
        create_basic_schema(cursor)
        
        # Import data
        tables_imported = 0
        
        # Import roles first (they're referenced by users)
        if 'roles' in sync_data:
            roles = sync_data['roles']
            for role in roles:
                # Fix datetime formats before importing
                role = fix_datetime_fields_in_record(role, ['created_at', 'updated_at'])
                cursor.execute('''
                INSERT OR REPLACE INTO roles (id, name, description, permissions, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    role['id'], role['name'], role['description'], 
                    role['permissions'], role['created_at'], role['updated_at']
                ))
            print(f"[SYNC] Imported {len(roles)} roles with datetime format fix")
            tables_imported += 1
        
        # Import users
        if 'users' in sync_data:
            users = sync_data['users']
            for user in users:
                # Fix datetime formats before importing
                user = fix_datetime_fields_in_record(user, ['created_at', 'updated_at', 'last_login', 'reset_token_expiration', 'remember_token_expiration'])
                
                # CORRECT APPROACH: Server should send plain text usernames/emails with correct hashes
                # The offline system should:
                # 1. Receive plain text username/email from server
                # 2. Use the hash provided by server (computed from plain text)
                # 3. Encrypt the username/email locally for storage security
                
                username_value = user['username']  # Should be plain text from server
                email_value = user['email']        # Should be plain text from server
                
                # Use the hashes provided by the server (these should be computed from plain text)
                # This allows login with plain text username to work correctly
                username_hash = user.get('username_hash')
                email_hash = user.get('email_hash')
                
                # If server didn't provide hashes, compute them from the plain text values
                if not username_hash and username_value:
                    username_hash = hash_value(username_value)
                    print(f"[SYNC] User {user['id']}: computed username hash from plain text")
                
                if not email_hash and email_value:
                    email_hash = hash_value(email_value)
                    print(f"[SYNC] User {user['id']}: computed email hash from plain text")
                
                # For offline storage security, encrypt the plain text username/email locally
                # This ensures the database doesn't store plain text credentials
                try:
                    from models import encrypt_value
                    encrypted_username = encrypt_value(username_value) if username_value else username_value
                    encrypted_email = encrypt_value(email_value) if email_value else email_value
                    print(f"[SYNC] User {user['id']}: encrypted username/email for secure local storage")
                    print(f"[SYNC] User {user['id']}: preserved server hashes - username_hash: {username_hash[:16]}..., email_hash: {email_hash[:16]}...")
                except Exception as e:
                    print(f"[SYNC] User {user['id']}: encryption failed, storing as plain text: {e}")
                    encrypted_username = username_value
                    encrypted_email = email_value
                
                cursor.execute('''
                INSERT OR REPLACE INTO users 
                (id, username, email, password_hash, full_name, active, is_admin, role_id, 
                 created_at, updated_at, username_hash, email_hash, remember_token, 
                 remember_token_expiration, remember_enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user['id'], encrypted_username, encrypted_email, user['password_hash'],
                    user.get('full_name'), user['active'], user['is_admin'], user['role_id'],
                    user['created_at'], user['updated_at'], username_hash,
                    email_hash, user.get('remember_token'),
                    user.get('remember_token_expiration'), user.get('remember_enabled', False)
                ))
            print(f"[SYNC] Imported {len(users)} users with correct plain-text hash handling")
            tables_imported += 1
        
        # Import other tables if present, now including audit_task_completions
        for table_name in ['sites', 'machines', 'parts', 'maintenance_records', 'audit_tasks', 'audit_task_completions']:
            if table_name in sync_data:
                records = sync_data[table_name]
                if table_name == 'sites':
                    for site in records:
                        cursor.execute('''
                        INSERT OR REPLACE INTO sites (id, name, location, contact_email, enable_notifications, notification_threshold, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            site['id'], site['name'], site.get('location'), site.get('contact_email'),
                            site.get('enable_notifications', True), site.get('notification_threshold', 30),
                            site.get('created_at'), site.get('updated_at')
                        ))
                elif table_name == 'machines':
                    for machine in records:
                        cursor.execute('''
                        INSERT OR REPLACE INTO machines (id, name, model, serial_number, machine_number, site_id, decommissioned, decommissioned_date, decommissioned_by, decommissioned_reason, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            machine['id'], machine['name'], machine.get('model'), machine.get('serial_number'),
                            machine.get('machine_number'), machine['site_id'], machine.get('decommissioned', False),
                            machine.get('decommissioned_date'), machine.get('decommissioned_by'), machine.get('decommissioned_reason'),
                            machine.get('created_at'), machine.get('updated_at')
                        ))
                elif table_name == 'parts':
                    for part in records:
                        cursor.execute('''
                        INSERT OR REPLACE INTO parts (id, name, description, machine_id, maintenance_frequency, maintenance_unit, last_maintenance, next_maintenance, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            part['id'], part['name'], part.get('description'), part['machine_id'],
                            part.get('maintenance_frequency'), part.get('maintenance_unit'),
                            part.get('last_maintenance'), part.get('next_maintenance'),
                            part.get('created_at'), part.get('updated_at')
                        ))
                elif table_name == 'audit_tasks':
                    for task in records:
                        cursor.execute('''
                        INSERT OR REPLACE INTO audit_tasks (id, name, description, site_id, created_by, interval, custom_interval_days, color, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            task['id'], task['name'], task.get('description'), task['site_id'],
                            task.get('created_by'), task.get('interval'), task.get('custom_interval_days'),
                            task.get('color'), task.get('created_at'), task.get('updated_at')
                        ))
                elif table_name == 'maintenance_records':
                    for record in records:
                        cursor.execute('''
                        INSERT OR REPLACE INTO maintenance_records (id, machine_id, part_id, user_id, maintenance_type, description, date, performed_by, status, notes, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            record['id'], record.get('machine_id'), record.get('part_id'), record.get('user_id'),
                            record.get('maintenance_type'), record.get('description'), record.get('date'),
                            record.get('performed_by'), record.get('status'), record.get('notes'),
                            record.get('created_at'), record.get('updated_at')
                        ))
                elif table_name == 'audit_task_completions':
                    for completion in records:
                        cursor.execute('''
                        INSERT OR REPLACE INTO audit_task_completions (id, audit_task_id, machine_id, date, completed, completed_by, completed_at, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            completion['id'], completion['audit_task_id'], completion.get('machine_id'),
                            completion.get('date'), completion.get('completed', False), completion.get('completed_by'),
                            completion.get('completed_at'), completion.get('created_at'), completion.get('updated_at')
                        ))
                print(f"[SYNC] Imported {len(records)} {table_name}")
                tables_imported += 1
        
        # Import machine_audit_task associations (CRITICAL for proper audit task display)
        if 'machine_audit_task' in sync_data:
            associations = sync_data['machine_audit_task']
            for assoc in associations:
                cursor.execute('''
                INSERT OR REPLACE INTO machine_audit_task (machine_id, audit_task_id)
                VALUES (?, ?)
                ''', (assoc['machine_id'], assoc['audit_task_id']))
            print(f"[SYNC] Imported {len(associations)} machine_audit_task associations")
            tables_imported += 1
        else:
            print("[SYNC] WARNING: No machine_audit_task associations found in sync data - audit tasks may not display properly")
        
        # Run comprehensive datetime format fix after import to catch any remaining issues
        print("[SYNC] Running post-import datetime format fix...")
        fix_count = run_comprehensive_datetime_fix(cursor)
        if fix_count > 0:
            print(f"[SYNC] SUCCESS: Fixed {fix_count} additional datetime format issues")
        else:
            print("[SYNC] SUCCESS: No additional datetime format issues found")
        
        conn.commit()
        conn.close()
        
        print(f"[SYNC] Successfully imported {tables_imported} tables to secure database")
        return True
        
    except Exception as e:
        print(f"[SYNC] Import error: {e}")
        return False

def ensure_audit_task_machine_associations(db_path):
    """Ensure that the machine_audit_task table exists but only use server-provided associations.
    This function does NOT create fallback associations - it only uses data provided by the server."""
    try:
        import sqlite3
        
        # Connect to secure database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if machine_audit_task table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='machine_audit_task'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            # Create the machine_audit_task table structure only
            cursor.execute('''
            CREATE TABLE machine_audit_task (
                machine_id INTEGER NOT NULL,
                audit_task_id INTEGER NOT NULL,
                PRIMARY KEY (machine_id, audit_task_id),
                FOREIGN KEY (machine_id) REFERENCES machines (id),
                FOREIGN KEY (audit_task_id) REFERENCES audit_tasks (id)
            )
            ''')
            print("[AUDIT] Created machine_audit_task association table")
            conn.commit()
        
        # Check existing associations (only from server sync data)
        cursor.execute("SELECT COUNT(*) FROM machine_audit_task")
        existing_associations = cursor.fetchone()[0]
        
        if existing_associations > 0:
            print(f"[AUDIT] SUCCESS: Found {existing_associations} existing audit task-machine associations")
        else:
            print("[AUDIT] WARNING: No audit task-machine associations found from server sync")
            print("[AUDIT] Audit tasks will only be visible if the server provides explicit associations")
            print("[AUDIT] Contact your administrator to configure audit task assignments on the server")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"[AUDIT] Error checking audit task associations: {e}")
        return False

def create_audit_task_associations(audit_task_id, machine_ids):
    """Create explicit audit task-machine associations for a specific audit task.
    This is the controlled way to create associations on the server side.
    
    Args:
        audit_task_id: ID of the audit task
        machine_ids: List of machine IDs to associate with the audit task
    
    Returns:
        tuple: (success: bool, message: str, associations_created: int)
    """
    try:
        from sqlalchemy import text
        
        # Verify audit task exists
        audit_task = AuditTask.query.get(audit_task_id)
        if not audit_task:
            return False, f"Audit task {audit_task_id} not found", 0
        
        # Verify machines exist and get their details
        valid_machines = []
        for machine_id in machine_ids:
            machine = Machine.query.get(machine_id)
            if machine:
                valid_machines.append(machine)
            else:
                print(f"[AUDIT_ASSOC] Warning: Machine {machine_id} not found, skipping")
        
        if not valid_machines:
            return False, "No valid machines found", 0
        
        # Ensure machine_audit_task table exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if not inspector.has_table('machine_audit_task'):
            db.session.execute(text('''
            CREATE TABLE machine_audit_task (
                machine_id INTEGER NOT NULL,
                audit_task_id INTEGER NOT NULL,
                PRIMARY KEY (machine_id, audit_task_id),
                FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE,
                FOREIGN KEY (audit_task_id) REFERENCES audit_tasks(id) ON DELETE CASCADE
            )
            '''))
            db.session.commit()
        
        # Create associations
        associations_created = 0
        for machine in valid_machines:
            try:
                db.session.execute(text('''
                INSERT OR IGNORE INTO machine_audit_task (machine_id, audit_task_id)
                VALUES (:machine_id, :audit_task_id)
                '''), {'machine_id': machine.id, 'audit_task_id': audit_task_id})
                
                # Check if the association was actually created (not already existing)
                result = db.session.execute(text('''
                SELECT COUNT(*) FROM machine_audit_task 
                WHERE machine_id = :machine_id AND audit_task_id = :audit_task_id
                '''), {'machine_id': machine.id, 'audit_task_id': audit_task_id}).scalar()
                
                if result > 0:
                    associations_created += 1
                    print(f"[AUDIT_ASSOC] Associated audit task '{audit_task.name}' with machine '{machine.name}'")
                    
            except Exception as e:
                print(f"[AUDIT_ASSOC] Error associating machine {machine.name}: {e}")
        
        db.session.commit()
        
        message = f"Created {associations_created} audit task associations for '{audit_task.name}'"
        if associations_created < len(valid_machines):
            message += f" ({len(valid_machines) - associations_created} were already associated)"
            
        return True, message, associations_created
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error creating audit task associations: {str(e)}", 0

def remove_audit_task_associations(audit_task_id, machine_ids=None):
    """Remove audit task-machine associations.
    
    Args:
        audit_task_id: ID of the audit task
        machine_ids: List of machine IDs to remove associations for. If None, removes all associations for the audit task.
    
    Returns:
        tuple: (success: bool, message: str, associations_removed: int)
    """
    try:
        from sqlalchemy import text
        
        # Verify audit task exists
        audit_task = AuditTask.query.get(audit_task_id)
        if not audit_task:
            return False, f"Audit task {audit_task_id} not found", 0
        
        associations_removed = 0
        
        if machine_ids is None:
            # Remove all associations for this audit task
            result = db.session.execute(text('''
            DELETE FROM machine_audit_task WHERE audit_task_id = :audit_task_id
            '''), {'audit_task_id': audit_task_id})
            associations_removed = result.rowcount
            message = f"Removed all {associations_removed} associations for audit task '{audit_task.name}'"
        else:
            # Remove specific machine associations
            for machine_id in machine_ids:
                result = db.session.execute(text('''
                DELETE FROM machine_audit_task 
                WHERE audit_task_id = :audit_task_id AND machine_id = :machine_id
                '''), {'audit_task_id': audit_task_id, 'machine_id': machine_id})
                associations_removed += result.rowcount
            
            message = f"Removed {associations_removed} specific associations for audit task '{audit_task.name}'"
        
        db.session.commit()
        return True, message, associations_removed
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error removing audit task associations: {str(e)}", 0

def create_basic_schema(cursor):
    """Create basic database schema in the secure database."""
    schema_sql = [
        '''CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            permissions TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            active BOOLEAN DEFAULT 1,
            is_admin BOOLEAN DEFAULT 0,
            role_id INTEGER,
            last_login TIMESTAMP,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            reset_token TEXT,
            reset_token_expiration TIMESTAMP,
            username_hash TEXT,
            email_hash TEXT,
            remember_token TEXT,
            remember_token_expiration TIMESTAMP,
            remember_enabled BOOLEAN DEFAULT 0,
            notification_preferences TEXT,
            FOREIGN KEY (role_id) REFERENCES roles(id)
        )''',
        '''CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT,
            contact_email TEXT,
            enable_notifications BOOLEAN DEFAULT 1,
            notification_threshold INTEGER DEFAULT 30,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS machines (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            model TEXT,
            serial_number TEXT,
            machine_number TEXT,
            site_id INTEGER,
            decommissioned BOOLEAN DEFAULT 0,
            decommissioned_date TIMESTAMP,
            decommissioned_by TEXT,
            decommissioned_reason TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites(id)
        )''',
        '''CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            machine_id INTEGER,
            maintenance_frequency INTEGER,
            maintenance_unit TEXT,
            last_maintenance TIMESTAMP,
            next_maintenance TIMESTAMP,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (machine_id) REFERENCES machines(id)
        )''',
        '''CREATE TABLE IF NOT EXISTS audit_tasks (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            site_id INTEGER,
            created_by INTEGER,
            interval TEXT,
            custom_interval_days INTEGER,
            color TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )''',
        '''CREATE TABLE IF NOT EXISTS machine_audit_task (
            machine_id INTEGER NOT NULL,
            audit_task_id INTEGER NOT NULL,
            PRIMARY KEY (machine_id, audit_task_id),
            FOREIGN KEY (machine_id) REFERENCES machines(id),
            FOREIGN KEY (audit_task_id) REFERENCES audit_tasks(id)
        )''',
        '''CREATE TABLE IF NOT EXISTS maintenance_records (
            id INTEGER PRIMARY KEY,
            machine_id INTEGER,
            part_id INTEGER,
            user_id INTEGER,
            maintenance_type TEXT,
            description TEXT,
            date TIMESTAMP,
            performed_by TEXT,
            status TEXT,
            notes TEXT,
            comments TEXT,
            client_id INTEGER,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (machine_id) REFERENCES machines(id),
            FOREIGN KEY (part_id) REFERENCES parts(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''',
        '''CREATE TABLE IF NOT EXISTS audit_task_completions (
            id INTEGER PRIMARY KEY,
            audit_task_id INTEGER,
            machine_id INTEGER,
            date TIMESTAMP,
            completed BOOLEAN DEFAULT 0,
            completed_by INTEGER,
            completed_at TIMESTAMP,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (audit_task_id) REFERENCES audit_tasks(id),
            FOREIGN KEY (machine_id) REFERENCES machines(id),
            FOREIGN KEY (completed_by) REFERENCES users(id)
        )''',
        '''CREATE TABLE IF NOT EXISTS maintenance_files (
            id INTEGER PRIMARY KEY,
            maintenance_record_id INTEGER,
            filename TEXT,
            filedata BLOB,
            filepath TEXT,
            filetype TEXT,
            filesize INTEGER,
            thumbnail_path TEXT,
            uploaded_by INTEGER,
            uploaded_at TIMESTAMP,
            FOREIGN KEY (maintenance_record_id) REFERENCES maintenance_records(id),
            FOREIGN KEY (uploaded_by) REFERENCES users(id)
        )'''
    ]
    for sql in schema_sql:
        cursor.execute(sql)

def update_database_configuration(secure_db_path):
    """Update the application to use the secure database."""
    # Update the DATABASE_URL environment variable to point to the secure database
    os.environ['DATABASE_URL'] = f'sqlite:///{secure_db_path}'
    print(f"[CONFIG] Updated database configuration to use: {secure_db_path}")

def ensure_online_server_audit_associations():
    """Ensure the online server has the machine_audit_task table but only explicit associations.
    This function creates the table structure but does not automatically create associations."""
    try:
        # Only run for online servers
        from timezone_utils import is_offline_mode
        if is_offline_mode():
            return True
            
        print("[AUDIT_SYNC] Ensuring online server has audit task association table...")
        
        # Check if machine_audit_task table exists
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        
        if not inspector.has_table('machine_audit_task'):
            print("[AUDIT_SYNC] Creating machine_audit_task table on online server...")
            # Create the table using SQLAlchemy
            db.session.execute(text('''
            CREATE TABLE machine_audit_task (
                machine_id INTEGER NOT NULL,
                audit_task_id INTEGER NOT NULL,
                PRIMARY KEY (machine_id, audit_task_id),
                FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE,
                FOREIGN KEY (audit_task_id) REFERENCES audit_tasks(id) ON DELETE CASCADE
            )
            '''))
            db.session.commit()
            print("[AUDIT_SYNC] SUCCESS: Created machine_audit_task table")
        
        # Check if there are any associations (only report, don't create)
        result = db.session.execute(text('SELECT COUNT(*) FROM machine_audit_task')).scalar()
        
        if result == 0:
            print("[AUDIT_SYNC] WARNING: No audit task-machine associations configured")
            print("[AUDIT_SYNC] Administrators should create explicit audit task assignments:")
            print("[AUDIT_SYNC] 1. Use the admin interface to assign audit tasks to specific machines")
            print("[AUDIT_SYNC] 2. Or run manual SQL to create associations: INSERT INTO machine_audit_task (machine_id, audit_task_id) VALUES (machine_id, task_id)")
            print("[AUDIT_SYNC] Without explicit associations, audit tasks will not appear on offline clients")
        else:
            print(f"[AUDIT_SYNC] SUCCESS: Found {result} configured audit task-machine associations")
            print("[AUDIT_SYNC] These associations will be exported to offline clients via sync")
        
        return True
        
    except Exception as e:
        print(f"[AUDIT_SYNC] Error checking online server audit associations: {e}")
        return False

def verify_bootstrap_success():
    """Verify that bootstrap was successful by checking database and credentials."""
    try:
        import keyring
        
        service = get_secure_storage_service()
        
        # Check essential credentials
        essential_keys = ['AMRS_ADMIN_USERNAME', 'AMRS_ADMIN_PASSWORD', 'USER_FIELD_ENCRYPTION_KEY']
        missing = []
        
        for key in essential_keys:
            if not keyring.get_password(service, key):
                missing.append(key)
        
        if missing:
            print(f"[VERIFY] ERROR: Missing essential credentials: {missing}")
            return False
        
        # Check database
        db_path = get_secure_database_path()
        if not os.path.exists(db_path):
            print(f"[VERIFY] ERROR: Secure database not found: {db_path}")
            return False
        
        # Check if database has users
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE active = 1")
        user_count = cursor.fetchone()[0]
        conn.close()
        
        if user_count == 0:
            print("[VERIFY] ERROR: No active users in secure database")
            return False
        
        print(f"[VERIFY] SUCCESS: Bootstrap verification passed - {user_count} users available")
        return True
        
    except Exception as e:
        print(f"[VERIFY] Bootstrap verification error: {e}")
        return False

# NOTE: Bootstrap will be called later in initialize_database_and_bootstrap() function
# This prevents double execution of the bootstrap process

# Import enhanced sync utilities
from datetime import datetime, timedelta, date
from timezone_utils import get_timezone_aware_now, get_eastern_date, is_online_server
from sync_utils_enhanced import (
    add_to_sync_queue_enhanced, 
    trigger_manual_sync, 
    start_enhanced_sync_worker,
    cleanup_expired_sync_queue_enhanced,
    should_trigger_sync
)

# --- Background Sync Worker ---
# --- Register secure secrets bootstrap endpoint after app is created ---
# (Keep all previous imports and code here)
import requests
import threading
import time

# NOTE: Bootstrap trigger moved to initialize_database_and_bootstrap() function
# This prevents double execution and ensures proper app context

def upload_pending_sync_queue():
    """Upload all pending sync_queue items to the server and mark them as synced if successful."""
    from sqlalchemy import text as sa_text
    with app.app_context():
        pending_items = db.session.execute(sa_text("SELECT id, table_name, record_id, operation, payload FROM sync_queue WHERE status = 'pending' ORDER BY created_at ASC")).fetchall()
        if not pending_items:
            print("[SYNC] No pending changes to upload.")
            return
        print(f"[SYNC] Uploading {len(pending_items)} pending changes from sync_queue...")
        # Prepare upload payload grouped by table
        upload_payload = {}
        for item in pending_items:
            table = item[1]  # table_name
            if table not in upload_payload:
                upload_payload[table] = []
            try:
                record = _json.loads(item[4])  # payload
                record['__operation__'] = item[3]  # operation
                record['__sync_queue_id__'] = item[0]  # id
                upload_payload[table].append(record)
            except Exception as e:
                print(f"[SYNC] Error parsing payload for sync_queue id {item[0]}: {e}")
                continue
        # Upload to server
        online_url = os.environ.get('AMRS_ONLINE_URL')
        admin_username = os.environ.get('AMRS_ADMIN_USERNAME')
        admin_password = os.environ.get('AMRS_ADMIN_PASSWORD')
        if not online_url or not admin_username or not admin_password:
            print("[SYNC] Missing AMRS_ONLINE_URL or AMRS_ADMIN_USERNAME/AMRS_ADMIN_PASSWORD; cannot upload changes.")
            return
        clean_url = online_url.strip('"\'').rstrip('/')
        if clean_url.endswith('/api'):
            clean_url = clean_url[:-4]
        try:
            resp = requests.post(
                f"{clean_url}/api/sync/data",
                json=upload_payload,
                headers={"Content-Type": "application/json"},
                auth=(admin_username, admin_password),
                timeout=30
            )
            if resp.status_code == 200:
                ids = [item[0] for item in pending_items]
                # Fix SQLite IN clause syntax - use named parameters
                if ids:
                    placeholders = ','.join([f':id_{i}' for i in range(len(ids))])
                    query = f"UPDATE sync_queue SET status = 'synced', synced_at = :now WHERE id IN ({placeholders})"
                    params = {'now': datetime.utcnow()}
                    for i, id_val in enumerate(ids):
                        params[f'id_{i}'] = id_val
                    db.session.execute(sa_text(query), params)
                    db.session.commit()
                    print(f"[SYNC] Successfully uploaded and marked {len(ids)} sync_queue items as synced.")
            else:
                print(f"[SYNC] Upload failed: {resp.status_code} {resp.text}")
                # Don't mark items as failed immediately - they'll be retried later
        except requests.exceptions.ConnectionError as e:
            print(f"[SYNC] Connection error during upload (desktop clients may be offline): {e}")
        except requests.exceptions.Timeout as e:
            print(f"[SYNC] Timeout during upload: {e}")
        except Exception as e:
            print(f"[SYNC] Exception during upload: {e}")
            # For any other exception, ensure we don't crash the sync worker

# Note: Enhanced sync worker will be started after app initialization


# --- SocketIO event for triggering sync ---
# (Moved below app creation for correct initialization)
# --- Ensure users.username and users.email columns are large enough on Render (PostgreSQL) ---
def ensure_large_user_columns():
    """Ensure users.username and users.email columns are at least VARCHAR(1024) on PostgreSQL."""
    try:
        from sqlalchemy import text
        engine = db.engine
        with engine.connect() as conn:
            # Check column sizes
            result = conn.execute(text("""
                SELECT column_name, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = 'users' AND column_name IN ('username', 'email')
            """))
            needs_update = []
            for row in result:
                if row['character_maximum_length'] is not None and row['character_maximum_length'] < 1024:
                    needs_update.append(row['column_name'])
            for col in needs_update:
                print(f"[SCHEMA] Altering users.{col} to VARCHAR(1024)...")
                try:
                    conn.execute(text(f"ALTER TABLE users ALTER COLUMN {col} TYPE VARCHAR(1024);"))
                    print(f"[SCHEMA] users.{col} column updated to VARCHAR(1024)")
                except Exception as e:
                    print(f"[SCHEMA] Error updating users.{col}: {e}")
    except Exception as e:
        print(f"[SCHEMA] Error ensuring large user columns: {e}")

# --- Utility: Add change to sync_queue ---
from sqlalchemy.exc import SQLAlchemyError

def fix_postgresql_sequence(table_name):
    """
    Fix PostgreSQL sequence for a table to avoid ID conflicts.
    This ensures the next auto-generated ID will be higher than any existing IDs.
    """
    try:
        # Only run on PostgreSQL (not SQLite)
        if 'postgresql' in str(db.engine.url).lower():
            from sqlalchemy import text
            # Get the maximum ID from the table
            result = db.session.execute(text(f"SELECT MAX(id) FROM {table_name}")).scalar()
            if result:
                # Set sequence to max_id + 1
                sequence_name = f"{table_name}_id_seq"
                db.session.execute(text(f"SELECT setval('{sequence_name}', {result})"))
                db.session.commit()
                print(f"[SEQUENCE] Fixed {sequence_name} to start from {result + 1}")
    except Exception as e:
        print(f"[SEQUENCE] Error fixing sequence for {table_name}: {e}")
        # Don't let sequence errors break the main functionality
        pass

def check_desktop_clients_available():
    """
    Check if desktop client sync is configured and working.
    Returns True if sync configuration is available, False otherwise.
    This prevents immediate sync attempts when sync is not properly configured.
    """
    try:
        # Check if sync environment variables are configured
        online_url = os.environ.get('AMRS_ONLINE_URL')
        admin_username = os.environ.get('AMRS_ADMIN_USERNAME')
        admin_password = os.environ.get('AMRS_ADMIN_PASSWORD')
        
        # If sync is not configured, don't attempt immediate sync
        if not online_url or not admin_username or not admin_password:
            return False
            
        # Always return True for now - let the background worker handle failures gracefully
        # This ensures items are queued properly regardless of current connectivity
        return True
        
    except Exception as e:
        print(f"[SYNC] Error checking desktop client availability: {e}")
        return False

def notify_desktop_clients_of_changes():
    """
    Notify desktop clients that changes are available for download.
    This could be expanded to use webhooks, push notifications, etc.
    """
    try:
        print("[SYNC] Audit task completion changes available for desktop client sync")
        notify_clients_of_sync()
    except Exception as e:
        print(f"[SYNC] Error notifying desktop clients: {e}")

def add_to_sync_queue(table_name, record_id, operation, payload_dict):
    """
    DEPRECATED: Use add_to_sync_queue_enhanced instead.
    This function is kept for compatibility but redirects to the enhanced version.
    """
    try:
        # Redirect to enhanced sync queue to avoid duplicate systems
        add_to_sync_queue_enhanced(table_name, record_id, operation, payload_dict, immediate_sync=False)
        print(f"[SYNC_QUEUE] Redirected {operation} for {table_name}:{record_id} to enhanced sync queue.")
    except Exception as e:
        print(f"[SYNC_QUEUE] Error redirecting to enhanced sync: {e}")
        # Don't fail, just log the error
        print(f"[SYNC_QUEUE] Error adding to sync_queue: {e}")
# --- Sync Queue Cleanup: Remove records older than 168 hours (7 days) ---
def cleanup_expired_sync_queue():
    from sqlalchemy import text as sa_text
    from datetime import datetime, timedelta
    """Delete sync_queue records older than 168 hours (7 days)."""
    try:
        cutoff = datetime.utcnow() - timedelta(hours=168)
        # Works for both SQLite and PostgreSQL
        db.session.execute(sa_text("""
            DELETE FROM sync_queue WHERE created_at < :cutoff
        """), {"cutoff": cutoff})
        db.session.commit()
        print(f"[SYNC_QUEUE] Cleaned up expired sync_queue records older than {cutoff}.")
    except Exception as e:
        print(f"[SYNC_QUEUE] Error cleaning up expired sync_queue records: {e}")

# Whitelist allowed table and column names for schema changes
ALLOWED_TABLES = {'users', 'roles', 'sites', 'machines', 'parts', 'maintenance_records', 'audit_tasks', 'audit_task_completions', 'machine_audit_task'}
ALLOWED_COLUMNS = {
    'users': {'last_login', 'reset_token', 'reset_token_expiration', 'created_at', 'updated_at'},
    'roles': {'created_at', 'updated_at'},
    'sites': {'created_at', 'updated_at'},
    'machines': {'created_at', 'updated_at'},
    'parts': {'created_at', 'updated_at'},
    'maintenance_records': {'created_at', 'updated_at', 'client_id', 'machine_id', 'maintenance_type', 'description', 'performed_by', 'status', 'notes'},
    'audit_tasks': {'created_at', 'updated_at', 'interval', 'custom_interval_days'},
    'audit_task_completions': {'created_at', 'updated_at'},
    'machine_audit_task': {'audit_task_id', 'machine_id'}
}

# --- Ensure sync columns exist in SQLite for offline mode ---
def ensure_sync_columns_sqlite():
    """Ensure all tables in SQLite have created_at, updated_at, deleted_at columns."""
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    sync_columns = [
        ('created_at', 'TIMESTAMP'),
        ('updated_at', 'TIMESTAMP'),
        ('deleted_at', 'TIMESTAMP')
    ]
    for table in ALLOWED_TABLES:
        if inspector.has_table(table):
            existing_columns = {col['name'] for col in inspector.get_columns(table)}
            with db.engine.connect() as conn:
                for col_name, col_type in sync_columns:
                    if col_name not in existing_columns:
                        print(f"[SYNC] Adding {col_name} to {table} (SQLite)...")
                        # SQLite does not support IF NOT EXISTS for ADD COLUMN
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
    # Switch SQLAlchemy to use the secure database after bootstrap
    print(f"[CONFIG] Updating SQLAlchemy database URI to: {secure_db_path}")
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{secure_db_path}"
    # Re-initialize the db object with the new URI
    try:
        db.engine.dispose()
        db.session.remove()
        db.init_app(app)
        print(f"[CONFIG] SQLAlchemy re-initialized with new database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        # Run auto-migration/schema validation on the secure database
        with app.app_context():
            print("[CONFIG] Running auto-migration/schema validation on secure database...")
            try:
                run_auto_migration()
                print("[CONFIG] Auto-migration/schema validation completed for secure database.")
            except Exception as migrate_exc:
                print(f"[CONFIG] Auto-migration/schema validation failed: {migrate_exc}")
    except Exception as e:
        print(f"[CONFIG] Error re-initializing SQLAlchemy: {e}")
    # Ensure sync_queue table has synced_at column
    if inspector.has_table('sync_queue'):
        existing_columns = {col['name'] for col in inspector.get_columns('sync_queue')}
        if 'synced_at' not in existing_columns:
            print("[SYNC] Adding synced_at to sync_queue (SQLite)...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE sync_queue ADD COLUMN synced_at TIMESTAMP"))
                conn.commit()
    
    print("[SYNC] Sync columns ensured in SQLite.")


# --- Flask-SocketIO for Real-Time Sync ---
from flask_socketio import SocketIO, emit

# Standard library imports
import sys
import random
import string
import logging
import signal
import argparse
import calendar
from functools import wraps
import traceback
from io import BytesIO

# --- TEST DB PATCH: Force in-memory SQLite for pytest runs ---
if any('pytest' in arg for arg in sys.argv):
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

# Third-party imports
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort, current_app, send_file
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_mail import Mail, Message
from sqlalchemy import or_, text
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import secrets
from sqlalchemy import inspect
import smtplib
from jinja2 import Environment, FileSystemLoader
import csv
import requests

# Local imports
from models import db, User, Role, Site, Machine, Part, MaintenanceRecord, AuditTask, AuditTaskCompletion, MaintenanceFile, encrypt_value, hash_value
from auto_migrate import run_auto_migration

# Patch is_admin property to User class immediately after import
def is_admin(self):
    """Add is_admin property to User class for template compatibility (read-only)"""
    return is_admin_user(self)
User.is_admin = property(is_admin)

# Then patch the Site class directly as a monkey patch
# This must be outside any function to execute immediately
def parts_status(self, current_date=None):
    """
    Get maintenance status of all parts at this site
    Returns dictionary with 'overdue' and 'due_soon' lists
    """
    if current_date is None:
        current_date = datetime.now()
    
    overdue = []
    due_soon = []
    threshold = self.notification_threshold or 30  # Default to 30 days if not set
    
    # Loop through all machines at this site
    for machine in self.machines:
        for part in machine.parts:
            # Skip parts without next_maintenance date
            if not part.next_maintenance:
                continue
                
            days_until = (part.next_maintenance - current_date).days
            
            # Skip if days_until is None (shouldn't happen but safety check)
            if days_until is None:
                continue
            
            # Overdue parts
            if days_until < 0:
                overdue.append(part)
            # Due soon parts within threshold
            elif days_until <= threshold:
                due_soon.append(part)
    
    return {
        'overdue': overdue,
        'due_soon': due_soon
    }

# Update the function assignments
Site.parts_status = parts_status
Site.get_parts_status = parts_status

# Define PostgreSQL database URI from environment only
POSTGRESQL_DATABASE_URI = os.environ.get('DATABASE_URL')

# Verify persistent storage
def check_persistent_storage():
    """Verify persistent storage is working properly"""
    # Since we're using PostgreSQL now, we can simplify this check
    # We'll just ensure the DATABASE_URL environment variable is set
    if os.environ.get('DATABASE_URL'):
        print(f"[APP] Using database URL from environment: {os.environ.get('DATABASE_URL')}")
    else:
        print(f"[APP] Using default PostgreSQL database")
    return True

# NOTE: Persistent storage check moved to initialize_database_and_bootstrap() function
# This prevents module-level database URL logging that conflicts with proper database configuration




# Initialize Flask app
app = Flask(__name__, instance_relative_config=True)

# Register SQLAlchemy with Flask app after config
from models import db

# NOTE: Database configuration will be handled later in a single consolidated section
# NOTE: Database initialization and auto-migration will be handled later in consolidated section

# Now import the rest of the models and other local modules
from models import User, Role, Site, Machine, Part, MaintenanceRecord, AuditTask, AuditTaskCompletion, MaintenanceFile, encrypt_value, hash_value
from auto_migrate import run_auto_migration

# --- Register secure secrets bootstrap endpoint after app is created ---

# --- Security Event Logger import ---
from security_event_logger import log_security_event

@app.route('/api/bootstrap-secrets', methods=['POST'])
def bootstrap_secrets():
    """Return essential sync secrets for desktop bootstrap, protected by a bootstrap token."""
    expected_token = os.environ.get('BOOTSTRAP_SECRET_TOKEN')
    auth_header = request.headers.get('Authorization', '')
    remote_addr = request.remote_addr or request.headers.get('X-Forwarded-For', 'unknown')
    
    if not expected_token or auth_header != f"Bearer {expected_token}":
        log_security_event(
            event_type="bootstrap_secrets_denied",
            details=f"Denied bootstrap secrets from {remote_addr}: invalid or missing token",
            is_critical=True
        )
        abort(403)
        
    log_security_event(
        event_type="bootstrap_secrets_success", 
        details=f"Bootstrap secrets successfully retrieved from {remote_addr}",
        is_critical=False
    )
    
    # Only return the secrets needed for offline sync/bootstrap
    return jsonify({
        "USER_FIELD_ENCRYPTION_KEY": os.environ.get("USER_FIELD_ENCRYPTION_KEY"),
        "RENDER_EXTERNAL_URL": os.environ.get("RENDER_EXTERNAL_URL"),
        "SYNC_URL": os.environ.get("SYNC_URL"),
        "SYNC_USERNAME": os.environ.get("SYNC_USERNAME"),
        "AMRS_ONLINE_URL": os.environ.get("AMRS_ONLINE_URL"),
        "AMRS_ADMIN_USERNAME": os.environ.get("AMRS_ADMIN_USERNAME"),
        "AMRS_ADMIN_PASSWORD": os.environ.get("AMRS_ADMIN_PASSWORD"),
    })


# Initialize SocketIO after app is created
import os
from flask_socketio import SocketIO, emit, disconnect
from flask import request

# Determine async mode based on environment and availability
def get_async_mode():
    """Determine the best async mode based on environment and available packages"""
    # Check if we're in production (Render)
    if os.environ.get('RENDER'):
        try:
            import eventlet
            return 'eventlet'
        except ImportError:
            try:
                import gevent
                return 'gevent'
            except ImportError:
                return 'threading'
    else:
        # Local development - use threading for compatibility
        return 'threading'

async_mode = get_async_mode()
print(f"[SocketIO] Using async_mode: {async_mode}")

# Memory-optimized SocketIO configuration with fallback handling
# Dynamic CORS configuration based on environment
cors_origins = [
    "http://localhost:10000", 
    "http://127.0.0.1:10000",
    "http://localhost:5000", 
    "http://127.0.0.1:5000"
]

# Add production URL if running on Render
render_external_url = os.environ.get('RENDER_EXTERNAL_URL')
if render_external_url:
    cors_origins.append(render_external_url)
    print(f"[SocketIO] Added Render URL to CORS: {render_external_url}")

# For development/testing, also allow common patterns
if os.environ.get('FLASK_ENV') == 'development' or os.environ.get('DEBUG'):
    cors_origins.extend([
        "https://amrs-maintenance.onrender.com",
        "https://amrs-pm-test.onrender.com",
        "*"  # Allow all origins in development (use with caution)
    ])
    print("[SocketIO] Added development CORS origins")

print(f"[SocketIO] CORS allowed origins: {cors_origins}")

try:
    socketio = SocketIO(
        app, 
        cors_allowed_origins=cors_origins,
        async_mode=async_mode,
        ping_timeout=120,  # Increased from 60 to handle slower connections
        ping_interval=60,  # Increased from 25 to reduce network traffic
        max_http_buffer_size=1024*1024,  # 1MB max message size
        allow_upgrades=True,
        transports=['polling', 'websocket'],  # Prefer polling first, then upgrade
        engineio_logger=False,  # Reduce verbose logging
        socketio_logger=False   # Reduce verbose logging
    )
    print(f"[SocketIO] Successfully initialized with {async_mode} mode")
except Exception as e:
    print(f"[SocketIO ERROR] Failed to initialize with {async_mode}: {e}")
    # Fallback to basic threading mode with conservative settings
    socketio = SocketIO(
        app,
        cors_allowed_origins=cors_origins,
        async_mode='threading',
        ping_timeout=120,
        ping_interval=60,
        transports=['polling'],  # Only use polling in fallback mode
        engineio_logger=False,
        socketio_logger=False
    )
    print("[SocketIO] Fallback to basic threading mode")

# Connection tracking for memory management
active_connections = set()

# --- SocketIO event handlers with robust error handling ---
@socketio.on('connect')
def handle_connect():
    try:
        client_id = request.sid
        active_connections.add(client_id)
        # Get client info for better debugging
        client_info = {
            'ip': request.environ.get('REMOTE_ADDR', 'unknown'),
            'user_agent': request.environ.get('HTTP_USER_AGENT', 'unknown')[:100]
        }
        print(f"[SocketIO] Client connected: {client_id} from {client_info['ip']} (Total: {len(active_connections)})")
        
        # For offline clients, trigger sync only when needed (not on every page load)
        from timezone_utils import is_online_server
        if not is_online_server():
            # Check if we should trigger sync (avoids constant syncing)
            if should_trigger_sync():
                print(f"[SocketIO] Offline client - sync needed, performing reconnection sync")
                
                # Import sync functions
                from sync_utils_enhanced import trigger_reconnection_sync
                
                # Trigger sync in background to avoid blocking page load
                try:
                    sync_result = trigger_reconnection_sync()
                    
                    if sync_result.get("status") == "success":
                        total_changes = sync_result.get("total_changes", 0)
                        if total_changes > 0:
                            print(f"[SocketIO] Reconnection sync successful: {total_changes} changes processed")
                    elif sync_result.get("status") == "no_changes":
                        print(f"[SocketIO] Reconnection sync: No changes needed")
                    else:
                        print(f"[SocketIO] Reconnection sync result: {sync_result.get('status')}")
                except Exception as e:
                    print(f"[SocketIO] Warning: Background sync failed: {e}")
            else:
                print(f"[SocketIO] Offline client - sync not needed (recent sync completed)")
        else:
            print(f"[SocketIO] Online client connected - no sync needed")
        
        emit('connected', {
            'message': 'Connected to AMRS sync server', 
            'client_id': client_id,
            'server_time': str(datetime.utcnow())
        })
    except Exception as e:
        print(f"[SocketIO ERROR] Error in connect handler: {e}")

@socketio.on('disconnect')
def handle_disconnect(reason=None):
    try:
        client_id = request.sid
        active_connections.discard(client_id)
        disconnect_reason = reason or 'unknown'
        print(f"[SocketIO] Client disconnected: {client_id} (reason: {disconnect_reason}) (Total: {len(active_connections)})")
    except Exception as e:
        print(f"[SocketIO ERROR] Error in disconnect handler: {e}")

@socketio.on('ping')
def handle_ping():
    """Handle client ping to maintain connection health"""
    try:
        emit('pong', {'timestamp': str(datetime.utcnow())})
    except Exception as e:
        print(f"[SocketIO ERROR] Error in ping handler: {e}")

@socketio.on('connect_error')
def handle_connect_error(data):
    """Handle connection errors"""
    print(f"[SocketIO] Connection error: {data}")

@socketio.on_error_default
def default_error_handler(e):
    """Handle any unhandled SocketIO errors"""
    try:
        print(f"[SocketIO ERROR] Unhandled error: {e}")
        # Log additional context
        import traceback
        print(f"[SocketIO ERROR] Traceback: {traceback.format_exc()}")
    except Exception as log_error:
        print(f"[SocketIO ERROR] Failed to log error: {log_error}")
    # Don't re-raise to prevent crashes

# Function to emit sync event to all clients with robust error handling
def notify_clients_of_sync():
    if not active_connections:
        print("[SocketIO] No active connections, skipping sync notification")
        return
    
    print(f"[SocketIO] Emitting sync event to {len(active_connections)} clients...")
    try:
        # Emit with acknowledgment to detect failed connections
        socketio.emit('sync', {
            'message': 'Data changed, please sync.', 
            'timestamp': str(datetime.utcnow()),
            'server_id': os.environ.get('RENDER_SERVICE_NAME', 'local-server')
        })
        print(f"[SocketIO] Sync event sent successfully")
    except Exception as e:
        print(f"[SocketIO ERROR] Failed to emit sync event: {e}")
        # Don't clear all connections immediately - let cleanup handle it
        print(f"[SocketIO] Will clean up stale connections in next cleanup cycle")

# Improved cleanup function with better error handling
def cleanup_stale_connections():
    """Remove connections that are no longer active"""
    if not active_connections:
        return
        
    stale_count = 0
    for client_id in list(active_connections):
        try:
            # Try to emit a small test message to verify connection
            socketio.emit('heartbeat', {'test': True}, room=client_id, timeout=5)
        except Exception:
            active_connections.discard(client_id)
            stale_count += 1
    
    if stale_count > 0:
        print(f"[SocketIO] Cleaned up {stale_count} stale connections")

# Background cleanup task
import threading
import time

def background_cleanup():
    """Background thread to periodically clean up stale connections"""
    while True:
        try:
            time.sleep(300)  # Clean up every 5 minutes
            cleanup_stale_connections()
        except Exception as e:
            print(f"[SocketIO ERROR] Background cleanup failed: {e}")

# Start background cleanup thread
cleanup_thread = threading.Thread(target=background_cleanup, daemon=True)
cleanup_thread.start()
print("[SocketIO] Started background connection cleanup thread")

# Load configuration from config.py for secure local database
app.config.from_object('config.Config')


# Add custom Jinja2 filters
@app.template_filter('format_datetime')
def format_datetime(value, fmt='%Y%m%d%H%M%S'):
    """Format a date or datetime object as string using the specified format."""
    if isinstance(value, str):
        # If value is a string format, treat it as a format pattern
        return datetime.now().strftime(value)
    elif isinstance(value, (datetime, date)):
        # If value is a date or datetime, format it directly
        return value.strftime(fmt)
    else:
        return ""

# --- Add to_eastern Jinja2 filter for timezone conversion ---
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from pytz import timezone as ZoneInfo

def to_eastern(dt, fmt='%Y-%m-%d %I:%M %p'):
    if not dt:
        return ''
    try:
        # If naive, assume UTC
        if getattr(dt, 'tzinfo', None) is None:
            from datetime import timezone as dt_timezone
            dt = dt.replace(tzinfo=dt_timezone.utc)
        # Use zoneinfo if available, else pytz
        try:
            eastern = dt.astimezone(ZoneInfo('America/New_York'))
        except Exception:
            # Fallback for pytz
            eastern = dt.astimezone(ZoneInfo('US/Eastern'))
        return eastern.strftime(fmt)
    except Exception:
        return str(dt)

app.jinja_env.filters['to_eastern'] = to_eastern

# Email configuration (all secrets from environment)
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# Checklist for email environment variables:
# MAIL_SERVER (e.g. smtp.ionos.com)
# MAIL_PORT (e.g. 587)
# MAIL_USE_TLS (true/false)
# MAIL_USERNAME (your email address)
# MAIL_PASSWORD (your email password)
# MAIL_DEFAULT_SENDER (your email address)

# Optional: SMTP connectivity test for debugging
def test_smtp_connection():
    try:
        server = os.environ.get('MAIL_SERVER')
        port = int(os.environ.get('MAIL_PORT', 587))
        username = os.environ.get('MAIL_USERNAME')
        password = os.environ.get('MAIL_PASSWORD')
        use_tls = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
        print(f"Testing SMTP connection to {server}:{port} as {username} (TLS={use_tls})")
        smtp = smtplib.SMTP(server, port, timeout=10)
        if use_tls:
            smtp.starttls()
        smtp.login(username, password)
        smtp.quit()
        print("SMTP connection successful!")
    except Exception as e:
        print(f"SMTP connection failed: {e}")

# Uncomment to test SMTP connectivity at startup
# test_smtp_connection()

# Initialize Flask-Mail
mail = Mail(app)

# Secret key from environment only
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Ensure .env file exists
def ensure_env_file():
    if not os.path.exists(dotenv_path):
        print(f"[APP] .env file not found at {dotenv_path}. Using environment variables.")

# Ensure email template directories exist
def ensure_email_templates():
    templates_dir = os.path.join(BASE_DIR, 'templates')
    email_dir = os.path.join(templates_dir, 'email')
    # Create templates directory if it doesn't exist
    if not os.path.exists(templates_dir):
        print(f"[APP] Creating templates directory: {templates_dir}")
        os.makedirs(templates_dir, exist_ok=True)
    
    # Create email directory if it doesn't exist
    if not os.path.exists(email_dir):
        print(f"[APP] Creating email templates directory: {email_dir}")
        os.makedirs(email_dir, exist_ok=True)
    
    # Check if template files exist
    print("[APP] Checking email templates...")
    # ... rest of your email templates code ...

# Call these setup functions
ensure_env_file()
ensure_email_templates()

# Print debug info about environment

print(f"[APP] Running in environment: {'RENDER' if os.environ.get('RENDER') else 'LOCAL'}")
print(f"[APP] Working directory: {os.getcwd()}")
print(f"[APP] Base directory: {BASE_DIR}")

# --- Ensure sync_queue table exists on startup ---

# NOTE: Table creation moved to initialize_database_and_bootstrap() function
# This prevents circular imports and ensures proper app context

try:
    # Import cache configuration
    from cache_config import configure_caching
except ImportError:
    print("[APP] Warning: cache_config module not found")
    configure_caching = None

try:
    # Import database configuration
    from db_config import configure_database
except ImportError as e:
    print(f"[APP] Error importing db_config: {str(e)}")
    # Define a simple fallback if import fails
    def configure_database(app):
        app.config['SQLALCHEMY_DATABASE_URI'] = POSTGRESQL_DATABASE_URI
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        return app

# Initialize Flask app with better error handling
app.config['APPLICATION_ROOT'] = os.environ.get('APPLICATION_ROOT', '/')
app.config['PREFERRED_URL_SCHEME'] = os.environ.get('PREFERRED_URL_SCHEME', 'https')

# Ensure URLs work with and without trailing slashes
app.url_map.strict_slashes = False



# --- Environment/Platform Detection and Database Switch ---
def is_render():
    """Detect if running on Render.com (production cloud)."""
    return os.environ.get('RENDER', '').lower() == 'true' or os.environ.get('RENDER_EXTERNAL_HOSTNAME')

def auto_sync_offline_db():
    # Clean up expired sync queue records before syncing
    cleanup_expired_sync_queue()
    """Automatically synchronize the local SQLite database with the online database using two-way sync."""
    if is_render():
        print("[SYNC] Running on Render - no offline sync needed")
        return True
    
    # Check if we have the necessary environment variables for online access
    try:
        import requests
        from datetime import datetime
        
        # Check if we have online connectivity by trying to reach the API
        online_url = os.environ.get('AMRS_ONLINE_URL')
        online_username = os.environ.get('AMRS_ADMIN_USERNAME') 
        online_password = os.environ.get('AMRS_ADMIN_PASSWORD')
        
        # Strip quotes from URL if present
        if online_url:
            online_url = online_url.strip('"\'')
        
        if not all([online_url, online_username, online_password]):
            print("[SYNC] Missing online credentials - operating in offline-only mode")
            print("[SYNC] Set AMRS_ONLINE_URL, AMRS_ADMIN_USERNAME, AMRS_ADMIN_PASSWORD for sync")
            return True
            
        print("[SYNC] Starting two-way database synchronization...")
        
        # Test connectivity and authentication
        session = requests.Session()
        
        # Try API-based authentication first, then fall back to session-based auth
        auth_success = False
        
        # Always try session-based login for data endpoint access
        try:
            # Clean up URL to avoid double /api - handle all cases including trailing slashes
            clean_url = online_url.rstrip('/')
            if clean_url.endswith('/api'):
                clean_url = clean_url[:-4]  # Remove /api
            login_resp = session.post(f"{clean_url}/login", data={
                'username': online_username,
                'password': online_password
            })
            
            if login_resp.status_code == 200 and 'dashboard' in login_resp.text.lower():
                auth_success = True
                print("[SYNC] Successfully authenticated via session login")
        except Exception as e:
            print(f"[SYNC] Session login failed: {e}")
            
        # Fallback: Try basic auth for status endpoint test
        if not auth_success:
            try:
                # Clean up URL to avoid double /api - handle all cases including trailing slashes
                clean_url = online_url.rstrip('/')
                if clean_url.endswith('/api'):
                    clean_url = clean_url[:-4]  # Remove /api
                test_resp = session.get(f"{clean_url}/api/sync/status", 
                                      auth=(online_username, online_password))
                if test_resp.status_code == 200:
                    auth_success = True
                    print("[SYNC] Successfully authenticated via API basic auth")
            except:
                pass
        
        if not auth_success:
            print(f"[SYNC] Failed to authenticate with online system")
            return False
        
        # Get local database path
        local_db_path = os.path.join(os.path.dirname(__file__), "maintenance.db")
        
        # Perform sync
        sync_success = perform_bidirectional_sync(session, online_url, local_db_path, online_username, online_password)
        
        if sync_success:
            print("[SYNC] Two-way synchronization completed successfully")
        else:
            print("[SYNC] Synchronization completed with some errors")
            
        return sync_success
        
    except Exception as e:
        print(f"[SYNC] Sync failed - operating in offline mode: {str(e)}")
        return False

def perform_bidirectional_sync(session, online_url, local_db_path, username, password):
    """Perform the actual bidirectional sync using the API."""
    try:
        import sqlite3
        import requests
        from datetime import datetime
        
        # Step 1: Download data from online system
        print("[SYNC] Downloading data from online system...")
        
        # Use the authenticated session (no basic auth needed since we already logged in)
        # Clean up URL to avoid double /api/api - handle all cases including trailing slashes
        clean_url = online_url.rstrip('/')
        if clean_url.endswith('/api'):
            clean_url = clean_url[:-4]  # Remove /api
        download_resp = session.get(f"{clean_url}/api/sync/data")
        if download_resp.status_code != 200:
            print(f"[SYNC] Failed to download data: {download_resp.status_code}")
            return False
            
        online_data = download_resp.json()
        
        # Step 2: Update local database with online changes
        local_conn = sqlite3.connect(local_db_path)
        local_cursor = local_conn.cursor()
        
        # Import online data into local database
        import_online_data_to_local(online_data, local_cursor)
        local_conn.commit()
        # Force SQLAlchemy to reload all ORM relationships and associations after import
        try:
            from models import db
            db.session.remove()
        except Exception as e:
            print(f"[SYNC] Could not remove SQLAlchemy session: {e}")
        
        # Step 3: Get local changes to upload
        print("[SYNC] Preparing local changes for upload...")
        local_changes = get_local_changes_for_upload(local_cursor)
        
        # Step 4: Upload local changes to online system
        if local_changes:
            print(f"[SYNC] Uploading {sum(len(v) for v in local_changes.values())} local changes...")
            
            upload_resp = session.post(f"{clean_url}/api/sync/data", 
                                     json=local_changes,
                                     headers={'Content-Type': 'application/json'})
            
            if upload_resp.status_code != 200:
                print(f"[SYNC] Failed to upload changes: {upload_resp.status_code}")
                local_conn.close()
                return False
                
            print("[SYNC] Successfully uploaded local changes")
        else:
            print("[SYNC] No local changes to upload")
        
        # Update sync timestamp
        update_last_sync_timestamp(local_cursor)
        
        # Fix password hashes for known users after sync
        # (Function fix_common_user_passwords is not defined; skipping call to avoid error)
        
        local_conn.commit()
        local_conn.close()
        
        return True
        
    except Exception as e:
        print(f"[SYNC] Error during bidirectional sync: {str(e)}")
        return False

def import_online_data_to_local(online_data, cursor):
    """Import downloaded online data into the local SQLite database."""
    try:
        # Debug: List all tables received from online
        print(f"[SYNC] Tables received from online: {list(online_data.keys())}")
        # Ensure audit_tasks is always present in the import, even if empty
        if 'audit_tasks' not in online_data:
            print("[SYNC] WARNING: 'audit_tasks' not found in online data. Adding empty list.")
            online_data['audit_tasks'] = []
        # Import each table's data
        for table_name, records in online_data.items():
            if table_name not in ALLOWED_TABLES:
                print(f"[SYNC] Skipping table not in ALLOWED_TABLES: {table_name}")
                continue
            print(f"[SYNC] Importing {len(records)} records for table {table_name}")
            for record in records:
                # Handle soft deletes by checking deleted_at
                if record.get('deleted_at'):
                    # Mark as deleted locally
                    cursor.execute(f"""
                        UPDATE {table_name} 
                        SET deleted_at = ? 
                        WHERE id = ?
                    """, (record['deleted_at'], record['id']))
                else:
                    # Insert or update record
                    try:
                        upsert_record_sqlite(table_name, record, cursor)
                    except Exception as e:
                        print(f"[SYNC] Error upserting record in {table_name}: {e}")
                        print(f"[SYNC] Record data: {record}")
    except Exception as e:
        print(f"[SYNC] Error importing online data: {str(e)}")
        raise

def get_local_changes_for_upload(cursor):
    """Get local changes that need to be uploaded to the online system."""
    try:
        changes = {}
        
        # Get last sync timestamp
        last_sync = get_last_sync_timestamp_local(cursor)
        
        for table_name in ALLOWED_TABLES:
            if last_sync:
                # Get records modified since last sync
                cursor.execute(f"""
                    SELECT * FROM {table_name} 
                    WHERE updated_at > ? OR created_at > ?
                    OR (deleted_at IS NOT NULL AND deleted_at > ?)
                """, (last_sync, last_sync, last_sync))
            else:
                # First sync - get all records
                cursor.execute(f"SELECT * FROM {table_name}")
            
            records = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            # Convert to list of dictionaries
            table_changes = []
            for record in records:
                record_dict = dict(zip(columns, record))
                # Convert datetime objects to ISO strings for JSON serialization
                for key, value in record_dict.items():
                    if isinstance(value, datetime):
                        record_dict[key] = value.isoformat()
                table_changes.append(record_dict)
            
            if table_changes:
                changes[table_name] = table_changes
                
        return changes
        
    except Exception as e:
        print(f"[SYNC] Error getting local changes: {str(e)}")
        return {}

def upsert_record_sqlite(table_name, record, cursor):
    """Insert or update a record in SQLite using UPSERT."""
    try:
        # Get table columns
        cursor.execute(f"PRAGMA table_info({table_name})")
        table_info = cursor.fetchall()
        table_columns = [col[1] for col in table_info]
        
        # Special handling for users table to ensure encryption fields are handled correctly
        if table_name == 'users':
            from models import encrypt_value, hash_value
            
            # Process the record to ensure proper encryption
            processed_record = record.copy()
            
            # Check if we need to encrypt the username
            if 'username' in processed_record:
                username = processed_record['username']
                if username and not processed_record.get('username_hash'):
                    # Plain text username - encrypt it and create hash
                    processed_record['username'] = encrypt_value(username)
                    processed_record['username_hash'] = hash_value(username)
                elif username and processed_record.get('username_hash'):
                    # Username hash provided - check if username is already encrypted
                    try:
                        # Try to decrypt - if it fails, assume it's plain text
                        from models import decrypt_value
                        decrypted = decrypt_value(username)
                        if decrypted == username:
                            # It's plain text, encrypt it
                            processed_record['username'] = encrypt_value(username)
                    except:
                        # Decryption failed, treat as plain text
                        processed_record['username'] = encrypt_value(username)
            
            # Check if we need to encrypt the email
            if 'email' in processed_record:
                email = processed_record['email']
                if email and not processed_record.get('email_hash'):
                    # Plain text email - encrypt it and create hash
                    processed_record['email'] = encrypt_value(email)
                    processed_record['email_hash'] = hash_value(email)
                elif email and processed_record.get('email_hash'):
                    # Email hash provided - check if email is already encrypted
                    try:
                        # Try to decrypt - if it fails, assume it's plain text
                        from models import decrypt_value
                        decrypted = decrypt_value(email)
                        if decrypted == email:
                            # It's plain text, encrypt it
                            processed_record['email'] = encrypt_value(email)
                    except:
                        # Decryption failed, treat as plain text
                        processed_record['email'] = encrypt_value(email)
            
            # Ensure password_hash is present (required field)
            if 'password_hash' not in processed_record or not processed_record['password_hash']:
                if processed_record.get('password_reset_required'):
                    # User needs password reset - generate a secure temporary password
                    from werkzeug.security import generate_password_hash
                    temp_password = f"reset_required_{processed_record.get('id', 'unknown')}"
                    processed_record['password_hash'] = generate_password_hash(temp_password)
                    print(f"[SYNC] User {processed_record.get('id')} requires password reset")
                else:
                    # Generate a random password hash for users without one
                    from werkzeug.security import generate_password_hash
                    processed_record['password_hash'] = generate_password_hash('temp_password_needs_reset')
            
            # Filter to columns that exist in the table
            filtered_record = {k: v for k, v in processed_record.items() if k in table_columns}
        else:
            # Filter record to only include columns that exist in the table
            filtered_record = {k: v for k, v in record.items() if k in table_columns}
        
        if not filtered_record:
            return
            
        columns = list(filtered_record.keys())
        placeholders = ', '.join(['?' for _ in columns])
        
        # Build UPSERT query for SQLite
        if table_name == 'machine_audit_task':
            # For association tables, use INSERT OR IGNORE since there's no ID column
            # and we don't want to update existing associations
            sql = f"""
                INSERT OR IGNORE INTO {table_name} ({', '.join(columns)})
                VALUES ({placeholders})
            """
        elif 'id' in columns:
            update_clauses = ', '.join([f"{col} = excluded.{col}" for col in columns if col != 'id'])
            sql = f"""
                INSERT INTO {table_name} ({', '.join(columns)})
                VALUES ({placeholders})
                ON CONFLICT(id) DO UPDATE SET {update_clauses}
            """
        else:
            # No id column, just insert
            sql = f"""
                INSERT OR REPLACE INTO {table_name} ({', '.join(columns)})
                VALUES ({placeholders})
            """
        
        values = [filtered_record[col] for col in columns]
        cursor.execute(sql, values)
        
    except Exception as e:
        print(f"[SYNC] Error upserting record in {table_name}: {str(e)}")
        print(f"[SYNC] Record data: {record}")
        print(f"[SYNC] Table columns: {table_columns}")
        raise

def get_last_sync_timestamp_local(cursor):
    """Get the last sync timestamp from local metadata."""
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("SELECT value FROM sync_metadata WHERE key = 'last_sync'")
        result = cursor.fetchone()
        return result[0] if result else None
        
    except Exception as e:
        print(f"[SYNC] Error getting last sync timestamp: {str(e)}")
        return None

def update_last_sync_timestamp(cursor):
    """Update the last sync timestamp in local metadata."""
    try:
        from datetime import datetime
        
        cursor.execute("""
            INSERT OR REPLACE INTO sync_metadata (key, value, updated_at)
            VALUES ('last_sync', ?, ?)
        """, (datetime.utcnow().isoformat(), datetime.utcnow()))
        
    except Exception as e:
        print(f"[SYNC] Error updating last sync timestamp: {str(e)}")

# Remove the old helper functions that are no longer needed
def get_online_db_config():
    """Get online database configuration if available."""
    return None  # We're using API-based sync instead of direct database access


# --- Main DB selection logic ---
# NOTE: Database configuration moved to consolidated section later in file

# --- Ensure timestamp columns exist on Render launch for future sync compatibility ---
def ensure_sync_columns():
    """Ensure all tables have created_at, updated_at, and deleted_at columns for sync."""
    try:
        print("[SYNC] Ensuring sync columns exist in all tables...")
        inspector = inspect(db.engine)
        sync_columns = [
            ('created_at', 'TIMESTAMP'),
            ('updated_at', 'TIMESTAMP'),
            ('deleted_at', 'TIMESTAMP')
        ]
        for table in ALLOWED_TABLES:
            if inspector.has_table(table):
                existing_columns = {col['name'] for col in inspector.get_columns(table)}
                with db.engine.connect() as conn:
                    for col_name, col_type in sync_columns:
                        if col_name not in existing_columns:
                            print(f"[SYNC] Adding {col_name} to {table}...")
                            # SQLite doesn't support IF NOT EXISTS in ALTER TABLE, so we check first
                            if 'sqlite' in str(db.engine.url):
                                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
                            else:
                                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
                            conn.commit()
        print("[SYNC] Sync columns ensured.")
    except Exception as e:
        print(f"[SYNC] Error ensuring sync columns: {e}")

# Note: ensure_sync_columns() is called later during proper database initialization

# Initialize Flask-Login
print("[APP] Initializing Flask-Login...")
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Specify the login view endpoint for @login_required
login_manager.login_message_category = 'info'  # Flash message category for login messages

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    # This must return None or a User object
    try:
        from flask import has_app_context
        if not has_app_context() or not user_id:
            return None
        return db.session.get(User, int(user_id))
    except Exception as e:
        app.logger.debug(f"Error loading user {user_id}: {e}")
        return None

# Standardized function to check admin status
def is_admin_user(user):
    """Standardized function to check if a user has admin privileges."""
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    # Relationship-based check
    if hasattr(user, 'role') and user.role and hasattr(user.role, 'name') and user.role.name and user.role.name.lower() == 'admin':
        return True
    # Fallback: username
    if getattr(user, 'username', None) == 'admin':
        return True
    return False

def user_can_see_all_sites(user):
    """Check if a user can see all sites or just their assigned sites.
    
    This function is used to implement site-based access restrictions.
    It returns True if the user is an admin or has maintenance.record permission,
    which means they can see all sites in the system.
    It returns False if the user can only see their assigned sites.
    
    Args:
        user: The user to check permissions for
        
    Returns:
        bool: True if the user can see all sites, False if restricted to assigned sites
    """
    # Admin always sees all sites
    if is_admin_user(user):
        return True
    
    # Check for maintenance.record permission
    if hasattr(user, 'role') and user.role and user.role.permissions:
        if 'maintenance.record' in user.role.permissions.split(','):
            return True
            
    # Otherwise, restrict to assigned sites
    return False

# Database connection checker
def check_db_connection():
    """Check if database connection is working and reconnect if needed."""
    try:
        # Check if we have a Flask app context
        try:
            from flask import has_app_context
            if not has_app_context():
                return False
        except:
            return False
            
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        app.logger.error(f"Database connection error: {e}")
        return False

# Whitelist allowed table and column names for schema changes
ALLOWED_TABLES = {'users', 'roles', 'sites', 'machines', 'parts', 'maintenance_records', 'audit_tasks', 'audit_task_completions', 'machine_audit_task'}
ALLOWED_COLUMNS = {
    'users': {'last_login', 'reset_token', 'reset_token_expiration', 'created_at', 'updated_at'},
    'roles': {'created_at', 'updated_at'},
    'sites': {'created_at', 'updated_at'},
    'machines': {'created_at', 'updated_at'},
    'parts': {'created_at', 'updated_at'},
    'maintenance_records': {'created_at', 'updated_at', 'client_id', 'machine_id', 'maintenance_type', 'description', 'performed_by', 'status', 'notes'},
    'audit_tasks': {'created_at', 'updated_at', 'interval', 'custom_interval_days'},
    'audit_task_completions': {'created_at', 'updated_at'},
    'machine_audit_task': {'audit_task_id', 'machine_id'}
}

# Function to ensure database schema matches models
def ensure_db_schema():
    """Ensure database schema matches the models by adding missing columns and fixing column types."""
    try:
        print("[APP] Checking database schema...")
        inspector = inspect(db.engine)
        table_schemas = {
            'users': {
                'last_login': 'TIMESTAMP',
                'reset_token': 'VARCHAR(100)',
                'reset_token_expiration': 'TIMESTAMP',
                'created_at': 'TIMESTAMP',
                'updated_at': 'TIMESTAMP'
            },
            'roles': {
                'created_at': 'TIMESTAMP',
                'updated_at': 'TIMESTAMP'
            },
            'sites': {
                'created_at': 'TIMESTAMP',
                'updated_at': 'TIMESTAMP'
            },
            'machines': {
                'created_at': 'TIMESTAMP',
                'updated_at': 'TIMESTAMP'
            },
            'parts': {
                'created_at': 'TIMESTAMP',
                'updated_at': 'TIMESTAMP'
            },
            'maintenance_records': {
                'created_at': 'TIMESTAMP',
                'updated_at': 'TIMESTAMP',
                'client_id': 'VARCHAR(36)',
                'machine_id': 'INTEGER',
                'maintenance_type': 'VARCHAR(50)',
                'description': 'TEXT',
                'performed_by': 'VARCHAR(100)',
                'status': 'VARCHAR(50)',
                'notes': 'TEXT'
            },
            'audit_tasks': {
                'created_at': 'TIMESTAMP',
                'updated_at': 'TIMESTAMP',
                'interval': 'VARCHAR(50)',
                'custom_interval_days': 'INTEGER'
            },
            'audit_task_completions': {
                'created_at': 'TIMESTAMP',
                'updated_at': 'TIMESTAMP'
            }
        }
        with db.engine.connect() as conn:
            for table, columns in table_schemas.items():
                if table not in ALLOWED_TABLES:
                    continue
                if inspector.has_table(table):
                    print(f"[APP] Checking {table} table schema...")
                    existing_columns = {column['name']: column for column in inspector.get_columns(table)}
                    for column_name, column_type in columns.items():
                        if column_name not in ALLOWED_COLUMNS.get(table, set()):
                            continue
                        if column_name not in existing_columns:
                            print(f"[APP] Adding missing column {column_name} to {table} table")
                            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column_name} {column_type}"))
                            conn.commit()
                        else:
                            # Check and fix type for client_id in maintenance_records
                            if table == 'maintenance_records' and column_name == 'client_id':
                                db_type = existing_columns[column_name]['type']
                                # Only fix if not already VARCHAR/CHAR/TEXT
                                if not (hasattr(db_type, 'length') and db_type.length == 36) and 'char' not in str(db_type).lower() and 'text' not in str(db_type).lower():
                                    print("[APP] Altering client_id column type to VARCHAR(36) in maintenance_records table")
                                    try:
                                        conn.execute(text("ALTER TABLE maintenance_records ALTER COLUMN client_id TYPE VARCHAR(36) USING client_id::text"))
                                        conn.commit()
                                    except Exception as e:
                                        print(f"[APP] Could not alter client_id column type: {e}")
                    if 'created_at' in columns and 'created_at' not in existing_columns:
                        conn.execute(text(f"UPDATE {table} SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))
                        conn.commit()
                    
                    if 'updated_at' in columns and 'updated_at' not in existing_columns:
                        conn.execute(text(f"UPDATE {table} SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL"))
                        conn.commit()
                else:
                    print(f"[APP] Table {table} does not exist - will be created by db.create_all()")
        
        print("[APP] Database schema check completed")
    except Exception as e:
        print(f"[APP] Error checking database schema: {e}")

# Ensure maintenance_records table has necessary columns
def ensure_maintenance_records_schema():
    """Ensure maintenance_records table has necessary columns."""
    try:
        inspector = inspect(db.engine)
        if inspector.has_table('maintenance_records'):
            columns = [column['name'] for column in inspector.get_columns('maintenance_records')]
            
            # Add client_id column if missing
            if 'client_id' not in columns:
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE maintenance_records ADD COLUMN IF NOT EXISTS client_id VARCHAR(36)"))
                    conn.commit()
                print("[APP] Added client_id column to maintenance_records table")
            
            # Add machine_id column if missing (to fix delete machine error)
            if 'machine_id' not in columns:
                print("[APP] Adding missing machine_id column to maintenance_records table")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE maintenance_records ADD COLUMN IF NOT EXISTS machine_id INTEGER"))
                    conn.commit()
                
                # Populate machine_id from associated part's machine_id
                maintenance_records = MaintenanceRecord.query.all()
                for record in maintenance_records:
                    if record.part:
                        record.machine_id = record.part.machine_id
                
                db.session.commit()
                print("[APP] Populated machine_id values in maintenance_records table")
                
                # Try to add foreign key constraint but don't fail if it doesn't work
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("""
                            ALTER TABLE maintenance_records 
                            ADD CONSTRAINT fk_maintenance_records_machine_id 
                            FOREIGN KEY (machine_id) REFERENCES machines (id)
                        """))
                        conn.commit()
                    print("[APP] Added foreign key constraint to machine_id column")
                except Exception as e:
                    print(f"[APP] Note: Could not add foreign key constraint: {str(e)}")
                    print("[APP] This is not critical, the column is still usable.")
    except Exception as e:
        print(f"[APP] Error ensuring maintenance_records schema: {e}")

def initialize_db_connection():
    """Initialize database connection."""
    try:
        # Test database connection
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("[APP] Database connection established successfully")
    except Exception as e:
        print(f"[APP] Database connection error: {e}")

# --- Default admin creation logic (for online server first launch only) ---
def add_default_admin_if_needed():
    """
    Create a default admin user if needed.
    This should ONLY run on the online server during its first launch.
    Packaged/offline applications should never create admin users - they get users via sync.
    """
    try:
        admin_username = os.environ.get('DEFAULT_ADMIN_USERNAME')
        admin_email = os.environ.get('DEFAULT_ADMIN_EMAIL')
        admin_password = os.environ.get('DEFAULT_ADMIN_PASSWORD')
        
        # Skip if environment variables aren't set
        if not admin_username or not admin_email or not admin_password:
            print("[APP] Default admin credentials not found in environment variables. Skipping default admin creation.")
            return
            
        # Check for admin by username or email (encrypted)
        admin_user = User.query.filter(
            (User._username == encrypt_value(admin_username)) |
            (User._email == encrypt_value(admin_email))
        ).first()

        # Ensure the admin role exists and has admin.full permission
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            # Create admin role if it doesn't exist
            admin_role = Role(name='admin', description='Administrator', permissions='admin.full')
            db.session.add(admin_role)
            db.session.commit()
            print("[APP] Created admin role with full permissions")
        elif 'admin.full' not in admin_role.permissions:
            # Update existing admin role to include admin.full permission
            current_permissions = admin_role.permissions.split(',') if admin_role.permissions else []
            if 'admin.full' not in current_permissions:
                current_permissions.append('admin.full')
                admin_role.permissions = ','.join(current_permissions)
                db.session.commit()
                print("[APP] Updated admin role to include full permissions")
        
        if not admin_user:
            print("[APP] No admin user found, creating default admin user")
            admin = User(
                username=admin_username,
                email=admin_email,
                password_hash=generate_password_hash(admin_password),
                role=admin_role
            )
            db.session.add(admin)
            db.session.commit()
            print(f"[APP] Default admin user created: {admin_username}")
        else:
            # Ensure admin user has admin role
            if admin_user and (not admin_user.role or admin_user.role != admin_role):
                print(f"[APP] Fixing admin role for user {admin_user.username}")
                admin_user.role = admin_role
                db.session.commit()
    except Exception as e:
        print(f"[APP] Error creating/updating default admin: {e}")


# --- Function to assign colors to audit tasks that don't have them ---
def assign_colors_to_audit_tasks():
    """
    Assign unique colors to audit tasks using site-specific color wheels.
    1. Finds tasks without colors and assigns them new ones
    2. Detects and fixes tasks with duplicate colors within the same site
    3. Ensures each site has its own independent color wheel (sites can reuse colors)
    4. Handles all task types that are visualized in the UI
    """
    from models import AuditTask, Site, db
    from sqlalchemy.orm import joinedload
    # Define a color palette (extend as needed)
    color_palette = [
        '#FF5733', '#33FF57', '#3357FF', '#F39C12', '#8E44AD', '#16A085',
        '#E67E22', '#2ECC71', '#3498DB', '#E74C3C', '#1ABC9C', '#9B59B6',
        '#34495E', '#27AE60', '#2980B9', '#C0392B', '#F1C40F', '#7F8C8D',
        '#D35400', '#BDC3C7', '#2C3E50', '#95A5A6', '#FF33A1', '#33FFF6',
    ]
    # Check if Site has an audit_tasks relationship
    if hasattr(Site, 'audit_tasks'):
        # Query all sites with their audit tasks
        sites = Site.query.options(joinedload('audit_tasks')).all()
        for site in sites:
            used_colors = set()
            audit_tasks = getattr(site, 'audit_tasks', [])
            # Collect used colors for this site
            for task in audit_tasks:
                if getattr(task, 'color', None):
                    used_colors.add(task.color)
            # Assign colors to tasks without one
            for task in audit_tasks:
                if not getattr(task, 'color', None):
                    for color in color_palette:
                        if color not in used_colors:
                            task.color = color
                            used_colors.add(color)
                            break
            # Optionally, fix duplicate colors (rare)
            color_count = {}
            for task in audit_tasks:
                color = getattr(task, 'color', None)
                if color:
                    color_count[color] = color_count.get(color, 0) + 1
            for color, count in color_count.items():
                if count > 1:
                    tasks_with_color = [t for t in audit_tasks if getattr(t, 'color', None) == color]
                    for t in tasks_with_color[1:]:
                        for new_color in color_palette:
                            if new_color not in used_colors:
                                t.color = new_color
                                used_colors.add(new_color)
                                break
    else:
        # Fallback: group audit tasks by site_id
        from collections import defaultdict
        tasks_by_site = defaultdict(list)
        all_tasks = AuditTask.query.all()
        for task in all_tasks:
            site_id = getattr(task, 'site_id', None)
            if site_id is not None:
                tasks_by_site[site_id].append(task)
        for site_id, audit_tasks in tasks_by_site.items():
            used_colors = set()
            for task in audit_tasks:
                if getattr(task, 'color', None):
                    used_colors.add(task.color)
            for task in audit_tasks:
                if not getattr(task, 'color', None):
                    for color in color_palette:
                        if color not in used_colors:
                            task.color = color
                            used_colors.add(color)
                            break
            color_count = {}
            for task in audit_tasks:
                color = getattr(task, 'color', None)
                if color:
                    color_count[color] = color_count.get(color, 0) + 1
            for color, count in color_count.items():
                if count > 1:
                    tasks_with_color = [t for t in audit_tasks if getattr(t, 'color', None) == color]
                    for t in tasks_with_color[1:]:
                        for new_color in color_palette:
                            if new_color not in used_colors:
                                t.color = new_color
                                used_colors.add(new_color)
                                break
    db.session.commit()
    color_palette = [
        '#FF5733', '#33FF57', '#3357FF', '#F39C12', '#8E44AD', '#16A085',
        '#E67E22', '#2ECC71', '#3498DB', '#E74C3C', '#1ABC9C', '#9B59B6',
        '#34495E', '#27AE60', '#2980B9', '#C0392B', '#F1C40F', '#7F8C8D',
        '#D35400', '#BDC3C7', '#2C3E50', '#95A5A6', '#FF33A1', '#33FFF6',
    ]
    # Check if Site has an audit_tasks relationship
    if hasattr(Site, 'audit_tasks'):
        # Query all sites with their audit tasks
        sites = Site.query.options(joinedload('audit_tasks')).all()
        for site in sites:
            used_colors = set()
            audit_tasks = getattr(site, 'audit_tasks', [])
            # Collect used colors for this site
            for task in audit_tasks:
                if getattr(task, 'color', None):
                    used_colors.add(task.color)
            # Assign colors to tasks without one
            for task in audit_tasks:
                if not getattr(task, 'color', None):
                    for color in color_palette:
                        if color not in used_colors:
                            task.color = color
                            used_colors.add(color)
                            break
            # Optionally, fix duplicate colors (rare)
            color_count = {}
            for task in audit_tasks:
                color = getattr(task, 'color', None)
                if color:
                    color_count[color] = color_count.get(color, 0) + 1
            for color, count in color_count.items():
                if count > 1:
                    tasks_with_color = [t for t in audit_tasks if getattr(t, 'color', None) == color]
                    for t in tasks_with_color[1:]:
                        for new_color in color_palette:
                            if new_color not in used_colors:
                                t.color = new_color
                                used_colors.add(new_color)
                                break
    else:
        # Fallback: group audit tasks by site_id
        from collections import defaultdict
        tasks_by_site = defaultdict(list)
        all_tasks = AuditTask.query.all()
        for task in all_tasks:
            site_id = getattr(task, 'site_id', None)
            if site_id is not None:
                tasks_by_site[site_id].append(task)
        for site_id, audit_tasks in tasks_by_site.items():
            used_colors = set()
            for task in audit_tasks:
                if getattr(task, 'color', None):
                    used_colors.add(task.color)
            for task in audit_tasks:
                if not getattr(task, 'color', None):
                    for color in color_palette:
                        if color not in used_colors:
                            task.color = color
                            used_colors.add(color)
                            break
            color_count = {}
            for task in audit_tasks:
                color = getattr(task, 'color', None)
                if color:
                    color_count[color] = color_count.get(color, 0) + 1
            for color, count in color_count.items():
                if count > 1:
                    tasks_with_color = [t for t in audit_tasks if getattr(t, 'color', None) == color]
                    for t in tasks_with_color[1:]:
                        for new_color in color_palette:
                            if new_color not in used_colors:
                                t.color = new_color
                                used_colors.add(new_color)
                                break
    db.session.commit()
    try:
        # Get all audit tasks
        all_tasks = AuditTask.query.all()
        if not all_tasks:
            print("[APP] No audit tasks found.")
            return
            
        print(f"[APP] Found {len(all_tasks)} total audit tasks, checking colors...")
        
        # Group all tasks by site_id
        tasks_by_site = {}
        for task in all_tasks:
            if task.site_id not in tasks_by_site:
                tasks_by_site[task.site_id] = []
            tasks_by_site[task.site_id].append(task)
        
        # Track total number of updates needed
        tasks_updated = 0
        
        # For each site, ensure all tasks have unique colors
        for site_id, site_tasks in tasks_by_site.items():
            # Track colors already assigned at this site
            used_colors = set()
            tasks_to_update = []
            
            # First pass: Identify tasks with no color or duplicate colors
            for task in site_tasks:
                if task.color is None:
                    tasks_to_update.append(task)
                elif task.color in used_colors:
                    tasks_to_update.append(task)
                else:
                    used_colors.add(task.color)

            # Second pass: Assign new colors to tasks needing updates
            if tasks_to_update:
                color_palette = [
                    '#FF5733', '#33FF57', '#3357FF', '#F1C40F', '#8E44AD', '#1ABC9C', '#E67E22', '#2ECC71', '#E74C3C', '#3498DB'
                ]
                for idx, task in enumerate(tasks_to_update):
                    color = color_palette[idx % len(color_palette)]
                    task.color = color
                    used_colors.add(color)
                    tasks_updated += 1
            
            # Verify we don't have any duplicate colors after updates
            check_colors = {}
            duplicates_found = False
            
            for task in site_tasks:
                if task.color in check_colors:
                    print(f"[APP] Warning: Duplicate color {task.color} found for tasks: {check_colors[task.color].id} and {task.id}")
                    duplicates_found = True
                else:
                    check_colors[task.color] = task
            
            if duplicates_found:
                print(f"[APP] Warning: Site {site_id} still has duplicate colors after assignment")
        
        # Commit all changes if any tasks were updated
        if tasks_updated > 0:
            db.session.commit()
            print(f"[APP] Successfully assigned unique colors to {tasks_updated} audit tasks.")
        else:
            print("[APP] All audit tasks already have unique colors within their respective sites.")
    except Exception as e:
        db.session.rollback()
        print(f"[APP] Error assigning colors to audit tasks: {e}")
        import traceback
        print(traceback.format_exc())

# NOTE: All database initialization moved to consolidated section at end of file
    try:
        # --- Ensure audit_tasks.color column exists ---
        from sqlalchemy import text
        engine = db.engine
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='audit_tasks' AND column_name='color'
            """))
            if not result.fetchone():
                print("[APP] Adding 'color' column to 'audit_tasks' table...")
                conn.execute(text("ALTER TABLE audit_tasks ADD COLUMN color VARCHAR(32)"))
                print("[APP] Column 'color' added to 'audit_tasks'.")
            else:
                print("[APP] 'color' column already exists in 'audit_tasks'.")
        import expand_user_fields
    except Exception as e:
        print(f"[STARTUP] User field length expansion migration failed: {e}")
    
    # Fix admin role first to ensure it exists with proper permissions
    try:
        # Ensure admin role exists with admin.full permission
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            print("[APP] Creating missing admin role with full permissions")
            admin_role = Role(name='admin', description='Administrator', permissions='admin.full')
            db.session.add(admin_role)
            db.session.commit()
        elif 'admin.full' not in admin_role.permissions:
            # Update existing admin role to include admin.full permission
            current_permissions = admin_role.permissions.split(',') if admin_role.permissions else []
            if 'admin.full' not in current_permissions:
                current_permissions.append('admin.full')
                admin_role.permissions = ','.join(current_permissions)
                db.session.commit()
                print("[APP] Updated admin role to include admin.full permission")
    except Exception as e:
        print(f"[APP] Error fixing admin role: {e}")
    
    # Now fix all admin users to have the admin role
    try:
        # Find the admin role
        admin_role = Role.query.filter_by(name='admin').first()
        if admin_role:
            # Find all users who should be admins (username=admin or is_admin flag)
            admin_users = User.query.filter(
                (User.username == 'admin') | 
                (User._username == encrypt_value('admin'))
            ).all()
            
            # Also get users with is_admin=True as a fallback
            # is_admin is now a property, not a column; skip this filter
            admin_flag_users = []
            
            # Combine the lists without duplicates
            all_admin_users = list({user.id: user for user in admin_users + admin_flag_users}.values())
            
            updated_count = 0
            for user in all_admin_users:
                if not user.role or user.role.id != admin_role.id:
                    user.role = admin_role
                    updated_count += 1
                    print(f"[APP] Fixed admin role for user {user.username}")
            
            if updated_count > 0:
                db.session.commit()
                print(f"[APP] Updated {updated_count} admin user(s) to have the correct role")
    except Exception as e:
        db.session.rollback()
        print(f"[APP] Error fixing admin users: {e}")
    
    # Only run default admin creation for the online server (never for offline/packaged applications)
    from timezone_utils import is_online_server
    if is_online_server():
        print("[APP] Running default admin creation (online server - first launch)")
        add_default_admin_if_needed()
    else:
        print("[APP] Skipping default admin creation - offline/packaged application (users will be synced from online server)")
    
    # Standard integrity checks
    try:
        print("[APP] Performing database integrity checks...")
        admin_users = User.query.join(Role).filter(
            or_(
                Role.name.ilike('admin'),
                User.username == 'admin'
            )
        ).all()
        for user in admin_users:
            if not user.role or user.role.name.lower() != 'admin':
                admin_role = Role.query.filter_by(name='admin').first()
                user.role = admin_role
                print(f"[APP] Fixed admin role for user {user.username}")
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[APP] Error performing database integrity checks: {e}")
    
    # Healthcheck log (now inside app context)
    try:
        from simple_healthcheck import check_database
        print("[STARTUP] Running healthcheck...")
        if check_database():
            print("[STARTUP] Healthcheck PASSED: Database is ready.")
        else:
            print("[STARTUP] Healthcheck FAILED: Database is not ready.")
    except Exception as e:
        print(f"[STARTUP] Healthcheck error: {e}")
    
# NOTE: Database initialization moved to consolidated section at end of file

# Add database connection check before requests
@app.before_request
def ensure_db_connection():
    """Ensure database connection is working before each request."""
    # Skip for static files and health checks
    if request.path.startswith('/static/') or request.path == '/health-check':
        return
        
    # Temporarily disable database connection checks to avoid context issues
    # TODO: Re-enable once all database operations have proper context handling
    return

# Helper: Always allow admins to access any page
@app.before_request
def allow_admin_everywhere():
    """
    Special handling for admin users: bypass permission checks
    Non-admin users proceed normally through the request cycle
    """
    # Only return early for admin users, for everyone else just continue the request
    if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated and getattr(current_user, 'is_admin', False):
        # Bypass permission checks for admins
        return None
    # For non-admin users, don't return anything and let the request continue normally

# Replace the enhance_models function with a template context processor
@app.context_processor
def inject_site_helpers():
    """Add helper functions to templates without modifying models."""
    def get_site_parts_status(site):
        """Get status of parts for a site's machines."""
        try:
            # Get all active (non-decommissioned) machines at this site
            machines = Machine.query.filter_by(site_id=site.id, decommissioned=False).all()
            
            # Count parts
            total_parts = 0
            low_stock = 0
            out_of_stock = 0
            
            for machine in machines:
                parts = Part.query.filter_by(machine_id=machine.id).all()
                total_parts += len(parts)
                
                for part in parts:
                    # Skip quantity checks since Part model doesn't have quantity field
                    # This function currently only counts total parts
                    # Future enhancement: add quantity field to Part model if needed
                    pass
            
            return {
                'total': total_parts,
                'low_stock': low_stock,
                'out_of_stock': out_of_stock
            }
        except Exception as e:
            app.logger.error(f"Error in get_site_parts_status: {e}")
            return {'total': 0, 'low_stock': 0, 'out_of_stock': 0}
    
    # Return both names to support multiple template patterns
    return {
        'get_parts_status': get_site_parts_status,
        'get_site_parts_status': get_site_parts_status
    }

# Add this context processor before other route definitions

@app.context_processor
def inject_common_variables():
    """Inject common variables into all templates."""
    try:
        is_auth = getattr(current_user, 'is_authenticated', False)
    except Exception:
        is_auth = False
    
    def has_permission(permission_name):
        """Check if current user has a specific permission"""
        if not current_user.is_authenticated:
            return False
        if current_user.is_admin:
            return True
        if hasattr(current_user, 'role') and current_user.role and current_user.role.permissions:
            return permission_name in current_user.role.permissions.split(',')
        return False
    
    return {
        'is_admin_user': is_admin_user(current_user) if is_auth else False,
        'url_for_safe': url_for_safe,
        'datetime': datetime,
        'now': datetime.now(),
        'hasattr': hasattr,  # Add hasattr function to be available in templates
        'has_permission': has_permission,  # Add permission checking helper
        'Role': Role,  # Add Role class to template context so it can be used in templates
        'safe_date': safe_date  # Add safe_date function for templates
    }

def url_for_safe(endpoint, **values):
    """A safe wrapper for url_for that won't raise exceptions."""
    try:
        return url_for(endpoint, **values)
    except Exception as e:
        app.logger.warning(f"URL building error for endpoint '{endpoint}': {e}")
        return "#"

def get_all_permissions():
    """Return a dictionary of all available permissions."""
    permissions = {
        'admin.full': 'Full Administrator Access',
        'admin.view': 'View Admin Panel',
        'admin.users': 'Manage Users',
        'admin.roles': 'Manage Roles',
        'sites.view': 'View Sites',
        'sites.create': 'Create Sites',
        'sites.edit': 'Edit Sites',
        'sites.delete': 'Delete Sites',
        'machines.view': 'View Machines',
        'machines.create': 'Create Machines',
        'machines.edit': 'Edit Machines',
        'machines.delete': 'Delete Machines',
        'parts.view': 'View Parts',
        'parts.create': 'Create Parts',
        'parts.edit': 'Edit Parts',
        'parts.delete': 'Delete Parts',
        'maintenance.record': 'Record Maintenance',
        'maintenance.view': 'View Maintenance Records',
        'reports.view': 'View Reports',
        # Audits permissions
        'audits.view': 'View Audits',
        'audits.create': 'Create Audit Tasks',
        'audits.edit': 'Edit Audit Tasks',
        'audits.delete': 'Delete Audit Tasks',
        'audits.complete': 'Complete Audit Tasks',
        'audits.access': 'Access Audits Page'
    }
    return permissions

# Add root route handler
@app.route('/')
def index():
    """Homepage route that redirects to dashboard if logged in or shows login page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Check if user wants to see decommissioned machines
        show_decommissioned = request.args.get('show_decommissioned', 'false').lower() == 'true'
        
        # Get site filter parameter
        site_filter = request.args.get('site_filter', 'all')
        
        # Get upcoming and overdue maintenance across all sites the user has access to
        if user_can_see_all_sites(current_user):
            # User can see all sites, eager load machines and parts
            all_sites = Site.query.options(joinedload(Site.machines).joinedload(Machine.parts)).all()
        else:
            # Check if user has any site assignments first
            if not hasattr(current_user, 'sites') or not current_user.sites:
                # Handle case where user has no site assignments
                app.logger.warning(f"User {current_user.username} (ID: {current_user.id}) has no site assignments")
                return render_template('dashboard.html', 
                                      sites=[], 
                                      all_sites=[],
                                      site_filter='all',
                                      site_part_highlights={},
                                      site_part_totals={},
                                      all_overdue=[],
                                      all_due_soon=[],
                                      all_overdue_total=0,
                                      all_due_soon_total=0,
                                      overdue_count=0, 
                                      due_soon_count=0, 
                                      ok_count=0, 
                                      total_parts=0,
                                      no_sites=True,  # Flag to show special message in template
                                      now=datetime.now(),
                                      show_decommissioned=show_decommissioned,
                                      decommissioned_count=0)
            
            # User can only see their assigned sites, eager load as well
            all_sites = (
                Site.query.options(joinedload(Site.machines).joinedload(Machine.parts))
                .filter(Site.id.in_([site.id for site in current_user.sites]))
                .all()
            )
        
        # Filter sites based on site_filter parameter
        if site_filter == 'all' or not site_filter:
            sites = all_sites
        else:
            try:
                site_id = int(site_filter)
                sites = [site for site in all_sites if site.id == site_id]
            except (ValueError, TypeError):
                sites = all_sites
                site_filter = 'all'
        
        # Get count of decommissioned machines for the toggle
        site_ids = [site.id for site in sites]
        decommissioned_count = 0
        if site_ids:
            decommissioned_count = Machine.query.filter(
                Machine.site_id.in_(site_ids),
                Machine.decommissioned == True
            ).count()
        
        # Get machines based on decommissioned toggle
        machines = []
        if site_ids:
            if show_decommissioned:
                # Show all machines (including decommissioned)
                machines = Machine.query.filter(Machine.site_id.in_(site_ids)).all()
            else:
                # Show only active (non-decommissioned) machines
                machines = Machine.query.filter(
                    Machine.site_id.in_(site_ids),
                    Machine.decommissioned == False
                ).all()
        
        # Get all parts that need maintenance soon or are overdue
        parts = []
        machine_ids = [machine.id for machine in machines]
        if machine_ids:
            # Get all parts for these machines
            parts = Part.query.filter(Part.machine_id.in_(machine_ids)).all()
        
        # Process parts for maintenance status
        now = datetime.now()
        overdue_count = 0
        due_soon_count = 0
        ok_count = 0
        all_overdue = []
        all_due_soon = []
        site_part_highlights = {}
        site_part_totals = {}
        
        # Process each site for the template
        for site in all_sites:
            site_overdue = []
            site_due_soon = []
            
            for machine in site.machines:
                if show_decommissioned or not machine.decommissioned:
                    for part in machine.parts:
                        if not part.next_maintenance:
                            continue
                        days_until = (part.next_maintenance - now).days
                        
                        # Create a dictionary with all needed information for the template
                        part_info = {
                            'part': part,
                            'machine': machine,
                            'site': site,
                            'days_until': days_until
                        }
                        
                        if days_until < 0:
                            site_overdue.append(part_info)
                            all_overdue.append(part_info)
                            overdue_count += 1
                        elif days_until <= 30:  # Due soon threshold
                            site_due_soon.append(part_info)
                            all_due_soon.append(part_info)
                            due_soon_count += 1
                        else:
                            ok_count += 1
            
            # Store site-specific data
            site_part_highlights[site.id] = {
                'overdue': site_overdue[:5],  # Limit to top 5 for highlights
                'due_soon': site_due_soon[:5]
            }
            site_part_totals[site.id] = {
                'overdue': len(site_overdue),
                'due_soon': len(site_due_soon)
            }
        
        total_parts = len(parts)
        all_overdue_total = len(all_overdue)
        all_due_soon_total = len(all_due_soon)
        
        return render_template('dashboard.html', 
                              sites=sites,
                              all_sites=all_sites,
                              site_filter=site_filter,
                              site_part_highlights=site_part_highlights,
                              site_part_totals=site_part_totals,
                              all_overdue=all_overdue[:10],  # Limit to top 10 for performance
                              all_due_soon=all_due_soon[:10],
                              all_overdue_total=all_overdue_total,
                              all_due_soon_total=all_due_soon_total,
                              overdue_count=overdue_count, 
                              due_soon_count=due_soon_count, 
                              ok_count=ok_count, 
                              total_parts=total_parts, 
                              now=now,
                              show_decommissioned=show_decommissioned,
                              decommissioned_count=decommissioned_count)
                              
    except Exception as e:
        import traceback
        app.logger.error(f"Dashboard error: {str(e)}")
        app.logger.error(f"Dashboard error traceback: {traceback.format_exc()}")
        # Instead of redirecting, show a minimal dashboard with an error message
        flash(f'Error loading dashboard data: {str(e)}', 'error')
        return render_template('dashboard.html', 
                              sites=[],
                              all_sites=[],
                              site_filter='all',
                              site_part_highlights={},
                              site_part_totals={},
                              all_overdue=[],
                              all_due_soon=[],
                              all_overdue_total=0,
                              all_due_soon_total=0,
                              overdue_count=0, 
                              due_soon_count=0, 
                              ok_count=0, 
                              total_parts=0,
                              error=True,  # Flag to show error message in template
                              now=datetime.now(),
                              show_decommissioned=False,
                              decommissioned_count=0)

# --- Admin Security Event Log Viewer ---
@app.route('/admin/security-logs', methods=['GET'])
@login_required
def admin_security_logs():
    if not is_admin_user(current_user):
        flash('You do not have permission to view security logs.', 'danger')
        return redirect(url_for('admin'))
    # Get filter parameters
    event_type = request.args.get('event_type')
    username = request.args.get('username')
    days = request.args.get('days', type=int, default=30)
    query = SecurityEvent.query
    if event_type:
        query = query.filter(SecurityEvent.event_type == event_type)
    if username:
        query = query.filter(SecurityEvent.username == username)
    if days:
        since = datetime.utcnow() - timedelta(days=days)
        query = query.filter(SecurityEvent.timestamp >= since)
    logs = query.order_by(SecurityEvent.timestamp.desc()).limit(500).all()
    return render_template('admin_security_logs.html', logs=logs, event_type=event_type, username=username, days=days)

@app.route('/admin')
@login_required
def admin():
    """Enhanced admin dashboard with comprehensive statistics."""
    # Use standardized admin check
    if not is_admin_user(current_user):
        flash('You do not have permission to access the admin panel.', 'danger')
        return redirect(url_for('dashboard'))
    try:
        # Get comprehensive database statistics
        stats = get_database_stats()
        # Create URLs for admin navigation - provide ALL possible links needed by template
        admin_links = {
            'users': url_for('admin_users'),
            'roles': url_for('admin_roles'),
            'sites': url_for('manage_sites'),
            'machines': url_for('manage_machines'),
            'parts': url_for('manage_parts'),
            'dashboard': url_for('dashboard'),
            'profile': url_for('user_profile'),
            'maintenance': url_for('maintenance_page'),
            'audit_history': url_for('admin_audit_history'),
            'excel_import': url_for('admin_excel_import'),
            'bulk_import': url_for('bulk_import'),
            'debug_info': url_for('debug_info')
        }
        # Security event logging toggle state
        security_logging_enabled = AppSetting.get('security_event_logging_enabled', '1') == '1'
        return render_template('admin.html',
                              stats=stats,
                              admin_links=admin_links,
                              user_count=stats.get('users', 0),
                              roles_count=stats.get('roles', 0),
                              sites_count=stats.get('sites', 0),
                              site_count=stats.get('sites', 0),  # Legacy template compatibility
                              machine_count=stats.get('active_machines', 0),
                              total_machine_count=stats.get('machines', 0),
                              decommissioned_machine_count=stats.get('decommissioned_machines', 0),
                              part_count=stats.get('parts', 0),
                              maintenance_records_count=stats.get('maintenance_records', 0),
                              audit_tasks_count=stats.get('audit_tasks', 0),
                              overdue_count=stats.get('maintenance_overdue', 0),
                              due_soon_count=stats.get('maintenance_due_soon', 0),
                              ok_count=stats.get('maintenance_ok', 0),
                              now=datetime.now(),
                              security_logging_enabled=security_logging_enabled,
                              csrf_token=generate_csrf)
    except Exception as e:
        app.logger.error(f"Error in admin dashboard: {e}")
        flash('Error loading admin dashboard. Some statistics may be unavailable.', 'warning')
        return render_template('admin.html',
                              stats={},
                              admin_links={},
                              user_count=0,
                              roles_count=0,
                              sites_count=0,
                              site_count=0,
                              machine_count=0,
                              total_machine_count=0,
                              decommissioned_machine_count=0,
                              part_count=0,
                              maintenance_records_count=0,
                              audit_tasks_count=0,
                              overdue_count=0,
                              due_soon_count=0,
                              ok_count=0,
                              now=datetime.now(),
                              security_logging_enabled=True,
                              csrf_token=generate_csrf)

# --- Admin: Toggle Security Logging ---
@app.route('/admin/toggle-security-logging', methods=['POST'])
@login_required
def toggle_security_logging():
    if not is_admin_user(current_user):
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('admin'))
    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception:
        flash('Invalid CSRF token.', 'danger')
        return redirect(url_for('admin'))
    enabled = AppSetting.get('security_event_logging_enabled', '1') == '1'
    new_value = '0' if enabled else '1'
    AppSetting.set('security_event_logging_enabled', new_value)
    flash(f'Security event logging has been {"enabled" if new_value == "1" else "disabled"}.', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/audit-history')
@login_required
def admin_audit_history():
    if not is_admin_user(current_user):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    completions = AuditTaskCompletion.query.filter_by(completed=True).order_by(AuditTaskCompletion.completed_at.desc()).all()
    audit_tasks = {t.id: t for t in AuditTask.query.all()}
    machines = {m.id: m for m in Machine.query.all()}
    users = {u.id: u for u in User.query.all()}
    return render_template('admin/audit_history.html', completions=completions, audit_tasks=audit_tasks, machines=machines, users=users)

@app.route('/admin/excel-import', methods=['GET'])
@login_required
def admin_excel_import():
    """Admin page for Excel data import."""
    if not is_admin_user(current_user):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    # You can render a template or just show a simple message for now
    return render_template('admin/excel_import.html') if os.path.exists(os.path.join('templates', 'admin', 'excel_import.html')) else "<h1>Excel Import Page</h1>"

@app.route('/test-email', methods=['GET', 'POST'])
@login_required
def test_email():
    # Always allow admins
    if not (current_user.is_admin or (hasattr(current_user, 'role') and current_user.role and 'test_email' in getattr(current_user.role, 'permissions', ''))):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        recipient = request.form.get('recipient') or current_user.email
        try:
            msg = Message(
                subject='Test Email from AMRS Maintenance Tracker',
                recipients=[recipient],
                html=render_template('email/test_email.html', user=current_user),
                sender=current_app.config['MAIL_DEFAULT_SENDER']
            )
            mail.send(msg)
            flash(f'Test email sent to {recipient}', 'success')
        except Exception as e:
            flash(f'Failed to send test email: {e}', 'danger')
    return render_template('admin/test_email.html')

@app.route('/audits', methods=['GET', 'POST'])
@login_required
def audits_page():
    # Permission checks
    can_delete_audits = False
    can_complete_audits = False
    if current_user.is_admin:
        can_delete_audits = True
        can_complete_audits = True
    else:
        # Handle both cases where role is a Role object or a string
        if hasattr(current_user, 'role') and current_user.role:
            if hasattr(current_user.role, 'name'):
                # Role is an object, use its permissions directly
                permissions = (current_user.role.permissions or '').replace(' ', '').split(',') 
                can_delete_audits = 'audits.delete' in permissions
                can_complete_audits = 'audits.complete' in permissions
            else:
                # Role is a string, query for the role
                user_role = Role.query.filter_by(name=current_user.role).first()
                permissions = (user_role.permissions or '').replace(' ', '').split(',') if user_role and user_role.permissions else []
                can_delete_audits = 'audits.delete' in permissions
                can_complete_audits = 'audits.complete' in permissions


    # Always re-query audit_tasks and sites from the database to ensure relationships are hydrated after sync/import
    from sqlalchemy.orm import joinedload
    if current_user.is_admin:
        audit_tasks = AuditTask.query.options(joinedload(AuditTask.machines)).all()
        sites = Site.query.options(joinedload(Site.machines)).all()
    else:
        user_site_ids = [site.id for site in current_user.sites]
        audit_tasks = AuditTask.query.options(joinedload(AuditTask.machines)).filter(AuditTask.site_id.in_(user_site_ids)).all()
        sites = Site.query.options(joinedload(Site.machines)).filter(Site.id.in_(user_site_ids)).all()

    today = get_eastern_date()  # Use timezone-aware date
    completions = {(c.audit_task_id, c.machine_id): c for c in AuditTaskCompletion.query.filter_by(date=today).all()}
    
    # Build a dict: (task_id, machine_id) -> next_eligible_date
    eligibility = {}
    for task in audit_tasks:
        for machine in task.machines:
            last_completion = (
                AuditTaskCompletion.query
                .filter_by(audit_task_id=task.id, machine_id=machine.id, completed=True)
                .order_by(AuditTaskCompletion.date.desc())
                .first()
            )
            if last_completion:
                last_date = last_completion.date
            else:
                last_date = None
            # Determine interval in days
            if task.interval == 'daily':
                interval_days = 1
            elif task.interval == 'weekly':
                interval_days = 7
            elif task.interval == 'monthly':
                interval_days = 30
            elif task.interval == 'custom' and task.custom_interval_days:
                interval_days = task.custom_interval_days
            else:
                interval_days = 1  # Default/fallback
            if last_date:
                next_eligible = last_date + timedelta(days=interval_days)
            else:
                next_eligible = None  # No completion yet, eligible immediately
            eligibility[(task.id, machine.id)] = next_eligible

    if request.method == 'POST' and request.form.get('create_audit') == '1':
        interval = request.form.get('interval')
        custom_interval_days = None
        if interval == 'custom':
            value = int(request.form.get('custom_interval_value', 1))
            unit = request.form.get('custom_interval_unit', 'day')
            if unit == 'week':
                custom_interval_days = value * 7
            elif unit == 'month':
                custom_interval_days = value * 30
            else:
                custom_interval_days = value
        machine_ids = request.form.getlist('machine_ids')
        if not (request.form.get('name') and request.form.get('site_id') and machine_ids):
            flash('Task name, site, and at least one machine are required.', 'danger')
            return redirect(url_for('audits_page'))
        try:
            site_id = int(request.form.get('site_id'))
            # Get all existing tasks for this site (before adding the new one)
            existing_tasks = AuditTask.query.filter_by(site_id=site_id).order_by(AuditTask.id).all()
            color_index = len(existing_tasks)
            num_colors = color_index + 1  # include the new one
            hue = int((color_index * 360) / num_colors) % 360
            color = f"hsl({hue}, 70%, 50%)"
            audit_task = AuditTask(
                name=request.form.get('name'),
                description=request.form.get('description'),
                site_id=site_id,
                created_by=current_user.id,
                interval=interval,
                custom_interval_days=custom_interval_days,
                color=color
            )
            for machine_id in machine_ids:
                machine = Machine.query.get(int(machine_id))
                if machine:
                    audit_task.machines.append(machine)
            db.session.add(audit_task)
            db.session.commit()
            
            # Log to sync queue AFTER commit so audit_task.id is available (immediate sync)
            add_to_sync_queue_enhanced('audit_tasks', audit_task.id, 'insert', {
                'id': audit_task.id,
                'name': audit_task.name,
                'description': audit_task.description,
                'site_id': audit_task.site_id,
                'created_by': audit_task.created_by,
                'interval': audit_task.interval,
                'custom_interval_days': audit_task.custom_interval_days,
                'color': audit_task.color
            }, immediate_sync=True)
            
            # Log machine associations to sync queue
            for machine_id in machine_ids:
                machine = Machine.query.get(int(machine_id))
                if machine:
                    add_to_sync_queue_enhanced('machine_audit_task', f'{audit_task.id}_{machine.id}', 'insert', {
                        'audit_task_id': audit_task.id,
                        'machine_id': machine.id
                    }, immediate_sync=True)
            flash('Audit task created successfully.', 'success')
            return redirect(url_for('audits_page'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating audit task: {str(e)}', 'danger')
            return redirect(url_for('audits_page'))
            
    if request.method == 'POST' and request.form.get('checkoff') == '1':
        updated = 0
        for task in audit_tasks:
            for machine in task.machines:
                key = f'complete_{task.id}_{machine.id}'
                if key in request.form:
                    # Check if already completed today
                    existing_completion = completions.get((task.id, machine.id))
                    if existing_completion and existing_completion.completed:
                        continue
                    # Strictly enforce interval: only allow if no previous completion or today >= next eligible date
                    next_eligible = eligibility.get((task.id, machine.id))
                    if next_eligible is not None and today < next_eligible:
                        continue  # Not eligible yet
                    
                    # Only record completion if eligible (either no previous completion or today >= next_eligible)
                    if existing_completion:
                        # Update existing completion record
                        existing_completion.completed = True
                        existing_completion.completed_by = current_user.id
                        existing_completion.completed_at = get_timezone_aware_now()  # Use timezone-aware datetime
                        completion = existing_completion
                        
                        # Log to sync queue for updated completion (immediate sync)
                        add_to_sync_queue_enhanced('audit_task_completions', completion.id, 'update', {
                            'id': completion.id,
                            'audit_task_id': completion.audit_task_id,
                            'machine_id': completion.machine_id,
                            'date': str(completion.date),
                            'completed': completion.completed,
                            'completed_by': completion.completed_by,
                            'completed_at': completion.completed_at.isoformat() if completion.completed_at else None
                        }, immediate_sync=True)
                    else:
                        # Check for any existing completion for this task/machine/date combination
                        # This handles cases where completions exist but weren't in our initial query
                        existing_any = AuditTaskCompletion.query.filter_by(
                            audit_task_id=task.id,
                            machine_id=machine.id,
                            date=today
                        ).first()
                        
                        if existing_any:
                            # Update the existing record
                            existing_any.completed = True
                            existing_any.completed_by = current_user.id
                            existing_any.completed_at = get_timezone_aware_now()  # Use timezone-aware datetime
                            completion = existing_any
                            
                            # Log to sync queue for updated completion (immediate sync)
                            add_to_sync_queue_enhanced('audit_task_completions', completion.id, 'update', {
                                'id': completion.id,
                                'audit_task_id': completion.audit_task_id,
                                'machine_id': completion.machine_id,
                                'date': str(completion.date),
                                'completed': completion.completed,
                                'completed_by': completion.completed_by,
                                'completed_at': completion.completed_at.isoformat() if completion.completed_at else None
                            }, immediate_sync=True)
                        else:
                            # Create new completion record with robust conflict handling
                            # First, fix PostgreSQL sequence to prevent ID conflicts
                            try:
                                if 'postgresql' in str(db.engine.url).lower():
                                    from sqlalchemy import text
                                    # Get max ID and update sequence
                                    max_id = db.session.execute(text("SELECT COALESCE(MAX(id), 0) FROM audit_task_completions")).scalar()
                                    if max_id:
                                        db.session.execute(text(f"SELECT setval('audit_task_completions_id_seq', {max_id + 1})"))
                                        db.session.commit()
                            except Exception as seq_error:
                                print(f"[AUDIT] Could not fix sequence: {seq_error}")
                            
                            # Now create the completion record
                            completion = AuditTaskCompletion(
                                audit_task_id=task.id,
                                machine_id=machine.id,
                                date=today,
                                completed=True,
                                completed_by=current_user.id,
                                completed_at=get_timezone_aware_now()  # Use timezone-aware datetime
                            )
                            
                            # Try add first, if it fails due to ID conflict, use merge
                            try:
                                db.session.add(completion)
                                db.session.flush()  # This will trigger the ID assignment and potential conflict
                            except Exception as add_error:
                                if "duplicate key" in str(add_error).lower() or "unique constraint" in str(add_error).lower():
                                    print(f"[AUDIT] ID conflict detected, using merge: {add_error}")
                                    db.session.rollback()
                                    # Use merge as fallback
                                    completion = db.session.merge(completion)
                                    db.session.flush()  # Ensure the merge is processed
                                else:
                                    raise add_error
                    
                    # Log to sync queue immediately after successful completion creation (immediate sync)
                    if completion and hasattr(completion, 'id'):
                        add_to_sync_queue_enhanced('audit_task_completions', completion.id, 'insert', {
                            'id': completion.id,
                            'audit_task_id': completion.audit_task_id,
                            'machine_id': completion.machine_id,
                            'date': str(completion.date),
                            'completed': completion.completed,
                            'completed_by': completion.completed_by,
                            'completed_at': completion.completed_at.isoformat() if completion.completed_at else None
                        }, immediate_sync=True)
                    
                    updated += 1
        if updated:
            db.session.commit()
            # Notify desktop clients that audit completion changes are available
            notify_desktop_clients_of_changes()
            flash(f'{updated} audit task(s) checked off successfully.', 'success')
        else:
            flash('No eligible audit tasks were checked off. Some checkoffs are not yet eligible.', 'warning')
        return redirect(url_for('audits_page'))
    
    # Helper function for the template
    def get_calendar_weeks(start, end):
        """Get calendar weeks for the date range."""
        # Handle both date objects and year/month integers
        if isinstance(start, int) and isinstance(end, int):
            # start is year, end is month
            year, month = start, end
            import calendar
            start = date(year, month, 1)
            # Get last day of the month
            last_day = calendar.monthrange(year, month)[1]
            end = date(year, month, last_day)
        
        # Find the first Sunday before or on the start date
        first_day_week = start - timedelta(days=start.weekday() + 1)
        if first_day_week.weekday() != 6:  # If not Sunday
            first_day_week = start - timedelta(days=(start.weekday() + 1) % 7)
        
        # Find the last Saturday after or on the end date
        last_day_week = end + timedelta(days=(5 - end.weekday()) % 7)
        
        # Generate weeks
        weeks = []
        current = first_day_week
        while current <= last_day_week:
            week = []
            for _ in range(7):
                week.append(current)
                current = current + timedelta(days=1)
            weeks.append(week)
        
        return weeks

    # Get monthly completions for calendar view
    from calendar import monthrange
    month_start = date(today.year, today.month, 1)
    month_end = date(today.year, today.month, monthrange(today.year, today.month)[1])
    
    monthly_completions = AuditTaskCompletion.query.filter(
        AuditTaskCompletion.date >= month_start,
        AuditTaskCompletion.date <= month_end,
        AuditTaskCompletion.completed == True
    ).all()
    
    # Build month_completions: {(task_id, machine_id, date_string): completion}
    month_completions = {}
    for completion in monthly_completions:
        date_str = completion.date.strftime('%Y-%m-%d')
        key = (completion.audit_task_id, completion.machine_id, date_str)
        month_completions[key] = completion

    return render_template('audits.html', audit_tasks=audit_tasks, sites=sites, completions=completions, today=today, can_delete_audits=can_delete_audits, can_complete_audits=can_complete_audits, eligibility=eligibility, get_calendar_weeks=get_calendar_weeks, month_completions=month_completions)

@app.route('/audit-history', methods=['GET'])
@login_required
def audit_history_page():
    # Same permission checks as audits_page
    if current_user.is_admin:
        can_access = True
    else:
        if hasattr(current_user, 'role') and current_user.role:
            if hasattr(current_user.role, 'name'):
                permissions = (current_user.role.permissions or '').replace(' ', '').split(',') 
                can_access = 'audits.access' in permissions
            else:
                user_role = Role.query.filter_by(name=current_user.role).first()
                permissions = (user_role.permissions or '').replace(' ', '').split(',') if user_role and user_role.permissions else []
                can_access = 'audits.access' in permissions
        else:
            can_access = False
    if not can_access:
        flash('You do not have permission to access audit history.', 'danger')
        return redirect(url_for('dashboard'))

    from calendar import monthrange
    today = datetime.now().date()
    # --- Parse month/year from month_year param ---
    month_year = request.args.get('month_year')
    if month_year:
        try:
            year, month = map(int, month_year.split('-'))
        except Exception:
            month = today.month
            year = today.year
    else:
        month = today.month
        year = today.year
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    # --- Generate available months for dropdown (from April 2025 to current month) ---
    import calendar
    from collections import OrderedDict
    start_month = 4
    start_year = 2025
    available_months = []
    y, m = start_year, start_month
    end_year, end_month = today.year, today.month
    while (y < end_year) or (y == end_year and m <= end_month):
        value = f"{y:04d}-{m:02d}"
        display = f"{calendar.month_name[m]} {y}"
        available_months.append({'value': value, 'display': display})
        m += 1
        if m > 12:
            m = 1
            y += 1
    
    # Explicitly check if we need to add the current month (for first of month)
    current_month_value = f"{today.year:04d}-{today.month:02d}"
    if not any(month['value'] == current_month_value for month in available_months):
        available_months.append({
            'value': current_month_value,
            'display': f"{calendar.month_name[today.month]} {today.year}"
        })
        app.logger.info(f"Added current month {current_month_value} to dropdown (first day of month detection)")
    
    # Ensure start month is always included
    if not any(month['value'] == f'{start_year:04d}-{start_month:02d}' for month in available_months):
        available_months.append({'value': f'{start_year:04d}-{start_month:02d}', 'display': f'{calendar.month_name[start_month]} {start_year}'})
    available_months = sorted(available_months, key=lambda x: x['value'], reverse=True)
    selected_month = f"{year:04d}-{month:02d}"

    # Get site and machine filters
    site_id = request.args.get('site_id', type=int)
    machine_id = request.args.get('machine_id')
    selected_machine = machine_id if machine_id else ''
    if machine_id:
        try:
            machine_id = int(machine_id)
        except Exception:
            machine_id = None

    # Restrict sites for non-admins
    if current_user.is_admin:
        sites = Site.query.all()
    else:
        user_site_ids = [site.id for site in current_user.sites]
        sites = current_user.sites
        if site_id and site_id not in user_site_ids:
            site_id = sites[0].id if sites else None
    if len(sites) == 1 and not site_id:
        site_id = sites[0].id

    # Get available machines based on selected site
    if site_id:
        available_machines = Machine.query.filter_by(site_id=site_id).all()
    else:
        if not current_user.is_admin and sites:
            site_ids = [site.id for site in sites]
            available_machines = Machine.query.filter(Machine.site_id.in_(site_ids)).all()
        else:
            available_machines = Machine.query.all()

    # Query completions for the selected month
    query = AuditTaskCompletion.query.filter(
        AuditTaskCompletion.date >= first_day,
        AuditTaskCompletion.date <= last_day,
        AuditTaskCompletion.completed == True
    )
    if site_id:
        site_audit_tasks = AuditTask.query.filter_by(site_id=site_id).all()
        task_ids = [task.id for task in site_audit_tasks]
        if task_ids:
            query = query.filter(AuditTaskCompletion.audit_task_id.in_(task_ids))
        else:
            completions = []
            machine_data = {}
            return render_template('audit_history.html', 
                completions=completions, 
                month=month, 
                year=year,
                current_month=month,
                current_year=year,
                month_weeks=[], 
                machine_data=machine_data, 
                audit_tasks={}, 
                unique_tasks=[], 
                machines={}, 
                users={}, 
                sites=sites, 
                selected_site=site_id, 
                selected_machine=selected_machine, 
                available_months=available_months, 
                available_machines=available_machines, 
                selected_month=selected_month,
                all_tasks_per_machine={},
                interval_bars={},
                display_machines=[],
                get_calendar_weeks=lambda start, end: [],
                today=today
            )
    else:
        if not current_user.is_admin and sites:
            site_ids = [site.id for site in sites]
            site_audit_tasks = AuditTask.query.filter(AuditTask.site_id.in_(site_ids)).all()
            task_ids = [task.id for task in site_audit_tasks]
            if task_ids:
                query = query.filter(AuditTaskCompletion.audit_task_id.in_(task_ids))
            else:
                completions = []
                machine_data = {}
                return render_template('audit_history.html', 
                    completions=completions, 
                    month=month, 
                    year=year,
                    current_month=month,
                    current_year=year,
                    month_weeks=[], 
                    machine_data=machine_data, 
                    audit_tasks={}, 
                    unique_tasks=[], 
                    machines={}, 
                    users={}, 
                    sites=sites, 
                    selected_site=site_id, 
                    selected_machine=selected_machine, 
                    available_months=available_months, 
                    available_machines=available_machines, 
                    selected_month=selected_month,
                    all_tasks_per_machine={},
                    interval_bars={},
                    display_machines=[],
                    get_calendar_weeks=lambda start, end: [],
                    today=today
                )
    completions = query.all()

    print(f"[DEBUG] Main audit history - Date range: {first_day} to {last_day}")
    print(f"[DEBUG] Main audit history - Site filter: {site_id}, Machine filter: {machine_id}")
    print(f"[DEBUG] Main audit history - Found {len(completions)} completions for {month}/{year}")
    if completions:
        print(f"[DEBUG] Sample completion: task_id={completions[0].audit_task_id}, machine_id={completions[0].machine_id}, date={completions[0].date}")

    # --- Build calendar weeks for the month ---
    import calendar
    cal = calendar.Calendar(firstweekday=6)  # Sunday start
    month_weeks = list(cal.monthdayscalendar(year, month))

    # --- Build machine_data: {machine_id: {date_string: [completions]}} ---
    machine_data = {}
    for completion in completions:
        m_id = completion.machine_id
        d = completion.date.strftime('%Y-%m-%d') if completion.date else None
        if d and m_id not in machine_data:
            machine_data[m_id] = {}
        if d and d not in machine_data[m_id]:
            machine_data[m_id][d] = []
        if d:
            machine_data[m_id][d].append(completion)

    # --- Build audit_tasks and unique_tasks for legend ---
    audit_tasks = {task.id: task for task in AuditTask.query.all()}
    unique_tasks = [audit_tasks[tid] for tid in {completion.audit_task_id for completion in completions if completion.audit_task_id in audit_tasks}]

    # --- Build all_tasks_per_machine: {machine_id: [AuditTask, ...]} ---
    all_tasks_per_machine = {}
    for machine in available_machines:
        all_tasks_per_machine[machine.id] = [task for task in audit_tasks.values() if machine in task.machines]

    # --- Build interval_bars: {machine_id: {task_id: [(start_date, end_date), ...]}} ---
    from collections import defaultdict
    interval_bars = defaultdict(lambda: defaultdict(list))
    for machine in available_machines:
        for task in all_tasks_per_machine[machine.id]:
            # Only for interval-based tasks (not daily)
            if task.interval in ('weekly', 'monthly') or (task.interval == 'custom' and task.custom_interval_days):
                # Determine interval length
                if task.interval == 'weekly':
                    interval_days = 7
                elif task.interval == 'monthly':
                    interval_days = 30
                elif task.interval == 'custom' and task.custom_interval_days:
                    interval_days = task.custom_interval_days
                else:
                    continue
                # Find the first interval start <= last_day
                # For simplicity, assume the interval starts from the first day of the month
                current = first_day
                while current <= last_day:
                    start = current
                    end = min(current + timedelta(days=interval_days - 1), last_day)
                    interval_bars[machine.id][task.id].append((start, end))
                    current = end + timedelta(days=1)

    machines_dict = {machine.id: machine for machine in available_machines}
    users = {user.id: user for user in User.query.all()}

    # Helper function for the template
    def get_calendar_weeks(start, end):
        """Get calendar weeks for the date range."""
        # Handle both date objects and year/month integers
        if isinstance(start, int) and isinstance(end, int):
            # start is year, end is month
            year, month = start, end
            import calendar
            start = date(year, month, 1)
            # Get last day of the month
            last_day = calendar.monthrange(year, month)[1]
            end = date(year, month, last_day)
        
        # Find the first Sunday before or on the start date
        first_day_week = start - timedelta(days=start.weekday() + 1)
        if first_day_week.weekday() != 6:  # If not Sunday
            first_day_week = start - timedelta(days=(start.weekday() + 1) % 7)
        
        # Find the last Saturday after or on the end date
        last_day_week = end + timedelta(days=(5 - end.weekday()) % 7)
        
        # Generate weeks
        weeks = []
        current = first_day_week
        while current <= last_day_week:
            week = []
            for _ in range(7):
                week.append(current)
                current = current + timedelta(days=1)
            weeks.append(week)
        
        return weeks

    return render_template(
        'audit_history.html',
        audit_tasks=audit_tasks,
        sites=sites,
        completions=completions,
        today=today,
        month=month,
        year=year,
        current_month=month,
        current_year=year,
        month_weeks=month_weeks,
        machine_data=machine_data,
        unique_tasks=unique_tasks,
        machines=machines_dict,
        users=users,
        selected_site=site_id,
        selected_machine=selected_machine,
        available_months=available_months,
        available_machines=available_machines,
        selected_month=selected_month,
        all_tasks_per_machine=all_tasks_per_machine,
        interval_bars=interval_bars,
        display_machines=available_machines,
        get_calendar_weeks=get_calendar_weeks
    )

@app.route('/audit-history/print-view', methods=['GET'])
@login_required
def audit_history_print():
    """Print view for audit history."""
    # Same permission checks as audit_history_page
    if current_user.is_admin:
        can_access = True
    else:
        if hasattr(current_user, 'role') and current_user.role:
            if hasattr(current_user.role, 'name'):
                permissions = (current_user.role.permissions or '').replace(' ', '').split(',') 
                can_access = 'audits.access' in permissions
            else:
                user_role = Role.query.filter_by(name=current_user.role).first()
                permissions = (user_role.permissions or '').replace(' ', '').split(',') if user_role and user_role.permissions else []
                can_access = 'audits.access' in permissions
        else:
            can_access = False
    if not can_access:
        flash('You do not have permission to access audit history.', 'danger')
        return redirect(url_for('dashboard'))

    # Define the calendar weeks function early
    def get_calendar_weeks(start_date, end_date):
        """Get calendar weeks for the date range."""
        import calendar
        weeks = []
        current = start_date.replace(day=1)
        
        # Get first Monday of the month view
        while current.weekday() != 0:  # 0 is Monday
            current -= timedelta(days=1)
        
        # Generate weeks until we cover the end date
        while current <= end_date or len(weeks) < 6:
            week = []
            for i in range(7):
                week.append(current + timedelta(days=i))
            weeks.append(week)
            current += timedelta(days=7)
            
            # Stop if we have 6 weeks and covered the month
            if len(weeks) >= 6 and current > end_date:
                break
                
        return weeks

    from calendar import monthrange
    today = datetime.now().date()
    
    # Parse month/year from month_year param
    month_year = request.args.get('month_year')
    if month_year:
        try:
            year, month = map(int, month_year.split('-'))
        except Exception:
            month = today.month
            year = today.year
    else:
        month = today.month
        year = today.year
    
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    # Get filters
    site_id = request.args.get('site_id', type=int)
    selected_machine = request.args.get('machine_id', type=int)
    
    # Get sites
    if current_user.is_admin:
        sites = Site.query.all()
    else:
        sites = current_user.sites

    # Build query for completions
    query = AuditTaskCompletion.query.filter(
        AuditTaskCompletion.completed_at >= first_day,
        AuditTaskCompletion.completed_at <= last_day
    )

    # Apply site filter
    if site_id:
        site_audit_tasks = AuditTask.query.filter_by(site_id=site_id).all()
        task_ids = [task.id for task in site_audit_tasks]
        if task_ids:
            query = query.filter(AuditTaskCompletion.audit_task_id.in_(task_ids))
        else:
            # No tasks for this site, return empty
            return render_template('audit_history_pdf.html', 
                machines=[], completions=[], machine_data={}, 
                audit_tasks={}, all_tasks_per_machine={}, 
                start_date=first_day, end_date=last_day, today=today,
                get_calendar_weeks=get_calendar_weeks)
    else:
        if not current_user.is_admin and sites:
            site_ids = [site.id for site in sites]
            site_audit_tasks = AuditTask.query.filter(AuditTask.site_id.in_(site_ids)).all()
            task_ids = [task.id for task in site_audit_tasks]
            if task_ids:
                query = query.filter(AuditTaskCompletion.audit_task_id.in_(task_ids))

    completions = query.all()

    # Build machine data structure
    machine_data = {}
    audit_tasks = {}
    all_tasks_per_machine = {}
    
    # Create a lookup dictionary for machines to avoid multiple queries
    machine_ids = {completion.machine_id for completion in completions}
    machines_lookup = {machine.id: machine for machine in Machine.query.filter(Machine.id.in_(machine_ids)).all()}
    
    for completion in completions:
        task = completion.audit_task
        machine = machines_lookup.get(completion.machine_id)
        if not task or not machine or not completion.completed_at:
            continue
            
        machine_id = machine.id
        completion_date = completion.completed_at.strftime('%Y-%m-%d')
        
        if machine_id not in machine_data:
            machine_data[machine_id] = {}
        if completion_date not in machine_data[machine_id]:
            machine_data[machine_id][completion_date] = []
        
        machine_data[machine_id][completion_date].append(completion)
        audit_tasks[completion.audit_task_id] = task
        
        if machine_id not in all_tasks_per_machine:
            all_tasks_per_machine[machine_id] = []
        if task not in all_tasks_per_machine[machine_id]:
            all_tasks_per_machine[machine_id].append(task)

    # Get machines that have data
    machines = []
    for machine_id in machine_data.keys():
        machine = Machine.query.get(machine_id)
        if machine:
            # Apply machine filter
            if selected_machine and machine.id != selected_machine:
                continue
            machines.append(machine)

    return render_template('audit_history_pdf.html',
        machines=machines,
        completions=completions,
        machine_data=machine_data,
        audit_tasks=audit_tasks,
        all_tasks_per_machine=all_tasks_per_machine,
        start_date=first_day,
        end_date=last_day,
        today=today,
        get_calendar_weeks=get_calendar_weeks
    )

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def admin_users():
    from security_event_logger import log_security_event
    """User management page."""
    # Use standardized admin check
    if not is_admin_user(current_user):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Handle form submission for creating a new user
    if request.method == 'POST':
        log_security_event(
            event_type="admin_user_change",
            details=f"Admin user change by {getattr(current_user, 'username', None)}. Data: {request.form}",
            is_critical=True
        )
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            role_id = request.form.get('role_id')
            role = db.session.get(Role, int(role_id)) if role_id else None
            
            # Validate required fields
            if not username or not email or not password:
                flash('Username, email, and password are required.', 'danger')
                return redirect('/admin/users')
            
            # Check if username or email already exist
            if User.query.filter_by(_username=encrypt_value(username)).first():
                flash(f'Username "{username}" is already taken.', 'danger')
                return redirect('/admin/users')
                
            if User.query.filter_by(_email=encrypt_value(email)).first():
                flash(f'Email "{email}" is already registered.', 'danger')
                return redirect('/admin/users')
            
            # Validate password length
            if len(password) < 8:
                flash('Password must be at least 8 characters long.', 'danger')
                return redirect('/admin/users')
            
            # Create new user with role as object
            new_user = User(
                # Always use property setters so values are encrypted once
                password_hash=generate_password_hash(password),
                role=role
            )
            new_user.username = username
            new_user.email = email
            
            # Add user to database
            db.session.add(new_user)
            db.session.commit()
            # Log to sync queue
            add_to_sync_queue_enhanced('users', new_user.id, 'insert', {
                'id': new_user.id,
                'username': new_user.username,
                'email': new_user.email,
                'full_name': new_user.full_name,
                'role_id': new_user.role_id
            }, immediate_sync=False)
            flash(f'User "{username}" created successfully.', 'success')
            return redirect('/admin/users')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creating user: {e}")
            flash(f'Error creating user: {str(e)}', 'danger')
    
    # For GET requests or after POST processing
    try:
        # Ensure database session is refreshed to get the latest data
        db.session.expire_all()
        
        # Get all users and roles for the template
        users = User.query.all()
        roles = Role.query.all()
        sites = Site.query.all()
        
        # Pre-generate safe URLs for actions on each user
        user_actions = {}
        for user in users:
            user_actions[user.id] = {
                'edit': f'/user/edit/{user.id}',
                'delete': f'/user/delete/{user.id}',
                'reset_password': f'/user/reset-password/{user.id}'
            }
        
        # Safe URLs for general actions
        safe_urls = {
            'create_user': '/admin/users',  # Updated to point to this route
            'users_list': '/admin/users',
            'roles_list': '/admin/roles',
            'dashboard': '/dashboard',
            'admin': '/admin'
        }
        
        # Use the specific template instead of the generic admin.html
        return render_template('admin/users.html', 
                              users=users,
                              roles=roles,
                              sites=sites,
                              current_user=current_user,
                              user_actions=user_actions,
                              safe_urls=safe_urls)
    except Exception as e:
        app.logger.error(f"Error in admin_users route: {e}")
        flash('An error occurred while loading the users page.', 'danger')
        return redirect('/admin')

@app.route('/user/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    from security_event_logger import log_security_event
    """Edit an existing user - admin only"""
    if not is_admin_user(current_user):
        flash('You do not have permission to edit users.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Replace get_or_404 for User
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    
    roles = Role.query.all()
    sites = Site.query.all()
    
    if request.method == 'POST':
        log_security_event(
            event_type="admin_user_edit",
            details=f"User {user_id} edited by {getattr(current_user, 'username', None)}. Data: {request.form}",
            is_critical=True
        )
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            full_name = request.form.get('full_name', '')
            role_id = request.form.get('role_id')
            
            # Check if username already exists for another user
            existing_user = User.query.filter(User.username == username, User.id != user_id).first()
            if existing_user:
                flash(f'Username "{username}" is already taken.', 'danger')
                return redirect(url_for('edit_user', user_id=user_id))
                
            # Check if email already exists for another user  
            existing_user = User.query.filter(User.email == email, User.id != user_id).first()
            if existing_user:
                flash(f'Email "{email}" is already registered.', 'danger')
                return redirect(url_for('edit_user', user_id=user_id))
            
            # Update user details
            user.username = username
            user.email = email
            user.full_name = full_name
            
            # More direct approach to role assignment
            old_role_name = user.role.name if user.role else "None"
            
            if role_id:
                # Find the role and assign it directly
                role = db.session.get(Role, int(role_id))
                if role:
                    # Force detach from previous role
                    user.role_id = None
                    db.session.flush()
                    # Assign new role
                    user.role = role
                    user.role_id = role.id
                    new_role_name = role.name
                else:
                    new_role_name = "None (role not found)"
            else:
                # Clear role if none selected
                user.role = None
                user.role_id = None
                new_role_name = "None"
            
            # Update site assignments if provided
            if 'site_ids' in request.form:
                # Clear existing site associations
                user.sites = []
                
                # Add selected sites
                site_ids = request.form.getlist('site_ids')
                for site_id in site_ids:
                    site = Site.query.get(int(site_id))
                    if site:
                        user.sites.append(site)
            
            # Force immediate commit to database
            db.session.commit()
            # Log to sync queue
            add_to_sync_queue_enhanced('users', user.id, 'update', {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role_id': user.role_id
            })
            # Log all site assignments for this user
            for site in user.sites:
                add_to_sync_queue_enhanced('user_sites', f'{user.id}_{site.id}', 'update', {
                    'user_id': user.id,
                    'site_id': site.id
                })
            # Log role change for debugging
            app.logger.info(f"User {user.username} role changed: {old_role_name} -> {new_role_name}")
            flash(f'User "{username}" updated successfully. Role changed from "{old_role_name}" to "{new_role_name}".', 'success')
            # Force session clear before redirect to ensure fresh data on next page load
            db.session.expire_all()
            return redirect(url_for('admin_users'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating user: {e}")
            flash(f'Error updating user: {str(e)}', 'danger')

    
    # For GET request, show the edit form
    return render_template('edit_user.html', 
                          user=user,
                          roles=roles,
                          sites=sites,
                          assigned_sites=[site.id for site in user.sites])

@app.route('/admin/roles', methods=['GET', 'POST'])
@login_required
def admin_roles():
    from security_event_logger import log_security_event
    """Redirect or render the roles management page."""
    if not is_admin_user(current_user):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Handle form submission for creating a new role
    if request.method == 'POST':
        log_security_event(
            event_type="admin_role_change",
            details=f"Role change by {getattr(current_user, 'username', None)}. Data: {request.form}",
            is_critical=True
        )
        try:
            name = request.form.get('name')
            description = request.form.get('description', '')
            permissions = request.form.getlist('permissions')
            
            # Validate required fields
            if not name:
                flash('Role name is required.', 'danger')
                return redirect(url_for('admin_roles'))
            
            # Check if role name already exists
            if Role.query.filter_by(name=name).first():
                flash(f'A role with the name "{name}" already exists.', 'danger')
                return redirect(url_for('admin_roles'))
            
            # Create new role
            new_role = Role(
                name=name,
                description=description,
                permissions=','.join(permissions) if permissions else ''
            )
            
            # Add role to database
            db.session.add(new_role)
            db.session.commit()
            # Log to sync queue
            add_to_sync_queue_enhanced('roles', new_role.id, 'insert', {
                'id': new_role.id,
                'name': new_role.name,
                'description': new_role.description,
                'permissions': new_role.permissions
            })
            flash(f'Role "{name}" created successfully.', 'success')
            return redirect(url_for('admin_roles'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creating role: {e}")
            flash(f'Error creating role: {str(e)}', 'danger')
    
    # For GET requests or after POST processing
    roles = Role.query.all()
    all_permissions = get_all_permissions()
    return render_template('admin/roles.html', roles=roles, all_permissions=all_permissions)

@app.route('/manage/roles')
@login_required
def manage_roles():
    """Redirect to admin roles page for compatibility."""
    return redirect(url_for('admin_roles'))

@app.route('/machines/delete/<int:machine_id>', methods=['POST'])
@login_required
def delete_machine(machine_id):
    """Delete a machine."""
    try:
        # Replace get_or_404 for Machine
        machine = db.session.get(Machine, machine_id)
        if not machine:
            abort(404)
        
        # Check for associated maintenance records and parts before deleting
        maintenance_records = MaintenanceRecord.query.filter_by(machine_id=machine_id).all()
        parts = Part.query.filter_by(machine_id=machine_id).all()
        
        if maintenance_records:
            flash(f'Cannot delete machine: It has {len(maintenance_records)} maintenance records. Delete those first.', 'danger')
        elif parts:
            flash(f'Cannot delete machine: It has {len(parts)} associated parts. Delete or reassign those first.', 'danger')
        else:
            db.session.delete(machine)
            db.session.commit()
            # Log to sync queue
            add_to_sync_queue_enhanced('machines', machine_id, 'delete', {'id': machine_id})
            flash(f'Machine "{machine.name}" deleted successfully.', 'success')
        
        return redirect(url_for('manage_machines'))
    except Exception as e:
        app.logger.error(f"Error deleting machine: {e}")
        flash('An error occurred while deleting the machine.', 'danger')
        return redirect(url_for('manage_machines'))

@app.route('/parts/delete/<int:part_id>', methods=['POST'])
@login_required
def delete_part(part_id):
    """Delete a part."""
    try:
        # Replace get_or_404 for Part
        part = db.session.get(Part, part_id)
        if not part:
            abort(404)
        
        # Delete the part
        db.session.delete(part)
        db.session.commit()
        # Log to sync queue
        add_to_sync_queue_enhanced('parts', part_id, 'delete', {'id': part_id})
        flash(f'Part "{part.name}" deleted successfully.', 'success')
        
        return redirect(url_for('manage_parts'))
    except Exception as e:
        app.logger.error(f"Error deleting part: {e}")
        flash('An error occurred while deleting the part.', 'danger')
        return redirect(url_for('manage_parts'))

@app.route('/sites/delete/<int:site_id>', methods=['POST'])
@login_required
def delete_site(site_id):
    """Delete a site."""
    try:
        # Replace get_or_404 for Site
        site = db.session.get(Site, site_id)
       
        if not site:
            abort(404)
        
        # Check for associated machines before deleting
        machines = Machine.query.filter_by(site_id=site_id).all()
        
        if machines:
            flash(f'Cannot delete site: It has {len(machines)} associated machines. Delete or reassign those first.', 'danger')
        else:
            db.session.delete(site)
            db.session.commit()
            # Log to sync queue
            add_to_sync_queue_enhanced('sites', site_id, 'delete', {'id': site_id})
            flash(f'Site "{site.name}" deleted successfully.', 'success')
        
        return redirect(url_for('manage_sites'))
    except Exception as e:
        app.logger.error(f"Error deleting site: {e}")
        db.session.rollback()
        flash('An error occurred while deleting the site.', 'danger')
        return redirect(url_for('manage_sites'))

@app.route('/part/<int:part_id>/history')
@login_required
def part_history_route(part_id):
    part = db.session.get(Part, part_id)
    if not part:
        abort(404)
    machine = part.machine
    site = part.machine.site if part.machine else None
    maintenance_records = MaintenanceRecord.query.filter_by(part_id=part_id).order_by(MaintenanceRecord.date.desc()).all()
    return render_template('part_history.html', part=part, machine=machine, site=site, maintenance_records=maintenance_records, now=datetime.now())

# --- MAINTENANCE DATE UPDATE AND HISTORY FIXES ---
@login_required
def part_history(part_id):
    part = db.session.get(Part, part_id)
    if not part:
        abort(404)
    machine = part.machine
    site = part.machine.site if part.machine else None
    maintenance_records = MaintenanceRecord.query.filter_by(part_id=part_id).order_by(MaintenanceRecord.date.desc()).all()
    return render_template('part_history.html', part=part, machine=machine, site=site, maintenance_records=maintenance_records, now=datetime.now())

@app.route('/machine/<int:machine_id>/history')
@login_required
def machine_history_view(machine_id):
    machine = db.session.get(Machine, machine_id)
    if not machine:
        abort(404)
    site = machine.site
    parts = Part.query.filter_by(machine_id=machine_id).all()
    # Gather all maintenance records for all parts in this machine
    maintenance_records = MaintenanceRecord.query.filter(MaintenanceRecord.part_id.in_([p.id for p in parts])).order_by(MaintenanceRecord.date.desc()).all()
    return render_template('machine_history.html', machine=machine, site=site, parts=parts, maintenance_records=maintenance_records, now=datetime.now())

@app.route('/site/<int:site_id>/history')
@login_required
def site_history(site_id):
    site = db.session.get(Site, site_id)
    if not site:
        abort(404)
    machines = Machine.query.filter_by(site_id=site_id).all()
    parts = []
    for machine in machines:
        parts.extend(Part.query.filter_by(machine_id=machine.id).all())
    # Gather all maintenance records for all parts in this site
    maintenance_records = MaintenanceRecord.query.filter(MaintenanceRecord.part_id.in_([p.id for p in parts])).order_by(MaintenanceRecord.date.desc()).all()
    return render_template('site_history.html', site=site, machines=machines, parts=parts, maintenance_records=maintenance_records, now=datetime.now())
# --- END MAINTENANCE HISTORY FIXES ---

@app.route('/role/delete/<int:role_id>', methods=['POST'])
@login_required
def delete_role(role_id):
    """Delete a role - admin only."""
    if not is_admin_user(current_user):
        flash('You do not have permission to delete roles.', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        # Replace get_or_404 for Role
        role = db.session.get(Role, role_id)
        if not role:
            abort(404)
        
        # Check if the role is assigned to any users before deleting
        # Using role_id comparison instead of comparing objects directly
        users_with_role = User.query.filter_by(role_id=role_id).all()
        
        if users_with_role:
            flash(f'Cannot delete role: It is assigned to {len(users_with_role)} users. Reassign those users first.', 'danger')
        else:
            db.session.delete(role)
            db.session.commit()
            # Log to sync queue
            add_to_sync_queue_enhanced('roles', role_id, 'delete', {'id': role_id})
            flash(f'Role "{role.name}" has been deleted successfully.', 'success')
        return redirect('/admin/roles')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting role: {e}")
        flash('An error occurred while deleting the role.', 'danger')
        return redirect('/admin/roles')

@app.route('/user/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete a user - admin only."""
    if not is_admin_user(current_user):
        flash('You do not have permission to delete users.', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        # Don't allow deleting your own account
        if user_id == current_user.id:
            flash('You cannot delete your own account.', 'danger')
            return redirect('/admin/users')
            
        # Replace get_or_404 for User
        user = db.session.get(User, user_id)
        if not user:
            abort(404)
        
        # Don't allow deleting the main admin account
        if user.username == 'admin':
            flash('The main admin account cannot be deleted.', 'danger')
            return redirect('/admin/users')
            
        db.session.delete(user)
        db.session.commit()
        # Log to sync queue
        add_to_sync_queue_enhanced('users', user_id, 'delete', {'id': user_id})
        flash(f'User "{user.username}" has been deleted successfully.', 'success')
        
        return redirect('/admin/users')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting user: {e}")
        flash('An error occurred while deleting the user.', 'danger')
        return redirect('/admin/users')

@app.route('/maintenance', methods=['GET', 'POST'])
@login_required
def maintenance_page():
    try:
        # Allow admins and users with 'maintenance.record' permission to see all sites
        def has_maintenance_record_permission(user):
            if getattr(user, 'is_admin', False):
                return True
            if hasattr(user, 'role') and user.role and user.role.permissions:
                return 'maintenance.record' in user.role.permissions.split(',')
            return False

        if current_user.is_admin or has_maintenance_record_permission(current_user):
            sites = Site.query.all()
        else:
            # fallback: only assigned sites
            sites = getattr(current_user, 'sites', [])

        # Get all machines, parts, and sites for the form
        site_ids = [site.id for site in sites] if sites else []
        machines = Machine.query.filter(Machine.site_id.in_(site_ids)).all() if site_ids else []
        machine_ids = [machine.id for machine in machines] if machines else []
        parts = Part.query.filter(Part.machine_id.in_(machine_ids)).all() if machine_ids else []
        
        # Get all maintenance records with related data
        maintenance_records = MaintenanceRecord.query.filter(MaintenanceRecord.machine_id.in_(machine_ids)).order_by(MaintenanceRecord.date.desc()).all() if machine_ids else []
        
        # Handle form submission for adding new maintenance records
        if request.method == 'POST':
            machine_id = request.form.get('machine_id')
            part_id = request.form.get('part_id')
            user_id = current_user.id
            maintenance_type =request.form.get('maintenance_type')
            description = request.form.get('description')
            date_str = request.form.get('date')
            performed_by = request.form.get('performed_by', '')
            status = request.form.get('status', 'completed')
            notes = request.form.get('notes', '')
            client_id = request.form.get('client_id')
            parts_used = request.form.getlist('parts_used')

            # Validate and cast to int
            try:
                machine_id = int(machine_id)
                part_id = int(part_id)
                user_id = int(user_id)
            except (TypeError, ValueError):
                flash('Invalid machine, part, or user selection.', 'danger')
                return redirect(url_for('maintenance_page'))

            # Validate required fields
            if not machine_id or not part_id or not user_id or not maintenance_type or not description or not date_str:
                flash('Machine, part, user, maintenance type, description, and date are required!', 'danger')
                return redirect(url_for('maintenance_page'))
            else:
                try:
                    maintenance_date = datetime.strptime(date_str, '%Y-%m-%d')
                    new_record = MaintenanceRecord(
                        machine_id=machine_id,
                        part_id=part_id,
                        user_id=user_id,
                        maintenance_type=maintenance_type,
                        description=description,
                        date=maintenance_date,
                        performed_by=performed_by,
                        status=status,
                        notes=notes,
                        client_id=client_id if client_id else None
                    )
                    db.session.add(new_record)

                    # Save uploaded files
                    files = request.files.getlist('maintenance_files')
                    import os
                    from werkzeug.utils import secure_filename
                    upload_folder = get_upload_folder_path()
                    for file in files:
                        if file and file.filename:
                            filename = secure_filename(file.filename)
                            filepath = os.path.join(upload_folder, filename)
                            # Ensure unique filename
                            base, ext = os.path.splitext(filename)
                            counter = 1
                            while os.path.exists(filepath):
                                filename = f"{base}_{counter}{ext}"
                                filepath = os.path.join(upload_folder, filename)
                                counter += 1
                            file.save(filepath)
                            filetype = file.mimetype
                            filesize = os.path.getsize(filepath)
                            maintenance_file = MaintenanceFile(
                                maintenance_record=new_record,
                                filename=filename,
                                filepath=filepath,
                                filetype=filetype,
                                filesize=filesize
                            )
                            db.session.add(maintenance_file)

                    # Update part's last_maintenance and next_maintenance
                    part = Part.query.get(part_id)
                    if part:
                        part.last_maintenance = maintenance_date
                        freq = part.maintenance_frequency or 1
                        unit = part.maintenance_unit or 'day'
                        if unit == 'week':
                            delta = timedelta(weeks=freq)
                        elif unit == 'month':
                            delta = timedelta(days=freq * 30)
                        elif unit == 'year':
                            delta = timedelta(days=freq * 365)
                        else:
                            delta = timedelta(days=freq)
                        part.next_maintenance = maintenance_date + delta
                        db.session.add(part)
                    db.session.commit()
                    # Log to sync queue
                    add_to_sync_queue_enhanced('maintenance_records', new_record.id, 'insert', {
                        'id': new_record.id,
                        'machine_id': new_record.machine_id,
                        'part_id': new_record.part_id,
                        'user_id': new_record.user_id,
                        'maintenance_type': new_record.maintenance_type,
                        'description': new_record.description,
                        'date': str(new_record.date),
                        'performed_by': new_record.performed_by,
                        'status': new_record.status,
                        'notes': new_record.notes,
                        'client_id': new_record.client_id
                    })
                    flash('Maintenance record and files added successfully!', 'success')
                    return redirect(url_for('maintenance_page'))
                except ValueError:
                    flash('Invalid date format! Use YYYY-MM-DD.', 'danger')
        
        # Ensure all context variables are strings for template/JS compatibility
        site_id = request.args.get('site_id') or request.form.get('site_id') or ''
        machine_id = request.args.get('machine_id') or request.form.get('machine_id') or ''
        part_id = request.args.get('part_id') or request.form.get('part_id') or ''
        site_id = str(site_id) if site_id else ''
        machine_id = str(machine_id) if machine_id else ''
        part_id = str(part_id) if part_id else ''
        return render_template(
            'maintenance.html',
            maintenance_records=maintenance_records,
            machines=machines,
            parts=parts,
            sites=sites,
            site_id=site_id,
            machine_id=machine_id,
            part_id=part_id
        )
    except Exception as e:
        app.logger.error(f"Error in maintenance_page: {e}")
        print("[MAINTENANCE ERROR] Exception occurred in maintenance_page:")
        traceback.print_exc()
        flash('An error occurred while loading maintenance records.', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/update-maintenance', methods=['POST'])
@login_required
def update_maintenance_alt():
    try:
        part_id = request.form.get('part_id')
        comments = request.form.get('comments', '')
        if not part_id:
            flash('Missing part ID', 'error')
            return redirect(url_for('maintenance_page'))
        part = Part.query.get_or_404(int(part_id))
        now = datetime.now()
        # Update the last maintenance date
        part.last_maintenance = now
        # Calculate next maintenance date based on frequency and unit
        freq = part.maintenance_frequency or 1
        unit = part.maintenance_unit or 'day'
        if unit == 'week':
            delta = timedelta(weeks=freq)
        elif unit == 'month':
            delta = timedelta(days=freq * 30)
        elif unit == 'year':
            delta = timedelta(days=freq * 365)
        else:
            delta = timedelta(days=freq)
        part.next_maintenance = now + delta
        # Create a maintenance record
        maintenance_record = MaintenanceRecord(
            part_id=part.id,
            user_id=current_user.id,
            date=now,
            comments=comments
        )
        db.session.add(maintenance_record)
        db.session.commit()
        # Log to sync queue: maintenance record insert and part update (immediate sync)
        add_to_sync_queue_enhanced('maintenance_records', maintenance_record.id, 'insert', {
            'id': maintenance_record.id,
            'part_id': maintenance_record.part_id,
            'user_id': maintenance_record.user_id,
            'date': maintenance_record.date.isoformat() if maintenance_record.date else None,
            'comments': maintenance_record.comments
        }, immediate_sync=True)
        add_to_sync_queue_enhanced('parts', part.id, 'update', {
            'id': part.id,
            'last_maintenance': part.last_maintenance.isoformat() if part.last_maintenance else None,
            'next_maintenance': part.next_maintenance.isoformat() if part.next_maintenance else None
        }, immediate_sync=True)
        flash(f'Maintenance for "{part.name}" has been recorded successfully.', 'success')
        referrer = request.referrer
        if referrer:
            return redirect(referrer)
        else:
            return redirect(url_for('maintenance_page'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating maintenance: {str(e)}', 'error')
        return redirect(url_for('maintenance_page'))

@app.route('/parts/<int:part_id>/update_maintenance', methods=['GET', 'POST'])
@login_required
def update_maintenance(part_id):
    try:
        part = Part.query.get_or_404(part_id)
        if request.method == 'GET':
            return redirect(url_for('maintenance_page'))
        now = datetime.now()
        part.last_maintenance = now
        
        # Calculate next_maintenance based on part.maintenance_frequency and part.maintenance_unit
        freq = part.maintenance_frequency or 1
        unit = part.maintenance_unit or 'day'
        if unit == 'week':
            delta = timedelta(weeks=freq)
        elif unit == 'month':
            delta = timedelta(days=freq * 30)
        elif unit == 'year':
            delta = timedelta(days=freq * 365)
        else:
            delta = timedelta(days=freq)
            
        # Set the next maintenance date
        part.next_maintenance = now + delta
        
        # Create a maintenance record
        maintenance_record = MaintenanceRecord(
            part_id=part.id,
            user_id=current_user.id,
            date=now,
            comments=request.form.get('comments', ''),
            description=request.form.get('description', None),
            machine_id=part.machine_id
        )
        db.session.add(maintenance_record)
        db.session.commit()
        # Log to sync queue: maintenance record insert and part update
        add_to_sync_queue_enhanced('maintenance_records', maintenance_record.id, 'insert', {
            'id': maintenance_record.id,
            'part_id': maintenance_record.part_id,
            'user_id': maintenance_record.user_id,
            'date': maintenance_record.date.isoformat() if maintenance_record.date else None,
            'comments': maintenance_record.comments,
            'description': maintenance_record.description,
            'machine_id': maintenance_record.machine_id
        })
        add_to_sync_queue_enhanced('parts', part.id, 'update', {
            'id': part.id,
            'last_maintenance': part.last_maintenance.isoformat() if part.last_maintenance else None,
            'next_maintenance': part.next_maintenance.isoformat() if part.next_maintenance else None
        })
        flash(f'Maintenance for "{part.name}" has been updated successfully.', 'success')
        referrer = request.referrer
        if referrer:
            return redirect(referrer)
        else:
            return redirect(url_for('manage_parts', machine_id=part.machine_id))
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating maintenance: {str(e)}', 'error')
        return redirect(url_for('manage_parts'))

@app.route('/machine-history/<int:machine_id>')
@login_required
def machine_history(machine_id):
    """Endpoint for viewing machine maintenance history."""
    try:
        machine = db.session.get(Machine, machine_id)
        if not machine:
            abort(404)
        return redirect(f'/maintenance?machine_id={machine_id}')
    except Exception as e:
        app.logger.error(f"Error in machine_history: {e}")
        flash('An error occurred while accessing the machine history.', 'danger')
        return redirect('/maintenance')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    """View and edit user profile."""
    try:
        user = current_user  # Always use the logged-in user
        if request.method == 'POST':
            form_type = request.form.get('form_type')
            # Profile form submission
            if form_type == 'profile':
                email = request.form.get('email')
                full_name = request.form.get('full_name')
                # Validate email input
                if not email or '@' not in email:
                    flash('Please enter a valid email address.', 'danger')
                    return redirect(url_for('user_profile'))
                email_changed = email != user.email
                # Check if email is already in use by another user
                if email_changed and User.query.filter(User.email == email, User.id != user.id).first():
                    flash('Email is already in use by another account.', 'danger')
                    return redirect(url_for('user_profile'))
                if email_changed:
                    user.email = email
                if full_name is not None:
                    user.full_name = full_name
                try:
                    db.session.add(user)
                    db.session.commit()
                    flash('Profile updated successfully!', 'success')
                except Exception as e:
                    db.session.rollback()
                    app.logger.error(f"Database error updating profile: {e}")
                    flash('Error updating profile.', 'danger')
                return redirect(url_for('user_profile'))
            # Password form submission
            elif form_type == 'password':
                current_password = request.form.get('current_password')
                new_password = request.form.get('new_password')
                confirm_password = request.form.get('confirm_password')
                if not user.password_hash or not check_password_hash(user.password_hash, current_password):
                    flash('Current password is incorrect.', 'danger')
                    return redirect(url_for('user_profile'))
                
                if len(new_password) < 8:
                    flash('New password must be at least 8 characters long.', 'danger')
                    return redirect(url_for('user_profile'))
                
                if new_password != confirm_password:
                    flash('New passwords do not match.', 'danger')
                    return redirect(url_for('user_profile'))
                
                # Update password
                user.password_hash = generate_password_hash(new_password)
                db.session.commit()
                # Log to sync queue
                add_to_sync_queue_enhanced('users', user.id, 'update', {
                    'id': user.id,
                    'password_hash': user.password_hash
                })
                flash('Password updated successfully!', 'success')
                return redirect(url_for('user_profile'))
                
            # Notification preferences form
            elif form_type == 'notifications':
                # Handle notification preferences in a separate route to keep this one cleaner
                return redirect(url_for('update_notification_preferences'))
                
            # Fallback for tests: handle both email and password fields in one POST if form_type is missing
            elif not form_type:
                # Support the test case scenario where all fields are submitted in one request
                email = request.form.get('email')
                if email and email != user.email:
                    # Validate email
                    if '@' not in email:
                        flash('Please enter a valid email address.', 'danger')
                        return redirect(url_for('user_profile'))
                        
                    # Check if email is already in use by another user
                    if User.query.filter(User.email == email, User.username != user.username).first():
                        flash('Email is already in use by another account.', 'danger')
                        return redirect(url_for('user_profile'))
                    # Update the email
                    user.email = email
                    db.session.commit()
                    flash('Email updated successfully', 'success')
                    
                # Handle password update in the same request if provided
                current_password = request.form.get('current_password')
                new_password = request.form.get('new_password')
                confirm_password = request.form.get('confirm_password')
                if current_password and new_password and confirm_password:
                    if not user.password_hash or not check_password_hash(user.password_hash, current_password):
                        flash('Current password is incorrect.', 'danger')
                    elif new_password != confirm_password:
                        flash('New passwords do not match.', 'danger')
                    else:
                        user.password_hash = generate_password_hash(new_password)
                        db.session.commit()
                        # Log to sync queue
                        add_to_sync_queue_enhanced('users', user.id, 'update', {
                            'id': user.id,
                            'password_hash': user.password_hash
                        })
                        flash('Password updated successfully', 'success')
                
                return redirect(url_for('user_profile'))
            
            # Unknown form type
            else:
                flash('Unknown form submission type.', 'danger')
                return redirect(url_for('user_profile'))

        # Fetch notification preferences for GET request
        notification_preferences = user.get_notification_preferences() if hasattr(user, 'get_notification_preferences') else {}
        
        # Get user's sites for notification preferences display
        user_sites = user.sites if hasattr(user, 'sites') else []
        
        return render_template('user_profile.html', user=user, notification_preferences=notification_preferences, user_sites=user_sites)
    except Exception as e:
        app.logger.error(f"Error in user_profile: {e}")
        flash('An error occurred while loading your profile.', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile."""
    try:
        # Handle profile updates
        user = current_user
        if request.form.get('email'):
            user.email = request.form.get('email')
        if request.form.get('full_name'):
            user.full_name = request.form.get('full_name')
        
        db.session.commit()
        # Log to sync queue
        add_to_sync_queue_enhanced('users', user.id, 'update', {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name
        })
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('user_profile'))
    except Exception as e:
        app.logger.error(f"Error updating profile: {e}")
        flash('An error occurred while updating your profile.', 'error')
        return redirect(url_for('user_profile'))

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """Handle password change requests."""
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate inputs
        if not current_password or not new_password or not confirm_password:
            flash('All password fields are required.', 'danger')
            return redirect(url_for('user_profile'))
        
        # Check current password
        if not current_user.password_hash or not check_password_hash(current_user.password_hash, current_password):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('user_profile'))
        
        # Validate new password
        if len(new_password) < 8:
            flash('New password must be at least 8 characters long.', 'danger')
            return redirect(url_for('user_profile'))
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return redirect(url_for('user_profile'))
        
        # Update password
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash('Password updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error changing password: {e}")
        flash('An error occurred while changing your password.', 'error')
    
    return redirect(url_for('user_profile'))

@app.route('/update_notification_preferences', methods=['POST'])
@login_required
def update_notification_preferences():
    user = current_user
    prefs = user.get_notification_preferences() if hasattr(user, 'get_notification_preferences') else {}
    
    # Process general notification settings
    enable_email = request.form.get('enable_email') == 'on'
    notification_frequency = request.form.get('notification_frequency', 'weekly')
    email_format = request.form.get('email_format', 'html')
    audit_reminders = request.form.get('audit_reminders') == 'on'
    
    # Validate notification frequency option
    valid_frequencies = ['immediate', 'daily', 'weekly', 'monthly', 'none']
    if notification_frequency not in valid_frequencies:
        notification_frequency = 'weekly'  # Default to weekly if invalid
    
    # 'none' disables email notifications
    if notification_frequency == 'none':
        enable_email = False
    
    # Update preferences
    prefs['enable_email'] = enable_email
    prefs['notification_frequency'] = notification_frequency
    prefs['email_format'] = email_format
    prefs['audit_reminders'] = audit_reminders
    
    # Process site-specific notification preferences
    site_notifications = {}
    for site in current_user.sites:
        key = f'site_notify_{site.id}'
        site_notifications[str(site.id)] = key in request.form
    
    prefs['site_notifications'] = site_notifications
    
    # Save preferences to user
    if hasattr(user, 'set_notification_preferences'):
        user.set_notification_preferences(prefs)
        db.session.commit()  # Ensure changes are saved
        # Log to sync queue
        add_to_sync_queue_enhanced('users', user.id, 'update', {
            'id': user.id,
            'notification_preferences': prefs
        })
        flash('Notification preferences updated successfully.', 'success')
    else:
        flash('Unable to save notification preferences.', 'danger')
    
    return redirect(url_for('user_profile'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle userlogin."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        app.logger.debug(f"Login attempt: username={username}, remember={remember}")
        
        # Debug: print login attempt
        print(f"[LOGIN DEBUG] Login attempt for username: {username}")
        user = None
        try:
            app.logger.debug(f"Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'NOT SET')}")
            # Try the normal SQLAlchemy query first
            user = User.query.filter_by(username_hash=hash_value(username)).first()
            print(f"[LOGIN DEBUG] User found by username_hash: {user}")
        except Exception as e:
            app.logger.error(f"SQLAlchemy error during login: {e}")
            # Fallback to direct database query
            try:
                from sqlalchemy import create_engine, text
                from werkzeug.security import check_password_hash as check_pw_hash
                engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
                with engine.connect() as conn:
                    result = conn.execute(
                        text("SELECT id, username_hash, password_hash FROM users WHERE username_hash = :hash LIMIT 1"),
                        {"hash": hash_value(username)}
                    ).first()
                    print(f"[LOGIN DEBUG] Raw DB result: {result}")
                    if result and check_pw_hash(result[2], password):  # Check password directly
                        print(f"[LOGIN DEBUG] Password check passed for user_id {result[0]}")
                        user = User.query.get(result[0])  # Get full user object by ID
                        if not user:
                            # If that fails too, create a temporary user object
                            class TempUser:
                                def __init__(self, user_id):
                                    self.id = user_id
                                    self.is_authenticated = True
                                    self.is_active = True
                                    self.is_anonymous = False
                                def get_id(self):
                                    return str(self.id)
                            user = TempUser(result[0])
                    else:
                        print(f"[LOGIN DEBUG] Password check failed or user not found in fallback query.")
                        user = None
            except Exception as e2:
                app.logger.error(f"Direct database error during login: {e2}")
                print(f"[LOGIN DEBUG] Direct DB error: {e2}")
                flash('Login system temporarily unavailable. Please try again.', 'danger')
                return render_template('login.html')
            
        from security_event_logger import log_security_event
        # Debug: print password hash and check result
        if user:
            try:
                print(f"[LOGIN DEBUG] Password hash in DB: {getattr(user, 'password_hash', None)}")
                pw_check = check_password_hash(user.password_hash, password)
                print(f"[LOGIN DEBUG] Password check result: {pw_check}")
            except Exception as e:
                print(f"[LOGIN DEBUG] Error during password check: {e}")
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            user.set_remember_preference(remember)
            log_security_event(
                event_type="login_success",
                details=f"Login from IP: {request.remote_addr} (username: {username})"
            )
            # Detect new device/IP (simple version: always log, can be improved)
            log_security_event(
                event_type="login_new_device_or_ip",
                details=f"Login from new device/IP: {request.remote_addr} (username: {username})"
            )
            if remember:
                token = user.generate_remember_token()
                db.session.commit()
                resp = redirect(request.args.get('next') or url_for('dashboard'))
                resp.set_cookie('remember_token', token, max_age=30*24*60*60, httponly=True, samesite='Lax')
                app.logger.debug(f"Remember token set for user_id={user.id}")
                return resp
            else:
                user.clear_remember_token()
                db.session.commit()
            app.logger.debug(f"Login successful: user_id={user.id}, username={user.username}")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            if user:
                app.logger.debug(f"Login failed: Invalid password for username={username}")
            else:
                app.logger.debug(f"Login failed: No user found with username={username}")
            log_security_event(
                event_type="login_failed",
                details=f"Failed login attempt for username: {username} from IP: {request.remote_addr}"
            )
            flash('Invalid username or password', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    from security_event_logger import log_security_event
    remote_addr = request.remote_addr or request.headers.get('X-Forwarded-For', 'unknown')
    user_id = getattr(current_user, 'id', None)
    username = getattr(current_user, 'username', None)
    event_context = {
        'ip': remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
    }
    log_security_event(
        event_type="logout",
        user_id=user_id,
        username=username,
        context=event_context,
        message="User logged out."
    )
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle password reset request."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email_hash=hash_value(email)).first()
        remote_addr = request.remote_addr or request.headers.get('X-Forwarded-For', 'unknown')
        event_context = {
            'ip': remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'email': email,
        }
        if user:
            # Generate a password reset token
            reset_token = secrets.token_urlsafe(32)
            expires = datetime.now() + timedelta(hours=24)
            # Store token in database
            user.reset_token = reset_token
            user.reset_token_expiration = expires
            db.session.commit()
            # Log password reset request (success)
            log_security_event(
                event_type="password_reset_requested",
                user_id=user.id,
                username=getattr(user, 'username', None),
                context=event_context,
                message="Password reset requested. Token generated."
            )
            # In a production app, you would send an email with the reset link
            reset_url = url_for('reset_password', token=reset_token, _external=True)
            flash(f'Password reset link: {reset_url}', 'info')
        else:
            # Log password reset request (unknown email)
            log_security_event(
                event_type="password_reset_requested_unknown_email",
                user_id=None,
                username=None,
                context=event_context,
                message="Password reset requested for unknown email."
            )
        # Always show this message to prevent user enumeration
        flash('If an account with that email exists, a password reset link has been sent.', 'info')
        return redirect(url_for('login'))
    return render_template('forgot_password.html') if os.path.exists(os.path.join('templates', 'forgot_password.html')) else '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Forgot Password</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Reset Password</div>
                        <div class="card-body">
                            <form method="post">
                                <div class="mb-3">
                                    <label for="email" class="form-label">Email</label>
                                    <input type="email" class="form-control" id="email" name="email" required>
                                </div>
                                <button type="submit" class="btn btn-primary">Send Reset Link</button>
                            </form>
                            <div class="mt-3">
                                <a href="/login" class="text-decoration-none">Back to Login</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    user = User.query.filter_by(reset_token=token).first()
    remote_addr = request.remote_addr or request.headers.get('X-Forwarded-For', 'unknown')
    event_context = {
        'ip': remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'token': token,
        'user_id': getattr(user, 'id', None) if user else None,
    }
    # Check if token is valid and not expired
    if not user or (user.reset_token_expiration and user.reset_token_expiration < datetime.now()):
        log_security_event(
            event_type="password_reset_token_invalid",
            user_id=None,
            username=None,
            context=event_context,
            message="Password reset link invalid or expired."
        )
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if not password or len(password) < 8:
            log_security_event(
                event_type="password_reset_failed_short_password",
                user_id=user.id,
                username=getattr(user, 'username', None),
                context=event_context,
                message="Password reset failed: password too short."
            )
            flash('Password must be at least 8 characters long.', 'danger')
            return redirect(url_for('reset_password', token=token))
        elif password != confirm_password:
            log_security_event(
                event_type="password_reset_failed_mismatch",
                user_id=user.id,
                username=getattr(user, 'username', None),
                context=event_context,
                message="Password reset failed: passwords do not match."
            )
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('reset_password', token=token))
        else:
            # Update password and clear reset token
            user.password_hash = generate_password_hash(password)
            user.reset_token = None
            user.reset_token_expiration = None
            db.session.commit()
            log_security_event(
                event_type="password_reset_success",
                user_id=user.id,
                username=getattr(user, 'username', None),
                context=event_context,
                message="Password reset successful."
            )
            flash('Your password has been updated. Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('reset_password.html', token=token) if os.path.exists(os.path.join('templates', 'reset_password.html')) else '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Reset Password</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
    <body style="font-family:Arial; text-align:center; padding:50px;">
            <h1 style="color:#FE7900;">Reset Password</h1>
            <form method="post">
                <div class="mb-3">
                    <label for="password" class="form-label">New Password</label>
                    <input type="password" class="form-control" id="password" name="password" required>
                </div>
                <div class="mb-3">
                    <label for="confirm_password" class="form-label">Confirm Password</label>
                    <input type="password" class="form-control" id="confirm_password" name="confirm_password" required>
                </div>
                <button type="submit" class="btn btn-primary">Reset Password</button>
            </form>
        </body>
        </html>
        '''

@app.route('/debug-info')
def debug_info():
    """Display debug information including all available routes."""
    if not app:
        if not app.debug:
            return "Debug mode is disabled", 403
        
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': ','.join(rule.methods),
            'route': str(rule)
        })
    return render_template('debug_info.html', routes=routes) if os.path.exists(os.path.join('templates', 'debug_info.html')) else jsonify(routes=routes)

@app.route('/api/sync/status', methods=['GET'])
def sync_status():
    """Get synchronization status information."""
    try:
        # Basic information about the server state
        return jsonify({
            'status': 'online',
            'server_time': get_timezone_aware_now().isoformat(),
            'version': '1.0.0',
            'timezone': 'America/New_York'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/sync/trigger', methods=['POST'])
def api_trigger_manual_sync():
    """API endpoint to trigger manual sync."""
    try:
        print("[API] Manual sync trigger requested")
        
        # Check if this is an offline client that should upload to server
        if should_trigger_sync(force_override_cooldown=True):
            print("[API] Offline client - triggering enhanced upload")
            # Run enhanced sync upload in a separate thread to avoid blocking
            import threading
            def run_enhanced_sync():
                try:
                    from sync_utils_enhanced import enhanced_upload_pending_sync_queue
                    result = enhanced_upload_pending_sync_queue()
                    print(f"[API] Enhanced upload completed: {result}")
                except Exception as sync_error:
                    print(f"[API] Enhanced upload failed: {sync_error}")
            
            # Start sync in background
            sync_thread = threading.Thread(target=run_enhanced_sync, daemon=True)
            sync_thread.start()
            
            return jsonify({"status": "triggered", "message": "Enhanced sync upload started"})
        else:
            # This is either an online server or sync is not eligible (cooldown, etc.)
            print("[API] Not triggering enhanced sync - running traditional sync")
            import threading
            def run_sync():
                try:
                    result = trigger_manual_sync()
                    print(f"[API] Manual sync completed: {result}")
                except Exception as sync_error:
                    print(f"[API] Manual sync failed: {sync_error}")
            
            # Start sync in background to prevent SocketIO blocking
            sync_thread = threading.Thread(target=run_sync, daemon=True)
            sync_thread.start()
            
            return jsonify({"status": "triggered", "message": "Sync started in background"})
            
    except Exception as e:
        print(f"[API] Manual sync trigger error: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500



# --- API AUTHENTICATION HELPER ---
def check_api_auth():
    """Check authentication for API endpoints - supports both session and basic auth."""
    # Check session-based authentication first
    if current_user.is_authenticated and is_admin_user(current_user):
        print(f"[API AUTH] Session auth successful for user: {current_user.username}")
        return True
    
    # Check basic authentication for API access
    auth = request.authorization
    if auth and auth.username and auth.password:
        print(f"[API AUTH] Attempting basic auth for username: {auth.username}")
        try:
            # Try encrypted username lookup first
            user = User.query.filter_by(_username=encrypt_value(auth.username)).first()
            if not user:
                print(f"[API AUTH] No user found with encrypted username, trying plain username")
                # Fallback to plain username lookup (for older records)
                user = User.query.filter_by(username=auth.username).first()
            
            if not user:
                print(f"[API AUTH] No direct match found, checking all users for decryption match")
                # If no direct match, try to find user by decrypting all usernames
                all_users = User.query.all()
                for candidate_user in all_users:
                    try:
                        # Try to decrypt the stored username and see if it matches
                        if candidate_user.username == auth.username:
                            user = candidate_user
                            print(f"[API AUTH] Found user via decryption match: {auth.username}")
                            break
                    except:
                        # Skip users whose usernames can't be decrypted
                        continue
            
            if user:
                print(f"[API AUTH] Found user: {user.username}, checking password and admin status")
                password_valid = user.check_password(auth.password)
                is_admin = is_admin_user(user)
                print(f"[API AUTH] Password valid: {password_valid}, Is admin: {is_admin}")
                
                if password_valid and is_admin:
                    print(f"[API AUTH] Basic auth successful for user: {user.username}")
                    return True
            else:
                print(f"[API AUTH] No user found for username: {auth.username}")
        except Exception as e:
            print(f"[API AUTH] Error checking basic auth: {e}")
    else:
        print(f"[API AUTH] No basic auth credentials provided")
    
    print(f"[API AUTH] Authentication failed")
    return False

def check_sync_auth():
    """Check authentication specifically for sync endpoints - allows sync service users."""
    # Check session-based authentication first (admin users)
    if current_user.is_authenticated and is_admin_user(current_user):
        print(f"[SYNC AUTH] Session auth successful for admin: {current_user.username}")
        return True
    
    # Check basic authentication for sync access
    auth = request.authorization
    if auth and auth.username and auth.password:
        print(f"[SYNC AUTH] Attempting basic auth for username: {auth.username}")
        try:
            # Try encrypted username lookup first
            user = User.query.filter_by(_username=encrypt_value(auth.username)).first()
            if not user:
                # Fallback to plain username lookup (for older records)
                user = User.query.filter_by(username=auth.username).first()
            
            if not user:
                # If no direct match, try to find user by decrypting all usernames
                all_users = User.query.all()
                for candidate_user in all_users:
                    try:
                        if candidate_user.username == auth.username:
                            user = candidate_user
                            break
                    except:
                        continue
            
            if user:
                password_valid = user.check_password(auth.password)
                is_admin = is_admin_user(user)
                has_sync_permission = user_has_sync_permission(user)
                
                print(f"[SYNC AUTH] User: {user.username}, Password valid: {password_valid}, Is admin: {is_admin}, Has sync permission: {has_sync_permission}")
                
                if password_valid and (is_admin or has_sync_permission):
                    print(f"[SYNC AUTH] Basic auth successful for user: {user.username}")
                    return True
            else:
                print(f"[SYNC AUTH] No user found for username: {auth.username}")
        except Exception as e:
            print(f"[SYNC AUTH] Error checking basic auth: {e}")
    
    print(f"[SYNC AUTH] Authentication failed")
    return False

def user_has_sync_permission(user):
    """Check if user has sync service permissions (read-only sync access)."""
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    
    # Check if user has a role with sync permissions
    if hasattr(user, 'role') and user.role:
        role_name = getattr(user.role, 'name', '').lower()
        permissions = getattr(user.role, 'permissions', '')
        
        # Allow "Sync Service" role or users with 'sync.read' permission
        if role_name in ['sync service', 'sync_service', 'data_sync']:
            return True
        if 'sync.read' in permissions or 'data.read.all' in permissions:
            return True
    
    return False

# --- SYNC ENDPOINT FOR OFFLINE USAGE ---
@app.route('/api/sync/data', methods=['GET', 'POST'])
def sync_data():
    """Two-way sync endpoint: GET returns all data, POST accepts pushed data from offline clients. Requires admin or sync service permissions."""
    if not check_sync_auth():
        return jsonify({'error': 'Unauthorized - Admin or sync service permissions required'}), 403
    if request.method == 'GET':
        try:
            # Import datetime at function scope for availability throughout
            from datetime import datetime
            
            # Check for incremental sync parameter
            since_timestamp = request.args.get('since')
            is_incremental = since_timestamp is not None
            
            if is_incremental:
                try:
                    # Parse the timestamp for filtering
                    since_dt = datetime.fromisoformat(since_timestamp.replace('Z', '+00:00'))
                    print(f"[SYNC] Incremental sync request since: {since_dt}")
                except (ValueError, TypeError) as e:
                    print(f"[SYNC] Invalid timestamp format: {since_timestamp}, falling back to full sync")
                    is_incremental = False
                    since_dt = None
            else:
                since_dt = None
                print("[SYNC] Full sync request (no timestamp)")
            
            # Collect all relevant data with optional timestamp filtering
            users = []
            user_query = User.query
            if is_incremental and since_dt:
                user_query = user_query.filter(User.updated_at > since_dt)
            
            for u in user_query.all():
                user_data = {
                    'id': u.id,
                    'username': u.username,  # Use decrypted value for compatibility
                    'username_hash': getattr(u, 'username_hash', None),
                    'email': u.email,  # Use decrypted value for compatibility
                    'email_hash': getattr(u, 'email_hash', None),
                    'full_name': u.full_name,  # Add full name for proper display
                    'role_id': u.role_id,
                    'is_admin': getattr(u, 'is_admin', False),
                    'active': getattr(u, 'active', True),
                    'created_at': u.created_at.isoformat() if u.created_at else None,
                    'updated_at': u.updated_at.isoformat() if u.updated_at else None,
                }
                # Ensure password_hash is included - critical for offline authentication
                password_hash = getattr(u, 'password_hash', None)
                if password_hash:
                    user_data['password_hash'] = password_hash
                else:
                    # If no password hash is available, we need to handle this gracefully
                    # The offline client should request password reset or use alternative auth
                    user_data['password_hash'] = None
                    user_data['password_reset_required'] = True
                
                users.append(user_data)
            
            roles = []
            role_query = Role.query
            if is_incremental and since_dt:
                role_query = role_query.filter(Role.updated_at > since_dt)
            
            roles = [
                {
                    'id': r.id,
                    'name': r.name,
                    'permissions': r.permissions,
                    'description': getattr(r, 'description', ''),
                    'created_at': r.created_at.isoformat() if getattr(r, 'created_at', None) else None,
                    'updated_at': r.updated_at.isoformat() if getattr(r, 'updated_at', None) else None,
                }
                for r in role_query.all()
            ]
            
            sites = []
            site_query = Site.query
            if is_incremental and since_dt:
                site_query = site_query.filter(Site.updated_at > since_dt)
            
            sites = [
                {
                    'id': s.id,
                    'name': s.name,
                    'location': getattr(s, 'location', ''),
                    'contact_email': getattr(s, 'contact_email', ''),
                    'enable_notifications': getattr(s, 'enable_notifications', True),
                    'notification_threshold': getattr(s, 'notification_threshold', 30),
                    'created_at': s.created_at.isoformat() if getattr(s, 'created_at', None) else None,
                    'updated_at': s.updated_at.isoformat() if getattr(s, 'updated_at', None) else None,
                }
                for s in site_query.all()
            ]
            
            machines = []
            machine_query = Machine.query
            if is_incremental and since_dt:
                machine_query = machine_query.filter(Machine.updated_at > since_dt)
            
            machines = [
                {
                    'id': m.id,
                    'name': m.name,
                    'model': m.model,
                    'serial_number': m.serial_number,
                    'machine_number': m.machine_number,
                    'site_id': m.site_id,
                    'decommissioned': getattr(m, 'decommissioned', False),
                    'decommissioned_date': m.decommissioned_date.isoformat() if getattr(m, 'decommissioned_date', None) else None,
                    'decommissioned_by': getattr(m, 'decommissioned_by', None),
                    'decommissioned_reason': getattr(m, 'decommissioned_reason', ''),
                    'created_at': m.created_at.isoformat() if getattr(m, 'created_at', None) else None,
                    'updated_at': m.updated_at.isoformat() if getattr(m, 'updated_at', None) else None,
                }
                for m in machine_query.all()
            ]
            
            parts = []
            part_query = Part.query
            if is_incremental and since_dt:
                part_query = part_query.filter(Part.updated_at > since_dt)
            
            parts = [
                {
                    'id': p.id,
                    'name': p.name,
                    'description': p.description,
                    'machine_id': p.machine_id,
                    'maintenance_frequency': p.maintenance_frequency,
                    'maintenance_unit': p.maintenance_unit,
                    'maintenance_days': getattr(p, 'maintenance_days', None),
                    'last_maintenance': p.last_maintenance.isoformat() if p.last_maintenance else None,
                    'next_maintenance': p.next_maintenance.isoformat() if p.next_maintenance else None,
                    'created_at': p.created_at.isoformat() if getattr(p, 'created_at', None) else None,
                    'updated_at': p.updated_at.isoformat() if getattr(p, 'updated_at', None) else None,
                }
                for p in part_query.all()
            ]
            
            maintenance_records = []
            maintenance_query = MaintenanceRecord.query
            if is_incremental and since_dt:
                maintenance_query = maintenance_query.filter(MaintenanceRecord.updated_at > since_dt)
            
            maintenance_records = [
                {
                    'id': r.id,
                    'machine_id': r.machine_id,
                    'part_id': r.part_id,
                    'user_id': r.user_id,
                    'maintenance_type': r.maintenance_type,
                    'description': r.description,
                    'date': r.date.isoformat() if r.date else None,
                    'performed_by': r.performed_by,
                    'status': r.status,
                    'notes': r.notes,
                    'comments': getattr(r, 'comments', ''),
                    'created_at': r.created_at.isoformat() if getattr(r, 'created_at', None) else None,
                    'updated_at': r.updated_at.isoformat() if getattr(r, 'updated_at', None) else None,
                }
                for r in maintenance_query.all()
            ]
            # Add audit tasks and completions for comprehensive sync
            audit_tasks = []
            audit_task_query = AuditTask.query
            if is_incremental and since_dt:
                audit_task_query = audit_task_query.filter(AuditTask.updated_at > since_dt)
            
            audit_tasks = [
                {
                    'id': t.id,
                    'name': t.name,
                    'description': getattr(t, 'description', ''),
                    'site_id': t.site_id,
                    'machine_id': getattr(t, 'machine_id', None),
                    'interval': getattr(t, 'interval', 'monthly'),
                    'custom_interval_days': getattr(t, 'custom_interval_days', None),
                    'color': getattr(t, 'color', '#007bff'),
                    'created_at': t.created_at.isoformat() if getattr(t, 'created_at', None) else None,
                    'updated_at': t.updated_at.isoformat() if getattr(t, 'updated_at', None) else None,
                }
                for t in audit_task_query.all()
            ]
            
            audit_task_completions = []
            completion_query = AuditTaskCompletion.query
            if is_incremental and since_dt:
                completion_query = completion_query.filter(AuditTaskCompletion.updated_at > since_dt)
            
            audit_task_completions = [
                {
                    'id': c.id,
                    'audit_task_id': c.audit_task_id,
                    'machine_id': c.machine_id,
                    'user_id': getattr(c, 'completed_by', None),  # Use completed_by as user_id
                    'date': c.date.isoformat() if c.date else None,
                    'completed': getattr(c, 'completed', False),
                    'completed_at': c.completed_at.isoformat() if getattr(c, 'completed_at', None) else None,
                    'notes': getattr(c, 'notes', ''),
                    'created_at': c.created_at.isoformat() if getattr(c, 'created_at', None) else None,
                    'updated_at': c.updated_at.isoformat() if getattr(c, 'updated_at', None) else None,
                }
                for c in completion_query.all()
            ]
            
            # Add machine_audit_task associations - CRITICAL for audit task sync
            from sqlalchemy import inspect, text
            machine_audit_task = []
            inspector = inspect(db.engine)
            if inspector.has_table('machine_audit_task'):
                try:
                    result = db.session.execute(text('SELECT audit_task_id, machine_id FROM machine_audit_task'))
                    machine_audit_task = [{'audit_task_id': row[0], 'machine_id': row[1]} for row in result.fetchall()]
                except Exception as e:
                    app.logger.error(f"Error fetching machine_audit_task associations: {e}")
                    machine_audit_task = []
            
            # Optionally add audit tasks, completions, etc.
            data = {
                'users': users,
                'roles': roles,
                'sites': sites,
                'machines': machines,
                'parts': parts,
                'maintenance_records': maintenance_records,
                'audit_tasks': audit_tasks,
                'audit_task_completions': audit_task_completions,
                'machine_audit_task': machine_audit_task,
            }
            
            # Add sync metadata for debugging
            sync_metadata = {
                'sync_type': 'incremental' if is_incremental else 'full',
                'since_timestamp': since_timestamp if is_incremental else None,
                'server_timestamp': datetime.now().isoformat(),
                'record_counts': {
                    'users': len(users),
                    'roles': len(roles),
                    'sites': len(sites),
                    'machines': len(machines),
                    'parts': len(parts),
                    'maintenance_records': len(maintenance_records),
                    'audit_tasks': len(audit_tasks),
                    'audit_task_completions': len(audit_task_completions),
                    'machine_audit_task': len(machine_audit_task),
                }
            }
            data['_sync_metadata'] = sync_metadata
            
            # Log the sync request for debugging
            total_records = sum(sync_metadata['record_counts'].values())
            print(f"[SYNC] {sync_metadata['sync_type'].title()} sync served: {total_records} records total")
            if is_incremental:
                print(f"[SYNC] Incremental sync since {since_timestamp}: {sync_metadata['record_counts']}")
            
            return jsonify(data)
        except Exception as e:
            app.logger.error(f"Error in sync_data: {e}")
            return jsonify({'error': str(e)}), 500
    elif request.method == 'POST':
        # Accept pushed data from offline client and merge into DB
        try:
            # Import datetime at function scope for availability throughout POST section
            from datetime import datetime
            
            data = request.get_json(force=True)
            # --- Users ---
            for u in data.get('users', []):
                # Sanitize datetime fields before processing
                u = sanitize_sync_record(u, ['last_login', 'created_at', 'updated_at', 'reset_token_expiration', 'remember_token_expiration'])
                
                user = User.query.get(u['id'])
                if user:
                    user.username = u['username']
                    user.email = u['email']
                    user.full_name = u.get('full_name')  # Add full_name sync
                    user.role_id = u['role_id']
                    # user.is_admin = u.get('is_admin', False)  # Removed: is_admin is a read-only property
                    user.active = u.get('active', True)
                else:
                    user = User(
                        id=u['id'], full_name=u.get('full_name'),  # Add full_name sync
                        role_id=u['role_id'], active=u.get('active', True)  # Removed: is_admin is a read-only property
                    )
                    user.username = u['username']
                    user.email = u['email']
                    db.session.add(user)
            
            # --- Roles ---
            for r in data.get('roles', []):
                # Sanitize datetime fields before processing
                r = sanitize_sync_record(r, ['created_at', 'updated_at'])
                
                role = Role.query.get(r['id'])
                if role:
                    role.name = r['name']
                    role.permissions = r['permissions']
                else:
                    role = Role(id=r['id'], name=r['name'], permissions=r['permissions'])
                    db.session.add(role)
            
            # --- Sites ---
            for s in data.get('sites', []):
                # Sanitize datetime fields before processing
                s = sanitize_sync_record(s, ['created_at', 'updated_at'])
                
                site = Site.query.get(s['id'])
                if site:
                    site.name = s['name']
                    site.location = s.get('location', '')
                else:
                    site = Site(id=s['id'], name=s['name'], location=s.get('location', ''))
                    db.session.add(site)
            
            # --- Machines ---
            for m in data.get('machines', []):
                # Sanitize datetime fields before processing
                m = sanitize_sync_record(m, ['created_at', 'updated_at', 'decommissioned_date'])
                
                machine = Machine.query.get(m['id'])
                if machine:
                    machine.name = m['name']
                    machine.model = m['model']
                    machine.serial_number = m['serial_number']
                    machine.machine_number = m['machine_number']
                    machine.site_id = m['site_id']
                    machine.decommissioned = m.get('decommissioned', False)
                    machine.decommissioned_date = m.get('decommissioned_date')
                    machine.decommissioned_by = m.get('decommissioned_by')
                    machine.decommissioned_reason = m.get('decommissioned_reason')
                else:
                    machine = Machine(
                        id=m['id'], name=m['name'], model=m['model'], serial_number=m['serial_number'],
                        machine_number=m['machine_number'], site_id=m['site_id']
                    )
                    db.session.add(machine)
            
            # --- Audit Tasks ---
            for at in data.get('audit_tasks', []):
                # Sanitize datetime fields before processing
                at = sanitize_sync_record(at, ['created_at', 'updated_at'])
                
                audit_task = AuditTask.query.get(at['id'])
                if audit_task:
                    audit_task.name = at['name']
                    audit_task.description = at['description']
                    audit_task.site_id = at['site_id']
                    audit_task.created_by = at['created_by']
                    audit_task.interval = at['interval']
                    audit_task.custom_interval_days = at.get('custom_interval_days')
                    audit_task.color = at.get('color')
                else:
                    audit_task = AuditTask(
                        id=at['id'], name=at['name'], description=at['description'], site_id=at['site_id'],
                        created_by=at['created_by'], interval=at['interval'], 
                        custom_interval_days=at.get('custom_interval_days'), color=at.get('color')
                    )
                    db.session.add(audit_task)
            
            # --- Parts ---
            for p in data.get('parts', []):
                # Sanitize datetime fields before processing
                p = sanitize_sync_record(p, ['last_maintenance', 'next_maintenance', 'created_at', 'updated_at'])
                
                part = Part.query.get(p['id'])
                if part:
                    part.name = p['name']
                    part.description = p['description']
                    part.machine_id = p['machine_id']
                    part.maintenance_frequency = p['maintenance_frequency']
                    part.maintenance_unit = p['maintenance_unit']
                    part.last_maintenance = p.get('last_maintenance')
                    part.next_maintenance = p.get('next_maintenance')
                else:
                    part = Part(
                        id=p['id'], name=p['name'], description=p['description'], machine_id=p['machine_id'],
                        maintenance_frequency=p['maintenance_frequency'], maintenance_unit=p['maintenance_unit'],
                        last_maintenance=p.get('last_maintenance'), next_maintenance=p.get('next_maintenance')
                    )
                    db.session.add(part)
            
            # --- Maintenance Records ---
            for r in data.get('maintenance_records', []):
                # Sanitize datetime fields before processing
                r = sanitize_sync_record(r, ['date', 'created_at', 'updated_at'])
                
                # Use merge for upsert behavior to avoid ID conflicts
                record = MaintenanceRecord(
                    id=r['id'], machine_id=r['machine_id'], part_id=r['part_id'], user_id=r['user_id'],
                    maintenance_type=r['maintenance_type'], description=r['description'], date=r.get('date'),
                    performed_by=r['performed_by'], status=r['status'], notes=r['notes']
                )
                db.session.merge(record)
            
            # --- Audit Task Completions ---
            for atc in data.get('audit_task_completions', []):
                # Sanitize datetime fields before processing
                atc = sanitize_sync_record(atc, ['date', 'completed_at', 'created_at', 'updated_at'])
                
                # Use merge for upsert behavior to avoid ID conflicts
                completion = AuditTaskCompletion(
                    id=atc['id'],
                    audit_task_id=atc['audit_task_id'],
                    machine_id=atc['machine_id'],
                    completed_by=atc.get('user_id'),  # Use completed_by instead of user_id
                    date=atc.get('date'),
                    completed=atc.get('completed', False),
                    completed_at=atc.get('completed_at')
                )
                merged_completion = db.session.merge(completion)
                db.session.flush()  # Ensure ID is available
                
                # Add to sync queue for tracking (without immediate sync to avoid loop)
                add_to_sync_queue_enhanced('audit_task_completions', merged_completion.id, 'update', {
                    'id': merged_completion.id,
                    'audit_task_id': merged_completion.audit_task_id,
                    'machine_id': merged_completion.machine_id,
                    'date': str(merged_completion.date) if merged_completion.date else None,
                    'completed': merged_completion.completed,
                    'completed_by': merged_completion.completed_by,
                    'completed_at': merged_completion.completed_at.isoformat() if merged_completion.completed_at else None
                }, immediate_sync=False, force_add=True)
            
            # --- Machine Audit Task Associations ---
            for mat in data.get('machine_audit_task', []):
                # No datetime fields to sanitize for this association table
                # Use direct insert/replace for association table
                db.session.execute(
                    text("INSERT OR REPLACE INTO machine_audit_task (machine_id, audit_task_id) VALUES (:machine_id, :audit_task_id)"),
                    {'machine_id': mat['machine_id'], 'audit_task_id': mat['audit_task_id']}
                )
            
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Data merged successfully'}), 200
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error in sync_data POST: {e}")
            return jsonify({'error': str(e)}), 500

@app.route('/health-check')
def health_check():
    """Basic healthcheck endpoint."""
    try:
        # Update to use connection-based execute pattern
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        app.logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/memory-status')
def memory_status():
    """Memory and connection monitoring endpoint."""
    try:
        import psutil
        import gc
        
        # Get process memory info
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        # Get Python garbage collection stats
        gc_stats = gc.get_stats()
        gc_count = gc.get_count()
        
        status = {
            'memory': {
                'rss_mb': round(memory_info.rss / 1024 / 1024, 2),
                'vms_mb': round(memory_info.vms / 1024 / 1024, 2),
                'percent': round(memory_percent, 2)
            },
            'socketio': {
                'active_connections': len(active_connections),
                'connection_ids': list(active_connections)
            },
            'gc': {
                'stats': gc_stats,
                'count': gc_count
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(status), 200
    except ImportError:
        # Fallback if psutil is not available
        return jsonify({
            'socketio': {
                'active_connections': len(active_connections),
                'connection_ids': list(active_connections)
            },
            'timestamp': datetime.utcnow().isoformat(),
            'note': 'Install psutil for detailed memory monitoring'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def page_not_found(e):
    try:
        return render_template('errors/404.html'), 404
    except:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Page Not Found - AMRS Maintenance</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="row justify-content-center">
                    <div class="col-md-6 text-center">
                        <h1 class="display-1 text-primary">404</h1>
                        <h2>Page Not Found</h2>
                        <p class="lead">The page you're looking for doesn't exist.</p>
                        <a href="/" class="btn btn-primary">Go Home</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        ''', 404

@app.errorhandler(500)
def server_error(e):
    try:
        return render_template('errors/500.html'), 500
    except:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Server Error - AMRS Maintenance</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="row justify-content-center">
                    <div class="col-md-6 text-center">
                        <h1 class="display-1 text-danger">500</h1>
                        <h2>Server Error</h2>
                        <p class="lead">Something went wrong on our end.</p>
                        <a href="/" class="btn btn-primary">Go Home</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        ''', 500

@app.errorhandler(400)
def bad_request(e):
    app.logger.warning(f"400 Bad Request: {request.path} - {e}")
    try:
        return render_template('errors/400.html'), 400
    except:
        return '<h1>Bad Request</h1><p>The request could not be understood by the server.</p>', 400

@app.errorhandler(401)
def unauthorized(e):
    app.logger.warning(f"401 Unauthorized: {request.path} - {e}")
    try:
        return render_template('errors/401.html'), 401
    except:
        return '<h1>Unauthorized</h1><p>Login required.</p>', 401

@app.errorhandler(403)
def forbidden(e):
    app.logger.warning(f"403 Forbidden: {request.path} - {e}")
    try:
        return render_template('errors/403.html'), 403
    except:
        return '<h1>Forbidden</h1><p>You do not have permission to access this resource.</p>', 403

@app.route('/admin/<section>')
@login_required
def admin_section(section):
    if not is_admin_user(current_user):
        flash('You do not have permission to access the admin panel.', 'danger')
        return redirect(url_for('dashboard'))
    if section == 'users':
        return render_template('admin/users.html',users=User.query.all())
    elif section == 'roles':
        return render_template('admin/roles.html', roles=Role.query.all())
    # Handle other sections...

@app.route('/sites', methods=['GET', 'POST'])
@login_required
def manage_sites():
    """Handle site management page and site creation"""
    # Filter sites based on user permissions
    if user_can_see_all_sites(current_user):
        sites = Site.query.all()
    else:
        sites = current_user.sites
    
    # Handle form submission for adding a new site
    if request.method == 'POST':
        # Only admins can create sites
        if not is_admin_user(current_user):
            from security_event_logger import log_security_event
            log_security_event(
                event_type="privilege_escalation_attempt",
                details=f"Non-admin user {getattr(current_user, 'username', None)} attempted to create a site.",
                is_critical=True
            )
            flash('You do not have permission to create sites.', 'danger')
            return redirect(url_for('manage_sites'))
            
        try:
            name = request.form['name']
            location = request.form.get('location', '')
            contact_email = request.form.get('contact_email', '')
            notification_threshold = request.form.get('notification_threshold', 30)
            enable_notifications = 'enable_notifications' in request.form
            
            # Create new site
            new_site = Site(
                name=name,
                location=location,
                contact_email=contact_email,
                notification_threshold=notification_threshold,
                enable_notifications=enable_notifications
            )
            
            # Add site to database
            db.session.add(new_site)
            db.session.commit()
            
            # Handle user assignments if admin
            if current_user.is_admin:
                user_ids = request.form.getlist('user_ids')
                if user_ids:
                    for user_id in user_ids:
                        user = User.query.get(int(user_id))
                        if user:
                            new_site.users.append(user)
                    db.session.commit()
            
            flash(f'Site "{name}" has been added successfully.', 'success')
            return redirect(url_for('manage_sites'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding site: {str(e)}', 'danger')

    # For GET request or if POST processing fails
    users = User.query.all() if current_user.is_admin else None
    
    # Define permissions for UI controls
    can_create = current_user.is_admin or (hasattr(current_user, 'role') and current_user.role and 'sites.create' in getattr(current_user.role, 'permissions', ''))
    can_edit = current_user.is_admin or (hasattr(current_user, 'role') and current_user.role and 'sites.edit' in getattr(current_user.role, 'permissions', '')) 
    can_delete = current_user.is_admin or (hasattr(current_user, 'role') and current_user.role and 'sites.delete' in getattr(current_user.role, 'permissions', ''))
    
    return render_template('sites.html', 
                          sites=sites,
                          users=users,
                          is_admin=current_user.is_admin,
                          now=datetime.now(),
                          can_create=can_create,
                          can_edit=can_edit,
                          can_delete=can_delete)

@app.route('/site/edit/<int:site_id>', methods=['GET', 'POST'])
@login_required
def edit_site(site_id):
    """Edit an existing site"""
    site = db.session.get(Site, site_id)
    if not site:
        abort(404)
    users = current_user.sites if not current_user.is_admin else Site.query.all()
    
    if request.method == 'POST':
        try:
            site.name = request.form['name']
            site.location = request.form.get('location', '')
            site.contact_email = request.form.get('contact_email', '')
            site.notification_threshold = request.form.get('notification_threshold', 30)
            site.enable_notifications = 'enable_notifications' in request.form
            
            # Handle user assignments if admin
            if current_user.is_admin:
                # First remove all user associations
                for user in site.users:
                    site.users.remove(user)
                
                # Then add selected users
                user_ids = request.form.getlist('user_ids')
                for user_id in user_ids:
                    user = User.query.get(int(user_id))
                    if user:
                        site.users.append(user)
            
            db.session.commit()
            # Log to sync queue
            add_to_sync_queue_enhanced('sites', site.id, 'update', {
                'id': site.id,
                'name': site.name,
                'location': site.location,
                'contact_email': site.contact_email,
                'notification_threshold': site.notification_threshold,
                'enable_notifications': site.enable_notifications
            })
            # Log all user assignments for this site
            for user in site.users:
                add_to_sync_queue_enhanced('site_users', f'{site.id}_{user.id}', 'update', {
                    'site_id': site.id,
                    'user_id': user.id
                })
            flash(f'Site "{site.name}" has been updated successfully.', 'success')
            return redirect(url_for('manage_sites'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating site: {e}")
            flash(f'Error updating site: {str(e)}', 'danger')
    
    # For GET requests, render the edit form
    return render_template('edit_site.html', 
                          site=site,
                          users=users,
                          is_admin=current_user.is_admin,
                          assigned_users=[user.id for user in site.users])

@app.route('/machines', methods=['GET', 'POST'])
@login_required
def manage_machines():
    """Handle machine management page and machine creation"""
    try:
        site_id = request.args.get('site_id', type=int)
        
        # Get accessible sites based on user permissions
        if user_can_see_all_sites(current_user):
            sites = Site.query.all()
            # Initialize site_ids for all sites
            site_ids = [site.id for site in sites]
            accessible_machines = Machine.query.all()
        else:
            sites = current_user.sites
            site_ids = [site.id for site in sites]
            accessible_machines = Machine.query.filter(
                Machine.site_id.in_(site_ids),
                Machine.decommissioned == False
            ).all()
            
        machine_ids = [machine.id for machine in accessible_machines]
        
        # Get filter parameters
        show_decommissioned = request.args.get('show_decommissioned', 'false').lower() == 'true'
        
        # Filter machines by site if site_id is provided
        if site_id:
            # Verify user can access this site
            if not user_can_see_all_sites(current_user) and site_id not in site_ids:
                from security_event_logger import log_security_event
                log_security_event(
                    event_type="suspicious_activity",
                    details=f"User {getattr(current_user, 'username', None)} attempted to access unauthorized site {site_id} in machines management.",
                    is_critical=True
                )
                flash('You do not have access to this site.', 'danger')
                return redirect(url_for('manage_machines'))
                
            # Filter machines by selected site with eager loading
            machines_query = Machine.query.options(
                db.joinedload(Machine.site),
                db.joinedload(Machine.parts)
            ).filter_by(site_id=site_id)
            title = f"Machines for {Site.query.get_or_404(site_id).name}"
        else:
            # Show machines from all sites user has access to with eager loading
            machines_query = Machine.query.options(
                db.joinedload(Machine.site),
                db.joinedload(Machine.parts)
            ).filter(Machine.site_id.in_(site_ids)) if site_ids else Machine.query.filter(False)
            title = "Machines"
        
        # Apply decommissioned filter
        if not show_decommissioned:
            machines_query = machines_query.filter(Machine.decommissioned == False)
            
        machines = machines_query.all()
        
        # Count decommissioned machines for the toggle
        if site_id:
            decommissioned_count = Machine.query.filter_by(site_id=site_id, decommissioned=True).count()
        else:
            decommissioned_count = Machine.query.filter(
                Machine.site_id.in_(site_ids), 
                Machine.decommissioned == True
            ).count() if site_ids else 0
        
        # Pre-generate URLs for admin navigation - provide ALL possible links needed by template
        safe_urls = {
            'add_machine': '/machines',
            'back_to_sites': '/sites',
            'dashboard': '/dashboard',
            'admin': '/admin',
            'machine_history': '/maintenance'  # Add a default history URL
        }
        
        # Generate URLs for each machine's actions
        for machine in machines:
            machine.delete_url = f'/machines/delete/{machine.id}'
            machine.edit_url = f'/machine/edit/{machine.id}'
            machine.parts_url = f'/parts?machine_id={machine.id}'
            # Add history URL too which is likely referenced in the template
            machine.history_url = f'/maintenance?machine_id={machine.id}'
        
        # Handle form submission for adding a new machine
        if request.method == 'POST':
            try:
                name = request.form['name']
                model = request.form.get('model', '')
                machine_number = request.form.get('machine_number', '')
                serial_number = request.form.get('serial_number', '')
                site_id = request.form['site_id']
                
                # Verify user has access to the selected site
                if not user_can_see_all_sites(current_user) and int(site_id) not in site_ids:
                    flash('You do not have permission to add machines to this site.', 'danger')
                    return redirect(url_for('manage_machines'))
                
                # Create new machine with minimal required fields only
                new_machine = Machine(
                    name=name,
                    model=model,
                    serial_number=serial_number,
                    machine_number=str(machine_number).strip(),
                    site_id=site_id
                )
                
                # Add machine to database
                db.session.add(new_machine)
                db.session.commit()
                
                flash(f'Machine "{name}" has been added successfully.', 'success')
                return redirect(url_for('manage_machines', site_id=site_id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding machine: {str(e)}', 'danger')
        
        return render_template('admin/machines.html', 
                              machines=machines,
                              sites=sites,
                              site_id=site_id,
                              title=title,
                              safe_urls=safe_urls,
                              show_decommissioned=show_decommissioned,
                              decommissioned_count=decommissioned_count,
                              now=datetime.now())
    except Exception as e:
        app.logger.error(f"Error in manage_machines route: {e}")
        flash('An error occurred while loading the machines page.', 'danger')
        return redirect('/dashboard')

@app.route('/machine/edit/<int:machine_id>', methods=['GET', 'POST'])
@login_required
def edit_machine(machine_id):
    """Edit an existing machine"""
    machine = db.session.get(Machine, machine_id)
    if not machine:
        abort(404)
    sites = current_user.sites if not current_user.is_admin else Site.query.all()
    
    if request.method == 'POST':
        try:
            machine.name = request.form['name']
            machine.model = request.form.get('model', '')
            machine.machine_number = request.form.get('machine_number', '')
            machine.serial_number = request.form.get('serial_number', '')
            
            # Convert site_id to integer
            site_id = int(request.form['site_id'])
            machine.site_id = site_id
            
            # Handle decommissioned status if user has permission
            if (current_user.is_admin or 
                (hasattr(current_user, 'role') and current_user.role and 
                 'machines.decommission' in getattr(current_user.role, 'permissions', ''))):
                
                was_decommissioned = machine.decommissioned
                is_being_decommissioned = request.form.get('decommissioned') == 'on'
                
                if is_being_decommissioned and not was_decommissioned:
                    # Machine is being decommissioned
                    reason = request.form.get('decommissioned_reason', '').strip()
                    machine.decommission(current_user, reason)
                    app.logger.info(f"Machine '{machine.name}' decommissioned by {current_user.username}: {reason}")
                    flash(f'Machine "{machine.name}" has been marked as decommissioned.', 'warning')
                    
                elif not is_being_decommissioned and was_decommissioned:
                    # Machine is being recommissioned
                    machine.recommission()
                    app.logger.info(f"Machine '{machine.name}' recommissioned by {current_user.username}")
                    flash(f'Machine "{machine.name}" has been recommissioned and is now active.', 'success')
                    
                elif is_being_decommissioned and was_decommissioned:
                    # Update decommissioned reason if provided
                    new_reason = request.form.get('decommissioned_reason', '').strip()
                    if new_reason != machine.decommissioned_reason:
                        machine.decommissioned_reason = new_reason
                        app.logger.info(f"Updated decommission reason for '{machine.name}': {new_reason}")
            
            db.session.commit()
            # Log to sync queue
            add_to_sync_queue_enhanced('machines', machine.id, 'update', {
                'id': machine.id,
                'name': machine.name,
                'model': machine.model,
                'machine_number': machine.machine_number,
                'serial_number': machine.serial_number,
                'site_id': machine.site_id,
                'decommissioned': getattr(machine, 'decommissioned', False),
                'decommissioned_reason': getattr(machine, 'decommissioned_reason', ''),
            })
            flash(f'Machine "{machine.name}" has been updated successfully.', 'success')
            return redirect(url_for('manage_machines'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating machine: {e}")
            flash(f'Error updating machine: {str(e)}', 'danger')
    
    # For GET requests, render the edit form
    return render_template('edit_machine.html', 
                          machine=machine,
                          sites=sites)

@app.route('/parts', methods=['GET', 'POST'])
@login_required
def manage_parts():
    """Handle parts management page and part creation"""
    try:
        machine_id = request.args.get('machine_id', type=int)
        
        # Get accessible sites based on user permissions
        if user_can_see_all_sites(current_user):
            sites = Site.query.all()
            accessible_machines = Machine.query.filter(Machine.decommissioned == False).all()
        else:
            sites = current_user.sites
            site_ids = [site.id for site in sites]
            accessible_machines = Machine.query.filter(
                Machine.site_id.in_(site_ids),
                Machine.decommissioned == False
            ).all()
            
        machine_ids = [machine.id for machine in accessible_machines]
        
        # Filter parts by machine if machine_id is provided
        if machine_id:
            # Verify user can access this machine
            machine = Machine.query.get(machine_id)
            if not machine or (not user_can_see_all_sites(current_user) and machine.site_id not in site_ids):
                from security_event_logger import log_security_event
                log_security_event(
                    event_type="suspicious_activity",
                    details=f"User {getattr(current_user, 'username', None)} attempted to access unauthorized machine {machine_id} in parts management.",
                    is_critical=True
                )
                flash('You do not have access to this machine.', 'danger')
                return redirect(url_for('manage_parts'))
            
            # Filter parts by selected machine
            parts = Part.query.filter_by(machine_id=machine_id).all()
            title = f"Parts for {machine.name}"
        else:
            # Show parts from all machines user has access to
            parts = Part.query.filter(Part.machine_id.in_(machine_ids)).all() if machine_ids else []
            title = "Parts"
        
        # Get machines user has access to for the form
        machines = accessible_machines
        
        # Pre-generate URLs for admin navigation - provide ALL possible links needed by template
        safe_urls = {
            'add_part': '/parts',
            'back_to_machines': '/machines',
            'dashboard': '/dashboard',
            'admin': '/admin'
        }
        
        # Handle form submission for adding a new part
        if request.method == 'POST':
            try:
                name = request.form['name']
                description = request.form.get('description', '')
                part_number = request.form.get('part_number', '')  
                machine_id = request.form['machine_id']
                quantity = request.form.get('quantity', 0)  
                notes = request.form.get('notes', '')
                
                # Check if user has access to the machine
                machine = Machine.query.get(machine_id)
                if not machine:
                    flash('Invalid machine selected.', 'danger')
                    return redirect(url_for('manage_parts'))
                    
                if not user_can_see_all_sites(current_user) and int(machine.site_id) not in [site.id for site in current_user.sites]:
                    flash('You do not have permission to add parts to this machine.', 'danger')
                    return redirect(url_for('manage_parts'))
                
                # Get maintenance frequency and unit from form
                maintenance_frequency = request.form.get('maintenance_frequency', 30)
                maintenance_unit = request.form.get('maintenance_unit', 'day')
                
                # Create new part with all fields
                new_part = Part(
                    name=name,
                    description=description,
                    machine_id=machine_id if machine_id else None,
                    maintenance_frequency=maintenance_frequency,
                    maintenance_unit=maintenance_unit
                )
                
                # Add part to database
                db.session.add(new_part)
                db.session.commit()
                flash(f'Part "{name}" has been added successfully.', 'success')
                return redirect('/parts')  # Using direct URL to avoid potential errors
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error adding part: {e}")
                flash(f'Error adding part: {str(e)}', 'danger')
        
        return render_template('admin/parts.html', 
                            parts=parts,
                            machines=machines,
                            machine_id=machine_id,
                            title=title,
                            safe_urls=safe_urls,
                            now=datetime.now())
    except Exception as e:
        app.logger.error(f"Error in manage_parts route: {e}")
        flash('An error occurred while loading the parts page.', 'danger')
        return redirect('/dashboard')


@app.route('/manage/users')
@login_required
def manage_users():
    """Alternative route for user management - redirects to admin users page."""
    # If this is a POST request, forward it to the admin_users function
    if request.method == 'POST':
        return admin_users()
        
    # For GET requests, continue with normal redirect logic
    if not is_admin_user(current_user):
        flash('You do not have permission to access this page.', 'danger')
        return redirect('/dashboard')
    return redirect('/admin/users')

@app.route('/import_excel', methods=['GET', 'POST'])
@login_required
def import_excel_route():
    """Handle Excel file imports to add data to the system."""
    if not is_admin_user(current_user):
        flash('You do not have permission to import data.', 'danger')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('No file part', 'danger')
            flash('Import complete', 'info')
            return redirect(request.referrer or url_for('admin_excel_import'))
            
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file', 'danger')
            flash('Import complete', 'info')
            return redirect(request.referrer or url_for('admin_excel_import'))
            
        if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ['xlsx', 'xls']:
            try:
                # Save the uploaded file temporarily
                import tempfile
                from excel_importer import import_excel
                
                # Create a temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
                file.save(temp_file.name)
                temp_file.close()
                
                # Import data from the Excel file
                try:
                    stats = import_excel(temp_file.name)
                    # Remove the temporary file
                    import os
                    os.unlink(temp_file.name)
                    # Display import results
                    success_message = f"Data imported successfully! Added {stats['sites_added']} sites, {stats['machines_added']} machines, and {stats['parts_added']} parts."
                    flash(success_message, 'success')
                except Exception as e:
                    flash(f'Error importing data: {str(e)}', 'danger')
                flash('Import complete', 'info')
                return redirect(url_for('admin_excel_import'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error importing data: {str(e)}', 'danger')
                flash('Import complete', 'info')
                return redirect(url_for('admin_excel_import'))
        else:
            flash('Invalid file type. Please upload an Excel file (.xlsx, .xls)', 'danger')
            flash('Import complete', 'info')
            return redirect(url_for('admin_excel_import'))
            
    # GET request - redirect to the Excel import page
    return render_template('admin/excel_import.html') if os.path.exists(os.path.join('templates', 'admin', 'excel_import.html')) else "<h1>Excel Import Page</h1>"

@app.route('/part/edit/<int:part_id>', methods=['GET', 'POST'])
@login_required
def edit_part(part_id):
    part = db.session.get(Part, part_id)
    if not part:
        abort(404)
    machines = Machine.query.all()
    if request.method == 'POST':
        part.name = request.form.get('name', part.name)
        part.description = request.form.get('description', part.description)
        part.machine_id = request.form.get('machine_id', part.machine_id)
        # Update maintenance_frequency and maintenance_unit from form
        part.maintenance_frequency = request.form.get('maintenance_frequency', part.maintenance_frequency)
        part.maintenance_unit = request.form.get('maintenance_unit', part.maintenance_unit)
        db.session.commit()
        # Log to sync queue
        add_to_sync_queue_enhanced('parts', part.id, 'update', {
            'id': part.id,
            'name': part.name,
            'description': part.description,
            'machine_id': part.machine_id,
            'maintenance_frequency': part.maintenance_frequency,
            'maintenance_unit': part.maintenance_unit
        })
        flash('Part updated successfully.', 'success')
        return redirect(url_for('manage_parts'))
    
    # Return template for GET request
    return render_template('edit_part.html', part=part, machines=machines)

@app.route('/role/edit/<int:role_id>', methods=['GET', 'POST'])
@login_required
def edit_role(role_id):
    """Edit an existing role - admin only."""
    if not is_admin_user(current_user):
        flash('You do not have permission to edit roles.', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        # Get role by ID
        role = db.session.get(Role, role_id)
        if not role:
            abort(404)
        
        # Process form submission
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description', '')
            permissions = request.form.getlist('permissions')
            
            # Validate required fields
            if not name:
                flash('Role name is required.', 'danger')
                return redirect(url_for('edit_role', role_id=role_id))
            
            # Check if role name already exists for another role
            existing_role = Role.query.filter(Role.name == name, Role.id != role_id).first()
            if existing_role:
                flash(f'A role with the name "{name}" already exists.', 'danger')
                return redirect(url_for('edit_role', role_id=role_id))
            
            # Update role details
            role.name = name
            role.description = description
            role.permissions = ','.join(permissions) if permissions else ''
            
            db.session.commit()
            flash(f'Role "{name}" has been updated successfully.', 'success')
            return redirect(url_for('admin_roles'))
        else:
            # For GET requests, render the edit form with the all_permissions dictionary
            all_permissions = get_all_permissions()
            role_permissions = role.permissions.split(',') if role.permissions else []
            return render_template('edit_role.html', role=role, all_permissions=all_permissions, role_permissions=role_permissions)
    except Exception as e:
        app.logger.error(f"Error editing role: {e}")
        flash(f'Error editing role: {str(e)}', 'danger')
        return redirect(url_for('admin_roles'))

@app.route('/api/maintenance/records', methods=['GET'])
@login_required
def maintenance_records_page():
    # Get all sites user can access
    if user_can_see_all_sites(current_user):
        sites = Site.query.all()
    else:
        sites = current_user.sites
        
    site_id = request.args.get('site_id', type=int)
    machine_id = request.args.get('machine_id', type=int)
    part_id = request.args.get('part_id', type=int)

    # Get site IDs the user has access to
    site_ids = [site.id for site in sites]
    
    machines = []
    parts = []
    records = []
    part_ids = []  # Initialize part_ids here

    if site_id:
        # Verify user can access this site
        if not user_can_see_all_sites(current_user) and site_id not in site_ids:
            flash('You do not have access to this site.', 'danger')
            return redirect(url_for('maintenance_records_page'))
            
        # Filter machines by selected site
        machines_query = Machine.query.filter_by(site_id=site_id)
    else:
        # Get machines from all available sites
        site_ids = [s.id for s in sites]
        machines_query = Machine.query.filter(Machine.site_id.in_(site_ids))
    
    # Apply machine filter if provided
    if machine_id:
        machines_query = machines_query.filter_by(id=machine_id)
    
    # Get the machines
    machines = machines_query.order_by(Machine.name).all()
    
    # Get machine IDs
    machine_ids = [m.id for m in machines]
    
    if part_id:
        # Verify user can access this part
        part = Part.query.get(part_id)
        if not part or (not user_can_see_all_sites(current_user) and part.machine.site_id not in site_ids):
            flash('You do not have access to this part.', 'danger')
            return redirect(url_for('maintenance_records_page'))
            
        # Filter records by selected part
        records = MaintenanceRecord.query.filter_by(part_id=part_id).order_by(MaintenanceRecord.date.desc()).all()
    elif machine_id:
        # If a machine is selected but no part, show records for all parts of that machine
        parts_for_machine = Part.query.filter_by(machine_id=machine_id).all()
        part_ids_for_machine = [part.id for part in parts_for_machine]
        records = MaintenanceRecord.query.filter(MaintenanceRecord.part_id.in_(part_ids_for_machine)).order_by(MaintenanceRecord.date.desc()).all()
    elif site_id:
        # If a site is selected but no machine/part, show records for all parts of all machines at that site
        machines_for_site = Machine.query.filter_by(site_id=site_id).all()
        machine_ids_for_site = [machine.id for machine in machines_for_site]
        parts_for_site = Part.query.filter(Part.machine_id.in_(machine_ids_for_site)).all()
        part_ids_for_site = [part.id for part in parts_for_site]
        records = MaintenanceRecord.query.filter(MaintenanceRecord.part_id.in_(part_ids_for_site)).order_by(MaintenanceRecord.date.desc()).all()
    else:
        # No filters selected - show all records for parts the user has access to
        if machine_ids:
            parts = Part.query.filter(Part.machine_id.in_(machine_ids)).all()
            part_ids = [part.id for part in parts]
        records = MaintenanceRecord.query.filter(MaintenanceRecord.part_id.in_(part_ids)).order_by(MaintenanceRecord.date.desc()).all() if part_ids else []

    return render_template(
        'maintenance_records.html',
        sites=sites,
        machines=machines,
        parts=parts,
        records=records,
        selected_site=site_id,
        selected_machine=machine_id,
        selected_part=part_id
    )

@app.route('/maintenance-record/<int:record_id>')
@login_required
def maintenance_record_detail(record_id):
    """View details of a specific maintenance record"""
    try:
        # Get the maintenance record
        record = MaintenanceRecord.query.get_or_404(record_id)
        
        # Check if user has access to this record's site
        if not user_can_see_all_sites(current_user):
            if record.machine and record.machine.site not in current_user.sites:
                flash('You do not have access to this maintenance record.', 'danger')
                return redirect(url_for('maintenance_records_page'))
        
        return render_template('maintenance_record_detail.html', record=record)
        
    except Exception as e:
        app.logger.error(f"Error in maintenance_record_detail: {e}")
        flash('An error occurred while loading the maintenance record.', 'danger')
        return redirect(url_for('maintenance_records_page'))

@app.route('/maintenance-record/print/<int:record_id>')
@login_required
def maintenance_record_print(record_id):
    """Generate a printable view for a maintenance record"""
    try:
        # Get the maintenance record
        record = MaintenanceRecord.query.get_or_404(record_id)
        
        # Check if user has access to this record's site
        if not user_can_see_all_sites(current_user):
            if record.machine and record.machine.site not in current_user.sites:
                flash('You do not have access to this maintenance record.', 'danger')
                return redirect(url_for('maintenance_records_page'))
        
        # Get any company information from site settings
        company_info = {}
        if record.machine and record.machine.site:
            site = record.machine.site
            company_info = {
                'name': site.name or "Maintenance Tracker",
                'address': site.location or "",
                'phone': "",  # Site model doesn't have phone field
                'email': site.contact_email or "",
                'logo_url': url_for('static', filename='img/logo.png')  # Use default logo
            }
        else:
            # Default company info if no site is associated
            company_info = {
                'name': "Maintenance Tracker",
                'address': "",
                'phone': "",
                'email': "",
                'logo_url': url_for('static', filename='img/logo.png')
            }
        
        return render_template(
            'maintenance_record_pdf.html',
            record=record,
            company_info=company_info,
            print_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
    except Exception as e:
        app.logger.error(f"Error in maintenance_record_print: {e}")
        flash('An error occurred while generating the print view.', 'danger')
        return redirect(url_for('maintenance_record_detail', record_id=record_id))

@app.route('/emergency-maintenance-request', methods=['POST'])
@login_required
def emergency_maintenance_request():
    """Handle emergency maintenance request form submission"""
    try:
        # Get form data
        machine_id = request.form.get('machine_id')
        machine_name = request.form.get('machine_name')
        site_name = request.form.get('site_name')
        site_location = request.form.get('site_location', '')
        part_id = request.form.get('part_id')
        contact_name = request.form.get('contact_name')
        contact_email = request.form.get('contact_email')
        contact_phone = request.form.get('contact_phone', '')
        issue_description = request.form.get('issue_description')
        priority = request.form.get('priority', 'Critical')
        
        # Validate required fields
        if not (machine_id and machine_name and contact_name and contact_email and issue_description):
            flash('Missing required fields for emergency request.', 'danger')
            return redirect(url_for('manage_machines'))
        
        # Get additional machine details
        machine = db.session.get(Machine, int(machine_id))
        if not machine:
            flash('Machine not found.', 'danger')
            return redirect(url_for('manage_machines'))
            
        # Get part details if specified
        part_name = None
        if part_id:
            part = db.session.get(Part, int(part_id))
            if part:
                part_name = part.name
        
        # Get emergency contact email from environment
        emergency_email = os.environ.get('EMERGENCY_CONTACT_EMAIL')
        
        # If no emergency email is configured, use a fallback approach
        if not emergency_email:
            app.logger.warning("No EMERGENCY_CONTACT_EMAIL configured. Using admin users as fallback.")
            # Get emails of all admin users as fallback
            admin_role = Role.query.filter_by(name='admin').first()
            if admin_role:
                admin_users = User.query.filter_by(role_id=admin_role.id).all()
                emergency_emails = [user.email for user in admin_users if user.email]
            else:
                # Absolute fallback - use the system default sender
                emergency_emails = [app.config['MAIL_DEFAULT_SENDER']]
        else:
            # Use the configured emergency email
            emergency_emails = [emergency_email]
        
        # Prepare email context
        context = {
            'machine_name': machine_name,
            'machine_model': machine.model,
            'machine_number': machine.machine_number or 'N/A',
            'serial_number': machine.serial_number or 'N/A',
            'site_name': site_name,
            'site_location': site_location,
            'part_name': part_name,
            'contact_name': contact_name,
            'contact_email': contact_email,
            'contact_phone': contact_phone,
            'issue_description': issue_description,
            'priority': priority,
            'now': datetime.now()
        }
        
        # Create subject line based on priority
        if priority == 'Critical':
            subject = f"URGENT: Critical Maintenance Required - {machine_name} at {site_name}"
        elif priority == 'High':
            subject = f"HIGH Priority: Maintenance Required - {machine_name} at {site_name}"
        else:
            subject = f"Maintenance Request - {machine_name} at {site_name}"
        
        # Send email
        try:
            msg = Message(
                subject=subject,
                recipients=emergency_emails,
                html=render_template('email/emergency_request.html', **context),
                sender=app.config['MAIL_DEFAULT_SENDER']
            )
            # Add reply-to header so technicians can reply directly to the requester
            msg.reply_to = contact_email
            
            # Send the email
            mail.send(msg)
            
            # Log the emergency request
            app.logger.info(f"Emergency maintenance request sent for {machine_name} at {site_name} with {priority} priority")
            
            flash('Emergency maintenance request has been sent successfully. A technician will contact you shortly.', 'success')
        except Exception as e:
            app.logger.error(f"Failed to send emergency maintenance email: {str(e)}")
            flash(f'Failed to send emergency request email: {str(e)}', 'danger')
        
        return redirect(url_for('manage_machines'))
        
    except Exception as e:
        app.logger.error(f"Error processing emergency maintenance request: {str(e)}")
        flash(f'Error processing emergency request: {str(e)}', 'danger')
        return redirect(url_for('manage_machines'))

@app.route('/audit-task/delete/<int:audit_task_id>', methods=['POST'])
@login_required
def delete_audit_task(audit_task_id):
    """Delete an audit task."""
    # Check permissions
    if not current_user.is_admin:
        # If not admin, check if user has specific permission
        if not hasattr(current_user, 'role') or not current_user.role or not current_user.role.permissions or 'audits.delete' not in current_user.role.permissions.split(','):
            flash('You do not have permission to delete audit tasks.', 'danger')
            return redirect(url_for('audits_page'))
    
    try:
        # Get the audit task
        audit_task = AuditTask.query.get_or_404(audit_task_id)
        
        # Check if the user has access to this site
        if not current_user.is_admin:
            user_site_ids = [site.id for site in current_user.sites]
            if audit_task.site_id not in user_site_ids:
                flash('You do not have permission to delete audit tasks for this site.', 'danger')
                return redirect(url_for('audits_page'))
        
        task_name = audit_task.name
        
        # Delete all completions first (to avoid foreign key constraint violations)
        # The cascade should handle this but we'll do it explicitly to be safe
        AuditTaskCompletion.query.filter_by(audit_task_id=audit_task_id).delete()
        
        # Delete the audit task
        db.session.delete(audit_task)
        db.session.commit()
        
        flash(f'Audit task "{task_name}" deleted successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting audit task: {e}")
        flash(f'An error occurred while deleting the audit task: {str(e)}', 'danger')
    
    return redirect(url_for('audits_page'))

def get_database_stats():
    """Gather statistics for the admin dashboard - database agnostic version."""
    try:
        # Use SQLAlchemy to query counts directly, which works with both SQLite and PostgreSQL
        stats = {}
        
        # Count users
        try:
            stats['users'] = User.query.count()
        except Exception:
            stats['users'] = 0
            
        # Count roles
        try:
            stats['roles'] = Role.query.count()
        except Exception:
            stats['roles'] = 0
            
        # Count sites
        try:
            stats['sites'] = Site.query.count()
        except Exception:
            stats['sites'] = 0
            
        # Count machines
        try:
            machine_count = Machine.query.count()
            stats['machines'] = machine_count
            stats['active_machines'] = Machine.query.filter_by(decommissioned=False).count()
            stats['decommissioned_machines'] = Machine.query.filter_by(decommissioned=True).count()
        except Exception:
            stats['machines'] = 0
            stats['active_machines'] = 0
            stats['decommissioned_machines'] = 0
            
        # Count parts
        try:
            stats['parts'] = Part.query.count()
        except Exception:
            stats['parts'] = 0
            
        # Count maintenance records
        try:
            stats['maintenance_records'] = MaintenanceRecord.query.count()
        except Exception:
            stats['maintenance_records'] = 0
            
        # Count audit tasks
        try:
            stats['audit_tasks'] = AuditTask.query.count()
        except Exception:
            stats['audit_tasks'] = 0
            
        # Calculate maintenance status (simplified version)
        try:
            from datetime import datetime, timedelta
            now = datetime.now()
            overdue_count = 0
            due_soon_count = 0
            ok_count = 0
            
            parts_with_maintenance = Part.query.filter(Part.next_maintenance.isnot(None)).all()
            for part in parts_with_maintenance:
                if part.next_maintenance:
                    if part.next_maintenance < now:
                        overdue_count += 1
                    elif part.next_maintenance < now + timedelta(days=7):
                        due_soon_count += 1
                    else:
                        ok_count += 1
                        
            stats['maintenance_overdue'] = overdue_count
            stats['maintenance_due_soon'] = due_soon_count
            stats['maintenance_ok'] = ok_count
        except Exception:
            stats['maintenance_overdue'] = 0
            stats['maintenance_due_soon'] = 0
            stats['maintenance_ok'] = 0
            
        return stats
        
    except Exception as e:
        print(f"[STATS] Error gathering database statistics: {e}")
        # Return empty stats if any error occurs
        return {
            'users': 0,
            'roles': 0,
            'sites': 0,
            'machines': 0,
            'active_machines': 0,
            'decommissioned_machines': 0,
            'parts': 0,
            'maintenance_records': 0,
            'audit_tasks': 0,
            'maintenance_overdue': 0,
            'maintenance_due_soon': 0,
            'maintenance_ok': 0
        }

# --- BULK IMPORT ROUTE ---
@app.route('/admin/bulk-import', methods=['GET', 'POST'])
@login_required
def bulk_import():
    """Handle bulk import of machines, parts, and maintenance records via CSV/JSON"""
    # Only allow users with 'manage' permissions (admin or role with 'manage' in permissions)
    if not (current_user.is_admin or (hasattr(current_user, 'role') and current_user.role and 'manage' in getattr(current_user.role, 'permissions', ''))):
        flash('You do not have permission to access bulk import.', 'danger')
        return redirect(url_for('admin'))

    # Get sites for the dropdown
    if current_user.is_admin:
        sites = Site.query.all()
    else:
        sites = current_user.sites

    def parse_frequency_string(frequency_str):
        """Parse a frequency string like '6 Months', '1 Year', '30 Days' into numeric value and unit"""
        if not frequency_str:
            return 30, 'day'  # default
        
        import re
        freq_lower = str(frequency_str).lower().strip()
        
        # Extract numeric value from the frequency string
        numbers = re.findall(r'\d+', freq_lower)
        numeric_value = int(numbers[0]) if numbers else 1
        
        # Convert everything to days for consistency
        if 'year' in freq_lower:
            return numeric_value * 365, 'day'
        elif 'month' in freq_lower:
            return numeric_value * 30, 'day'
        elif 'week' in freq_lower:
            return numeric_value * 7, 'day'
        elif 'day' in freq_lower:
            return numeric_value, 'day'
        else:
            # If no unit specified, assume the number is in days
            return numeric_value, 'day'  # fallback default

   

    def smart_field_mapping(row, entity_type):
        """Intelligently map various field names to standard format"""
        mapped = {}
        
        # Define field mappings for different naming conventions
        field_mappings = {
            'machines': {
                'name': ['name', 'machine', 'machine_name', 'Machine'],
                'model': ['model', 'machine_model', 'Model'],
                'serial_number': ['serial_number', 'serial', 'Serial Number', 'sn'],
                'machine_number': ['machine_number', 'Machine Number', 'number', 'id']
            },
            'parts': {
                'name': ['name', 'part_name', 'Part', 'part'],
                'description': ['description', 'desc', 'Description'],
                'machine_name': ['machine_name', 'machine', 'Machine', 'Machine Name'],
                'maintenance_frequency': ['maintenance_frequency', 'frequency', 'Frequency', 'interval'],
                'maintenance_unit': ['maintenance_unit', 'unit', 'Unit', 'frequency_unit'],
                'frequency_text': ['frequency_text', 'frequency_string', 'interval_text', 'schedule']
            },
            'maintenance': {
                'machine_name': ['machine_name', 'machine', 'Machine', 'Machine Name'],
                'part_name': ['part_name', 'part', 'Part', 'component'],
                'maintenance_type': ['maintenance_type', 'type', 'Type', 'Maintenance Type'],
                'description': ['description', 'desc', 'Description', 'work_done'],
                'date': ['date', 'Date', 'maintenance_date', 'performed_date'],
                'performed_by': ['performed_by', 'technician', 'Technician', 'worker'],
                'status': ['status', 'Status', 'state'],
                'notes': ['notes', 'Notes', 'comments', 'Comments']
            }
        }
        
        # Map fields based on entity type
        if entity_type in field_mappings:
            for standard_field, possible_names in field_mappings[entity_type].items():
                for possible_name in possible_names:
                    if possible_name in row and row[possible_name] is not None:
                        mapped[standard_field] = row[possible_name]
                        break
        
        return mapped

    def extract_parts_data(machine_data, machine_name):
        """Extract parts from nested MaintenanceData.Parts or flat CSV structure"""
        parts = []
        
        # Handle nested JSON structure (existing logic)
        if 'MaintenanceData' in machine_data and 'Parts' in machine_data['MaintenanceData']:
            parts_list = machine_data['MaintenanceData']['Parts']
            
            for part_data in parts_list:
                if not part_data or not part_data.get('Part Name'):
                    continue
                    
                maintenance = part_data.get('Maintenance', {})
                
                # Parse frequency to get numeric value and unit
                frequency_str = maintenance.get('Frequency', '1 Year')
                freq_value, freq_unit = parse_frequency_string(frequency_str)
                
                part = {
                    'name': part_data.get('Part Name', ''),
                    'description': f"{maintenance.get('Maintenance Done', '')} - {maintenance.get('Maintenance Type', '')}".strip(' -'),
                    'machine_name': machine_name,
                    'maintenance_frequency': freq_value,
                    'maintenance_unit': freq_unit,
                    'materials': maintenance.get('Required Materials', ''),
                    'quantity': maintenance.get('Qty.', '')
                }
                
                if part['name']:
                    parts.append(part)
        
        # Handle flat CSV structure
        elif machine_data.get('part_name'):
            # Extract part data from flat CSV row
            part_name = machine_data.get('part_name', '').strip()
            if part_name:
                # Parse frequency from CSV columns
                freq_value = 30  # default
                freq_unit = 'day'  # default
                
                if machine_data.get('maintenance_frequency'):
                    try:
                        freq_value = int(machine_data.get('maintenance_frequency', 30))
                    except (ValueError, TypeError):
                        freq_value = 30
                
                if machine_data.get('maintenance_unit'):
                    freq_unit = machine_data.get('maintenance_unit', 'day').lower()
                    # Convert months to days for consistency
                    if freq_unit in ['month', 'months']:
                        freq_value = freq_value * 30
                        freq_unit = 'day'
                    elif freq_unit in ['year', 'years']:
                        freq_value = freq_value * 365;
                        freq_unit = 'day'
                
                part = {
                    'name': part_name,
                    'description': machine_data.get('description', '').strip(),
                    'machine_name': machine_name,
                    'maintenance_frequency': freq_value,
                    'maintenance_unit': freq_unit,
                    'materials': machine_data.get('materials', ''),
                    'quantity': machine_data.get('quantity', '')
                }
                
                parts.append(part)
        
        return parts

    def find_or_create_machine(machine_data, site_id):
        """Find existing machine or create new one with smart duplicate detection"""
        mapped = smart_field_mapping(machine_data, 'machines')
        
        name = str(mapped.get('name', '')).strip()
        model = str(mapped.get('model', '')).strip()
        serial = str(mapped.get('serial_number', '')).strip()
        
        # If no name found in standard mapping, try machine_name field
        if not name:
            name = str(machine_data.get('machine_name', '')).strip()
        
        if not name:
            return None, "Missing machine name"
        
        # Default model to machine name if not provided
        if not model:
            model = name
        
        # Try to find existing machine using multiple criteria
        existing = None
        
        # First try: exact match on name, model, and serial
        if serial:
            existing = Machine.query.filter_by(
                name=name, 
                model=model, 
                serial_number=serial,
                site_id=site_id
            ).first()
        
        # Second try: match on name and serial (in case model is slightly different)
        if not existing and serial:
            existing = Machine.query.filter_by(
                name=name,
                serial_number=serial,
                site_id=site_id
            ).first()
        
        # If we have a serial number and haven't found a match, this should be a new machine
        # Only check name/model matches if there's no serial number provided
        if not existing and not serial:
            # Third try: match on name and model (only if no serial number)
            if model:
                existing = Machine.query.filter_by(
                    name=name,
                    model=model,
                    site_id=site_id
                ).first()
            
            # Fourth try: match on name only (if it's unique within site and no serial)
            if not existing:
                name_matches = Machine.query.filter_by(name=name, site_id=site_id).all()
                if len(name_matches) == 1:
                    existing = name_matches[0]
        
        if existing:
            # Update existing machine with any new/better data
            updated = False
            if not existing.model and model:
                existing.model = model
                updated = True
            if not existing.serial_number and serial:
                existing.serial_number = serial
                updated = True
            if not existing.machine_number and mapped.get('machine_number'):
                existing.machine_number = str(mapped.get('machine_number', '')).strip()
                updated = True
            
            return existing, "Updated existing machine" if updated else "Found existing machine"
        else:
            # Create new machine
            machine = Machine(
                name=name,
                model=model,
                serial_number=serial,
                machine_number=str(mapped.get('machine_number', '')).strip(),
                site_id=site_id
            )
            return machine, "Created new machine"

    def find_or_create_part(part_data, machine):
        """Find existing part or create new one with smart duplicate detection"""
        part_name = part_data.get('name', '').strip()
        
        if not part_name:
            return None, "Missing part name"
        
        # Try to find existing part for this machine
        existing = Part.query.filter_by(
            name=part_name,
            machine_id=machine.id
        ).first()
        
        if existing:
            # Update existing part with any new/better data
            updated = False
            
            # Update description if empty or new one is more detailed
            new_desc = part_data.get('description', '').strip()
            if new_desc and (not existing.description or len(new_desc) > len(existing.description)):
                existing.description = new_desc
                updated = True
            
            # Update maintenance frequency if new data is provided and different
            new_freq = part_data.get('maintenance_frequency', 0)
            new_unit = part_data.get('maintenance_unit', 'day')
            
            # Check if there's a text-based frequency to parse
            frequency_text = part_data.get('frequency_text', '')
            if frequency_text and not new_freq:
                new_freq, new_unit = parse_frequency_string(frequency_text)
            
            if new_freq and (new_freq != existing.maintenance_frequency or new_unit != existing.maintenance_unit):
                existing.maintenance_frequency = new_freq
                existing.maintenance_unit = new_unit
                updated = True
            
            return existing, "Updated existing part" if updated else "Found existing part"
        else:
            # Parse frequency data for new part
            freq_value = part_data.get('maintenance_frequency', 0)
            freq_unit = part_data.get('maintenance_unit', 'day')
            
            # Check if there's a text-based frequency to parse
            frequency_text = part_data.get('frequency_text', '')
            if frequency_text and not freq_value:
                freq_value, freq_unit = parse_frequency_string(frequency_text)
            
            # Use defaults if still not set
            if not freq_value:
                freq_value = 30
                freq_unit = 'day'
            
            # Create new part
            description = part_data.get('description', '').strip()
            part = Part(
                name=part_name,
                description=description,
                machine_id=machine.id,
                maintenance_frequency=freq_value,
                maintenance_unit=freq_unit
            )
            return part, "Created new part"
    def find_or_create_maintenance(maintenance_data, machine, part):
        """Find existing maintenance record or create new one with smart duplicate detection"""
        from datetime import datetime, timedelta
        
        # Parse the maintenance date
        date_obj = None
        date_str = maintenance_data.get('date', '')
        
        if date_str:
            try:
                # Clean the date string - remove time part and extra whitespace
                date_str = str(date_str).strip().split(' ')[0]
                
                # Try different date formats
                date_formats = [
                    '%Y-%m-%d',      # 2025-01-16
                    '%m/%d/%Y',      # 01/16/2025
                    '%d/%m/%Y',      # 16/01/2025
                    '%Y/%m/%d',      # 2025/01/16
                    '%m-%d-%Y',      # 01-16-2025
                    '%d-%m-%Y'       # 16-01-2025
                ]
                
                for date_format in date_formats:
                    try:
                        date_obj = datetime.strptime(date_str, date_format)
                        break
                    except ValueError:
                        continue
                        
            except Exception as e:
                app.logger.warning(f"Failed to parse date '{date_str}': {e}")
        
        # If we couldn't parse the date, use a reasonable default (30 days ago)
        # This prevents all maintenance from showing as "today"
        if date_obj is None:
            if date_str:
                app.logger.warning(f"Could not parse maintenance date '{date_str}', using 30 days ago as fallback")
            date_obj = datetime.now() - timedelta(days=30)
        
        maintenance_type = maintenance_data.get('maintenance_type', 'Scheduled')
        description = maintenance_data.get('description', '').strip()
        performed_by = maintenance_data.get('performed_by', current_user.username)
        
        # Look for existing maintenance records that might be duplicates
        # Check for records on the same day with similar description
        date_start = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=1)
        
        existing = MaintenanceRecord.query.filter(
            MaintenanceRecord.machine_id == machine.id,
            MaintenanceRecord.part_id == part.id,
            MaintenanceRecord.date >= date_start,
            MaintenanceRecord.date < date_end,
            MaintenanceRecord.maintenance_type == maintenance_type
        ).first()
        
        # If we found a record on the same day with same type, check if it's likely the same
        if existing:
            # If descriptions are very similar or one is empty, consider it a duplicate
            existing_desc = existing.description.strip().lower()
            new_desc = description.lower()
            
            # Check for similarity (either exact match, one contains the other, or both are short)
            is_duplicate = (
                existing_desc == new_desc or
                (len(existing_desc) < 20 and len(new_desc) < 20) or
                (existing_desc and new_desc and (existing_desc in new_desc or new_desc in existing_desc))
            )
            
            if is_duplicate:
                # Update existing record with any new/better data
                updated = False
                
                # Update description if new one is more detailed
                if len(description) > len(existing.description):
                    existing.description = description
                    updated = True
                
                # Update performed_by if it was generic
                if existing.performed_by in ['System Import', 'Unknown'] and performed_by not in ['System Import', 'Unknown']:
                    existing.performed_by = performed_by
                    updated = True
                
                # Update notes if we have additional information
                new_notes = maintenance_data.get('notes', '').strip()
                if new_notes and new_notes not in existing.notes:
                    existing.notes = f"{existing.notes}\n{new_notes}".strip()
                    updated = True
                
                return existing, "Updated existing maintenance record" if updated else "Found existing maintenance record"
        
        # Create new maintenance record
        maintenance = MaintenanceRecord(
            machine_id=machine.id,
            part_id=part.id,
            user_id=current_user.id,
            maintenance_type=maintenance_type,
            description=description,
            date=date_obj,
            performed_by=performed_by,
            status=maintenance_data.get('status', 'completed'),
            notes=maintenance_data.get('notes', '')
        )
        
        # Note: Part maintenance dates will be updated in bulk after all imports are complete
        return maintenance, "Created new maintenance record"

    def extract_maintenance_data(machine_data):
        """Extract maintenance records from nested machine data or flat CSV structure"""
        records = []
        
        # Handle nested JSON structure (existing logic)
        if 'MaintenanceData' in machine_data:
            maint_data = machine_data['MaintenanceData']
            machine_name = smart_field_mapping(machine_data, 'machines').get('name', '')
            
            # Process each part in the Parts array
            if 'Parts' in maint_data:
                for part_data in maint_data['Parts']:
                    if not part_data or not part_data.get('Part Name'):
                        continue
                    
                    part_name = part_data.get('Part Name', '')
                    maintenance_info = part_data.get('Maintenance', {})
                    
                    # Extract maintenance fields from the nested Maintenance object
                    maintenance_done = maintenance_info.get('Maintenance Done', '')
                    maintenance_type = maintenance_info.get('Maintenance Type', '')
                    last_pm_done = maintenance_info.get('Last PM Done', '')
                    required_materials = maintenance_info.get('Required Materials', '')
                    qty = maintenance_info.get('Qty.', '')
                    frequency = maintenance_info.get('Frequency', '')
                    
                    # Skip if no maintenance info
                    if not maintenance_done and not maintenance_type and not last_pm_done:
                        continue
                    
                    # Create a description from available fields
                    description_parts = [maintenance_done, maintenance_type, required_materials, f"Qty: {qty}"]
                    description = ' - '.join([part for part in description_parts if part]).strip(' -');
                    
                    # Parse frequency to get numeric value and unit
                    freq_value, freq_unit = 30, 'day'  # Default values
                    if frequency:
                        freq_value, freq_unit = parse_frequency_string(frequency)
                    
                    record = {
                        'machine_name': machine_name,
                        'part_name': part_name,  # Use the actual part name from JSON
                        'maintenance_type': maintenance_type,
                        'description': description,
                        'date': last_pm_done,
                        'performed_by': 'System Import',
                        'status': 'completed',
                        'notes': f"Materials: {required_materials}, Qty: {qty}, Frequency: {frequency}",
                        'maintenance_frequency': freq_value,
                        'maintenance_unit': freq_unit
                    }
                    
                    # Clean up the date format
                    if record['date']:
                        try:
                            # Handle the date format from JSON (e.g., "2025-01-16 00:00:00")
                            date_str = record['date'].split(' ')[0]  # Remove time part
                            record['date'] = date_str
                        except:
                            record['date'] = ''
                    
                    if record['machine_name'] and record['part_name']:
                        records.append(record)
            else:
                # Fallback for machines without Parts array - use main maintenance data
                record = {
                    'machine_name': machine_name,
                    'part_name': maint_data.get('Maintenance Done', 'General Maintenance'),  # Use maintenance done as part name
                    'maintenance_type': maint_data.get('Maintenance Type', 'Scheduled'),
                    'description': maint_data.get('Maintenance Done', ''),
                    'date': maint_data.get('Last PM Done', ''),
                    'performed_by': 'System Import',
                    'status': 'completed',
                    'notes': f"Materials: {maint_data.get('Required Materials', 'N/A')}, Qty: {maint_data.get('Qty.', 'N/A')}, Frequency: {maint_data.get('Frequency', 'N/A')}"
                }
                
                if record['date']:
                    try:
                        date_str = record['date'].split(' ')[0]
                        record['date'] = date_str
                    except:
                        record['date'] = ''
                
                if record['machine_name'] and record['description']:
                    records.append(record)
        
        # Handle flat CSV structure
        elif machine_data.get('part_name') and (machine_data.get('description') or machine_data.get('maintenance_type')):
            # Extract maintenance data from flat CSV row
            machine_name = smart_field_mapping(machine_data, 'machines').get('name', '')
            if not machine_name:
                # Try alternative machine name field
                machine_name = machine_data.get('machine_name', '')
            
            part_name = machine_data.get('part_name', '').strip()
            maintenance_type = machine_data.get('maintenance_type', 'Scheduled').strip()
            description = machine_data.get('description', '').strip()
            date = machine_data.get('date', '').strip()
            performed_by = machine_data.get('performed_by', 'System Import').strip()
            status = machine_data.get('status', 'completed').strip()
            notes = machine_data.get('notes', '').strip()
            
            # Parse frequency
            freq_value = 30  # default
            freq_unit = 'day'  # default
            
            if machine_data.get('maintenance_frequency'):
                try:
                    freq_value = int(machine_data.get('maintenance_frequency', 30))
                except (ValueError, TypeError):
                    freq_value = 30
            
            if machine_data.get('maintenance_unit'):
                freq_unit = machine_data.get('maintenance_unit', 'day').lower()
                # Convert months to days for consistency
                if freq_unit in ['month', 'months']:
                    freq_value = freq_value * 30
                    freq_unit = 'day'
                elif freq_unit in ['year', 'years']:
                    freq_value = freq_value * 365;
                    freq_unit = 'day'
                
                # Special case: if unit is empty but frequency is a valid number, treat as days
                if freq_value > 0 and not freq_unit:
                    freq_unit = 'day'
            
            if machine_name and part_name:
                record = {
                    'machine_name': machine_name,
                    'part_name': part_name,
                    'maintenance_type': maintenance_type,
                    'description': description,
                    'date': date,
                    'performed_by': performed_by or 'System Import',
                    'status': status or 'completed',
                    'notes': notes,
                    'maintenance_frequency': freq_value,
                    'maintenance_unit': freq_unit
                }
                
                records.append(record)
        
        return records

    if request.method == 'POST':
        entity = request.form.get('entity', 'unified')  # Default to unified import
        site_id = request.form.get('site_id')
        file = request.files.get('file')
        
        if not site_id or not file:
            flash('Site and file are required.', 'danger')
            return redirect(url_for('bulk_import'))
        
        # Validate site access
        site = Site.query.get(int(site_id))
        if not site:
            flash('Invalid site selected.', 'danger')
            return redirect(url_for('bulk_import'))
        
        if not current_user.is_admin and site not in current_user.sites:
            flash('You do not have access to the selected site.', 'danger')
            return redirect(url_for('bulk_import'))
        
        filename = secure_filename(file.filename)
        if not filename:
            flash('Invalid filename.', 'danger')
            return redirect(url_for('bulk_import'))
            
        ext = filename.rsplit('.', 1)[-1].lower()
        
        try:
            # Parse file based on extension
            if ext == 'csv':
                stream = file.stream.read().decode('utf-8')
                reader = csv.DictReader(stream.splitlines())
                data = list(reader)
            elif ext == 'json':
                data = _json.load(file.stream)
                if not isinstance(data, list):
                    flash('JSON must be an array of objects.', 'danger')
                    return redirect(url_for('bulk_import'))
            else:
                flash('Unsupported file type. Please upload CSV or JSON.', 'danger')
                return redirect(url_for('bulk_import'))
            
            added = 0
            updated = 0
            merged = 0
            errors = []
            
            # Process based on entity type
            if entity == 'machines':
                for row in data:
                    try:
                        # Skip rows with missing essential data
                        if not row or all(v is None or v == '' for v in row.values()):
                            continue
                        
                        machine, status = find_or_create_machine(row, int(site_id))
                        if not machine:
                            errors.append(f"Could not process machine: {status}")
                            continue
                        
                        # Add or update machine
                        if machine.id is None:  # New machine
                            db.session.add(machine)
                            db.session.flush()  # Get the ID
                            added += 1
                        elif "Updated" in status:
                            updated += 1
                        elif "Found" in status:
                            merged += 1
                        
                        # Extract and add parts from nested data
                        machine_name = smart_field_mapping(row, 'machines').get('name', '')
                        parts_data = extract_parts_data(row, machine_name)
                        
                        parts_added = 0
                        parts_updated = 0
                        for part_data in parts_data:
                            try:
                                part, part_status = find_or_create_part(part_data, machine)
                                if part:
                                    if part.id is None:  # New part
                                        db.session.add(part)
                                        parts_added += 1
                                    elif "Updated" in part_status:
                                        parts_updated += 1
                                    elif "Found" in part_status:
                                        merged += 1
                            except Exception as e:
                                errors.append(f"Error processing part '{part_data.get('name', '')}': {str(e)}")
                        
                        if parts_added > 0 or parts_updated > 0:
                            print(f"Processed {parts_added} new parts and {parts_updated} updated parts for machine '{machine_name}'")
                        
                        # Extract and add maintenance records from nested data
                        maintenance_records = extract_maintenance_data(row)
                        
                        maint_added = 0
                        maint_updated = 0
                        for record in maintenance_records:
                            try:
                                # Use the actual part name from the record
                                part_name = record.get('part_name', 'General Maintenance')
                                part = Part.query.filter_by(name=part_name, machine_id=machine.id).first()
                                
                                if not part:
                                    # If part doesn't exist, create it
                                    freq_value = record.get('maintenance_frequency', 365)
                                    freq_unit = record.get('maintenance_unit', 'day')
                                    
                                    part = Part(
                                        name=part_name,
                                        description=record.get('description', f'Auto-created for maintenance import'),
                                        machine_id=machine.id,
                                        maintenance_frequency=freq_value,
                                        maintenance_unit=freq_unit
                                    )
                                    db.session.add(part)
                                    db.session.flush()  # Get the ID
                                
                                # Use smart maintenance record creation with deduplication
                                maintenance, status = find_or_create_maintenance(record, machine, part)
                                
                                if maintenance:
                                    if maintenance.id is None:  # New maintenance record
                                        db.session.add(maintenance)
                                        maint_added += 1
                                    elif "Updated" in status:
                                        maint_updated += 1
                                    elif "Found" in status:
                                        merged += 1
                            except Exception as e:
                                errors.append(f"Error processing maintenance record for machine '{machine_name}': {str(e)}")
                    
                    except Exception as e:
                        errors.append(f"Error processing machine row: {str(e)}")
                        
            elif entity == 'parts':
                # Get machines for the selected site
                site_machines = {m.name: m.id for m in Machine.query.filter_by(site_id=int(site_id)).all()}
                
                for row in data:
                    try:
                        if not row or all(v is None or v == '' for v in row.values()):
                            continue
                        
                        # For parts import, we need to extract parts from the nested structure
                        machine_name = row.get('Machine')
                        if not machine_name:
                            errors.append(f"Row missing machine name: {row}")
                            continue
                        
                        if machine_name not in site_machines:
                            errors.append(f"Machine '{machine_name}' not found in site '{site.name}': {row}")
                            continue
                        
                        machine_id = site_machines[machine_name]
                        machine = Machine.query.get(machine_id)
                        
                        # Extract parts from MaintenanceData.Parts
                        if 'MaintenanceData' in row and 'Parts' in row['MaintenanceData']:
                            parts_list = row['MaintenanceData']['Parts']
                            
                            for part_data in parts_list:
                                if not part_data or not part_data.get('Part Name'):
                                    continue
                                
                                part_name = part_data.get('Part Name')
                                maintenance_info = part_data.get('Maintenance', {})
                                
                                # Parse frequency to get numeric value and unit
                                frequency_str = maintenance_info.get('Frequency', '1 Year')
                                freq_value, freq_unit = parse_frequency_string(frequency_str)
                                
                                # Create the part data in the format expected by find_or_create_part
                                mapped_part_data = {
                                    'name': part_name,
                                    'description': maintenance_info.get('Maintenance Done', ''),
                                    'machine_name': machine_name,
                                    'maintenance_frequency': freq_value,
                                    'maintenance_unit': freq_unit,
                                    'materials': maintenance_info.get('Required Materials', ''),
                                    'quantity': maintenance_info.get('Qty.', '')
                                }
                                
                                # Use smart part creation
                                part, status = find_or_create_part(mapped_part_data, machine)
                                
                                if part:
                                    if part.id is None:  # New part
                                        db.session.add(part)
                                        parts_added += 1
                                    elif "Updated" in status:
                                        updated += 1
                                    elif "Found" in status:
                                        merged += 1
                        else:
                            # Fallback for machines without Parts array - use main maintenance data
                            if 'MaintenanceData' in row:
                                maint_data = row['MaintenanceData']
                                part_name = maint_data.get('Maintenance Done', 'General Maintenance')
                                
                                if part_name and part_name != 'General Maintenance':
                                    frequency_str = maint_data.get('Frequency', '1 Year')
                                    freq_value, freq_unit = parse_frequency_string(frequency_str)
                                    
                                    mapped_part_data = {
                                        'name': part_name,
                                        'description': maint_data.get('Maintenance Done', ''),
                                        'machine_name': machine_name,
                                        'maintenance_frequency': freq_value,
                                        'maintenance_unit': freq_unit,
                                        'materials': maint_data.get('Required Materials', ''),
                                        'quantity': maint_data.get('Qty.', '')
                                    }
                                    
                                    part, status = find_or_create_part(mapped_part_data, machine)
                                    
                                    if part:
                                        if part.id is None:  # New part
                                            db.session.add(part)
                                            parts_added += 1
                                        elif "Updated" in status:
                                            updated += 1
                                        elif "Found" in status:
                                            merged += 1
                            
                    except Exception as e:
                        errors.append(f"Error processing part row: {str(e)}")

            elif entity == 'maintenance':
                # Get machines and parts for the selected site
                site_machines = {m.name: m for m in Machine.query.filter_by(site_id=int(site_id)).all()}
                
                # Handle both direct maintenance records and extracted from machine data
                maintenance_records = []
                
                for row in data:
                    if not row or all(v is None or v == '' for v in row.values()):
                        continue
                    
                    # Extract machine name from the row
                    machine_name = row.get('Machine')
                    if not machine_name:
                        continue
                    
                    # Check if this is machine data with nested maintenance
                    if 'MaintenanceData' in row and 'Parts' in row['MaintenanceData']:
                        # Extract maintenance records from each part
                        parts_list = row['MaintenanceData']['Parts']
                        
                        for part_data in parts_list:
                            if not part_data or not part_data.get('Part Name'):
                                continue
                            
                            part_name = part_data.get('Part Name')
                            maintenance_info = part_data.get('Maintenance', {})
                            
                            maintenance_record = {
                                'machine_name': machine_name,
                                'part_name': part_name,
                                'maintenance_type': maintenance_info.get('Maintenance Type', 'Scheduled'),
                                'description': maintenance_info.get('Maintenance Done', ''),
                                'date': maintenance_info.get('Last PM Done', ''),
                                'performed_by': 'System Import',
                                'status': 'completed',
                                'notes': f"Materials: {maintenance_info.get('Required Materials', 'N/A')}, Qty: {maintenance_info.get('Qty.', 'N/A')}, Frequency: {maintenance_info.get('Frequency', 'N/A')}"
                            }
                            
                            # Clean up the date format
                            if maintenance_record['date']:
                                try:
                                    date_str = maintenance_record['date'].split(' ')[0]  # Remove time part
                                    maintenance_record['date'] = date_str
                                except:
                                    maintenance_record['date'] = ''
                            
                            if maintenance_record['machine_name'] and maintenance_record['part_name']:
                                maintenance_records.append(maintenance_record)
                    
                    elif 'MaintenanceData' in row:
                        # Fallback: extract from top-level MaintenanceData if no Parts array
                        maint_data = row['MaintenanceData']
                        
                        maintenance_record = {
                            'machine_name': machine_name,
                            'part_name': maint_data.get('Maintenance Done', 'General Maintenance'),
                            'maintenance_type': maint_data.get('Maintenance Type', 'Scheduled'),
                            'description': maint_data.get('Maintenance Done', ''),
                            'date': maint_data.get('Last PM Done', ''),
                            'performed_by': 'System Import',
                            'status': 'completed',
                            'notes': f"Materials: {maint_data.get('Required Materials', 'N/A')}, Qty: {maint_data.get('Qty.', 'N/A')}, Frequency: {maint_data.get('Frequency', 'N/A')}"
                        }
                        
                        if maintenance_record['date']:
                            try:
                                date_str = maintenance_record['date'].split(' ')[0]
                                maintenance_record['date'] = date_str
                            except:
                                maintenance_record['date'] = ''
                        
                        if maintenance_record['machine_name'] and maintenance_record['description']:
                            maintenance_records.append(maintenance_record)
                    else:
                        # Direct maintenance record (not nested in MaintenanceData)
                        mapped = smart_field_mapping(row, 'maintenance')
                        if mapped.get('machine_name') and mapped.get('description'):
                            maintenance_records.append(mapped)
                
                # Process maintenance records
                for record in maintenance_records:
                    try:
                        machine_name = record.get('machine_name', '')
                        
                        if machine_name not in site_machines:
                            errors.append(f"Machine '{machine_name}' not found in site '{site.name}'")
                            continue
                        
                        machine = site_machines[machine_name]
                        
                        # Use the actual part name from the record, not a default
                        part_name = record.get('part_name')
                        if not part_name:
                            # If no part name specified, use the description or default
                            part_name = record.get('description', 'General Maintenance')
                        
                        # Find or create the part
                        part = Part.query.filter_by(name=part_name, machine_id=machine.id).first()
                        if not part:
                            # Create part with proper maintenance schedule from the record
                            freq_value = record.get('maintenance_frequency', 365)
                            freq_unit = record.get('maintenance_unit', 'day')
                            
                            part = Part(
                                name=part_name,
                                description=record.get('description', f'Auto-created for maintenance import'),
                                machine_id=machine.id,
                                maintenance_frequency=freq_value,
                                maintenance_unit=freq_unit
                            )
                            db.session.add(part)
                            db.session.flush()  # Get the ID
                        
                        # Use smart maintenance record creation with deduplication
                        maintenance, status = find_or_create_maintenance(record, machine, part)
                        
                        if maintenance:
                            if maintenance.id is None:  # New maintenance record
                                db.session.add(maintenance)
                                maintenance_added += 1
                            elif "Updated" in status:
                                updated += 1
                            elif "Found" in status:
                                merged += 1
                        
                    except Exception as e:
                        errors.append(f"Error processing maintenance record: {str(e)}")
            
            elif entity == 'unified':
                # Unified import - automatically process everything from the JSON
                # This processes machines, parts, and maintenance records in one go
                machines_added = 0
                parts_added = 0
                maintenance_added = 0
                
                for row in data:
                    try:
                        if not row or all(v is None or v == '' for v in row.values()):
                            continue
                        
                        # Step 1: Process machine
                        machine, machine_status = find_or_create_machine(row, int(site_id))
                        if not machine:
                            errors.append(f"Could not process machine: {machine_status}")
                            continue
                        
                        # Add or update machine
                        if machine.id is None:  # New machine
                            db.session.add(machine)
                            db.session.flush()  # Get the ID
                            machines_added += 1
                        elif "Updated" in machine_status:
                            updated += 1
                        elif "Found" in machine_status:
                            merged += 1
                        
                        # Step 2: Extract and process parts from nested data
                        machine_name = smart_field_mapping(row, 'machines').get('name', '')
                        parts_data = extract_parts_data(row, machine_name)
                        
                        for part_data in parts_data:
                            try:
                                part, part_status = find_or_create_part(part_data, machine)
                                if part:
                                    if part.id is None:  # New part
                                        db.session.add(part)
                                        parts_added += 1
                                    elif "Updated" in part_status:
                                        updated += 1
                                    elif "Found" in part_status:
                                        merged += 1
                            except Exception as e:
                                errors.append(f"Error processing part '{part_data.get('name', '')}': {str(e)}")
                        
                        # Step 3: Extract and process maintenance records from nested data
                        maintenance_records = extract_maintenance_data(row)
                        
                        for record in maintenance_records:
                            try:
                                # Use the actual part name from the record
                                part_name = record.get('part_name', 'General Maintenance')
                                part = Part.query.filter_by(name=part_name, machine_id=machine.id).first()
                                
                                if not part:
                                    # If part doesn't exist, create it
                                    freq_value = record.get('maintenance_frequency', 365)
                                    freq_unit = record.get('maintenance_unit', 'day')
                                    
                                    part = Part(
                                        name=part_name,
                                        description=record.get('description', f'Auto-created for maintenance import'),
                                        machine_id=machine.id,
                                        maintenance_frequency=freq_value,
                                        maintenance_unit=freq_unit
                                    )
                                    db.session.add(part)
                                    db.session.flush()  # Get the ID
                                
                                # Use smart maintenance record creation with deduplication
                                maintenance, status = find_or_create_maintenance(record, machine, part)
                                
                                if maintenance:
                                    if maintenance.id is None:  # New maintenance record
                                        db.session.add(maintenance)
                                        maintenance_added += 1
                                    elif "Updated" in status:
                                        updated += 1
                                    elif "Found" in status:
                                        merged += 1
                            except Exception as e:
                                errors.append(f"Error processing maintenance record for machine '{machine_name}': {str(e)}")
                    
                    except Exception as e:
                        errors.append(f"Error processing row: {str(e)}")
                
                # Update the added count to include all types
                added = machines_added + parts_added + maintenance_added
            
            else:
                flash('Invalid entity type.', 'danger')
                return redirect(url_for('bulk_import'))
            
            # Commit changes
            if added > 0 or updated > 0:
                db.session.commit()
                
                # After importing, update all part maintenance dates based on actual maintenance records
                # This ensures parts show correct last/next maintenance dates regardless of import order
                if entity in ['maintenance', 'unified']:
                    updated_parts = set()
                    
                    # Find all parts that were affected by the import
                    if entity == 'maintenance':
                        # For maintenance imports, get parts from the selected site
                        site_machines = Machine.query.filter_by(site_id=int(site_id)).all()
                        for machine in site_machines:
                            for part in machine.parts:
                                update_part_maintenance_dates(part)
                                updated_parts.add(part.name)
                    
                    elif entity == 'unified':
                        # For unified imports, get all parts from the imported machines
                        site_machines = Machine.query.filter_by(site_id=int(site_id)).all()
                        for machine in site_machines:
                            for part in machine.parts:
                                update_part_maintenance_dates(part)
                                updated_parts.add(part.name)
                    
                    # Commit the part updates
                    if updated_parts:
                        db.session.commit()
                        app.logger.info(f"Updated maintenance dates for {len(updated_parts)} parts: {', '.join(list(updated_parts)[:10])}")
            
            # Provide detailed feedback
            total_processed = added + updated + merged
            if total_processed > 0:
                feedback_parts = []
                if added > 0:
                    feedback_parts.append(f"{added} new")
                if updated > 0:
                    feedback_parts.append(f"{updated} updated")
                if merged > 0:
                    feedback_parts.append(f"{merged} merged/skipped")
                
                feedback_msg = f'Successfully processed {total_processed} records to site "{site.name}" ({", ".join(feedback_parts)})'
                
                if errors:
                    feedback_msg += f' with {len(errors)} errors. First few errors: {"; ".join(errors[:3])}'
                    flash(feedback_msg, 'warning')
                else:
                    flash(feedback_msg, 'success')
            else:
                if errors:
                    flash(f'No records processed due to {len(errors)} errors. First few: {"; ".join(errors[:3])}', 'danger')
                else:
                    flash('No valid records found to import.', 'warning')
                
        except Exception as e:
            db.session.rollback()
            flash(f'Import failed: {str(e)}', 'danger')
            
        return redirect(url_for('bulk_import'))
    
    # GET request - show the form
    return render_template('admin/bulk_import.html', sites=sites)

def update_part_maintenance_dates(part):
    """Update part's last_maintenance and next_maintenance based on actual maintenance records"""
    from datetime import timedelta
    
    # Find the most recent maintenance record for this part
    latest_maintenance = MaintenanceRecord.query.filter_by(
        part_id=part.id
    ).order_by(MaintenanceRecord.date.desc()).first()
    
    if latest_maintenance:
        # Update last_maintenance to the actual latest date
        part.last_maintenance = latest_maintenance.date
        
        # Calculate next maintenance date based on frequency
        freq = part.maintenance_frequency or 30
        unit = part.maintenance_unit or 'day'
        
        if unit == 'week':
            delta = timedelta(weeks=freq)
        elif unit == 'month':
            delta = timedelta(days=freq * 30)
        elif unit == 'year':
            delta = timedelta(days=freq * 365)
        else:
            delta = timedelta(days=freq)
            
        part.next_maintenance = part.last_maintenance + delta
        
        app.logger.info(f"Updated part '{part.name}' - Last maintenance: {part.last_maintenance}, Next: {part.next_maintenance}")
    else:
        # No maintenance records found, clear the dates
        part.last_maintenance = None
        part.next_maintenance = None

def safe_date(year, month, day):
    """Safely create a date object, returning None if the date is invalid."""
    try:
        return date(year, month, day)
    except ValueError:
        return None

@app.context_processor
def inject_safe_date_utility():
    """Inject the safe_date function into the template context."""
    return dict(safe_date=safe_date)

# Enhanced context processors and utility functions
@app.context_processor
def inject_debug_context():
    """Inject debug information and utilities into template context."""
    return dict(
        app_debug=app.debug,
        current_route=request.endpoint if request else None,
        app_name="AMRS Maintenance Tracker",
        version="2.0.0"
    )

@app.context_processor
def inject_permission_helpers():
    """Inject permission helper functions into template context."""
    def has_permission(permission_name):
        """Check if current user has a specific permission."""
        if not current_user.is_authenticated:
            return False
        if is_admin_user(current_user):
            return True
        if hasattr(current_user, 'role') and current_user.role and current_user.role.permissions:
            return permission_name in current_user.role.permissions.split(',')
        return False
    
    def can_access_all_sites():
        """Check if user can access all sites."""
        return user_can_see_all_sites(current_user)
    
    return dict(
        has_permission=has_permission,
        can_access_all_sites=can_access_all_sites,
        is_admin=lambda: is_admin_user(current_user) if current_user.is_authenticated else False
    )

# Serve uploaded maintenance files
@app.route('/files/<int:file_id>')
@login_required
def serve_uploaded_file(file_id):
    maintenance_file = MaintenanceFile.query.get_or_404(file_id)
    # Only allow access to users who can see the record
    record = maintenance_file.maintenance_record
    if not (current_user.is_admin or record.user_id == current_user.id):
        abort(403)
    return send_file(maintenance_file.filepath, as_attachment=True, download_name=maintenance_file.filename)

# Serve uploaded maintenance file thumbnails (fallback to original if not available)
@app.route('/files/<int:file_id>/thumb')
@login_required
def serve_uploaded_thumbnail(file_id):
    maintenance_file = MaintenanceFile.query.get_or_404(file_id)
    # Only allow access to users who can see the record
    record = maintenance_file.maintenance_record
    if not (current_user.is_admin or record.user_id == current_user.id):
        abort(403)
    if maintenance_file.thumbnail_path and os.path.exists(maintenance_file.thumbnail_path):
        return send_file(maintenance_file.thumbnail_path, as_attachment=False)
    else:
        return send_file(maintenance_file.filepath, as_attachment=False)
    
# Enhanced error handlers with better user experience
@app.errorhandler(404)
def enhanced_page_not_found(e):
    """Enhanced 404 handler with user-friendly message."""
    app.logger.warning(f"404 Page Not Found: {request.path}")
    try:
        return render_template('errors/404.html'), 404
    except:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Page Not Found - AMRS Maintenance</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="row justify-content-center">
                    <div class="col-md-6 text-center">
                        <h1 class="display-1 text-primary">404</h1>
                        <h2>Page Not Found</h2>
                        <p class="lead">The page you're looking for doesn't exist.</p>
                        <a href="/" class="btn btn-primary">Go Home</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        ''', 404

@app.errorhandler(500)
def enhanced_server_error(e):
    """Enhanced 500 handler with better error reporting."""
    app.logger.error(f"500 Server Error: {request.path} - {str(e)}")
    try:
        return render_template('errors/500.html'), 500
    except:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Server Error - AMRS Maintenance</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="row justify-content-center">
                    <div class="col-md-6 text-center">
                        <h1 class="display-1 text-danger">500</h1>
                        <h2>Server Error</h2>
                        <p class="lead">Something went wrong on our end.</p>
                        <a href="/" class="btn btn-primary">Go Home</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        ''', 500
    



# --- CONSOLIDATED DATABASE CONFIGURATION ---
# Initialize database configuration immediately on import

print("[AMRS] Starting consolidated database configuration...")

# Determine environment and database type
POSTGRESQL_DATABASE_URI = os.environ.get('DATABASE_URL')
is_render_env = os.environ.get('RENDER') or os.environ.get('RENDER_SERVICE_NAME')

print(f"[DEBUG] DATABASE_URL value: {POSTGRESQL_DATABASE_URI}")
print(f"[DEBUG] RENDER env: {os.environ.get('RENDER')}")
print(f"[DEBUG] is_render_env: {is_render_env}")

# Use the same offline detection as the rest of the application
try:
    from timezone_utils import is_offline_mode as detect_offline_mode
    offline_mode = detect_offline_mode()
    print(f"[DEBUG] offline_mode: {offline_mode}")
except ImportError as e:
    print(f"[DEBUG] Could not import timezone_utils: {e}")
    print("[DEBUG] Assuming online mode due to import error")
    offline_mode = False

# Check if DATABASE_URL is actually PostgreSQL
is_postgresql_url = POSTGRESQL_DATABASE_URI and ('postgresql://' in POSTGRESQL_DATABASE_URI or 'postgres://' in POSTGRESQL_DATABASE_URI)
print(f"[DEBUG] is_postgresql_url: {is_postgresql_url}")

# Configure database based on environment
if is_render_env:
    # Render environment: always use PostgreSQL
    if is_postgresql_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = POSTGRESQL_DATABASE_URI
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        print("[AMRS] RENDER MODE: Using PostgreSQL database")
    else:
        print("[AMRS] ERROR: RENDER environment but no DATABASE_URL found!")
        print(f"[AMRS] DEBUG: DATABASE_URL = '{POSTGRESQL_DATABASE_URI}'")
        print(f"[AMRS] DEBUG: is_postgresql_url = {is_postgresql_url}")
        # Don't exit here - let the app try to continue with SQLite fallback
        print("[AMRS] FALLBACK: Attempting to use SQLite database")
        secure_db_path = get_secure_database_path()
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{secure_db_path}"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
elif offline_mode:
    # Local offline mode: use secure bootstrap database if available, otherwise local SQLite
    secure_db_path = get_secure_database_path()
    
    if os.path.exists(secure_db_path):
        # Use the existing secure database from previous bootstrap
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{secure_db_path}"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        print(f"[AMRS] OFFLINE MODE: Using existing secure database: {secure_db_path}")
    else:
        # Fallback to local database
        db_path = os.path.join(os.path.dirname(__file__), "maintenance.db")
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        print(f"[AMRS] OFFLINE MODE: Using local SQLite fallback at {db_path}")
else:
    # Local online mode: use PostgreSQL if available, fallback to SQLite
    if is_postgresql_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = POSTGRESQL_DATABASE_URI
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        print("[AMRS] LOCAL ONLINE MODE: Using PostgreSQL database")
    else:
        db_path = os.path.join(os.path.dirname(__file__), "maintenance.db")
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        print(f"[AMRS] LOCAL FALLBACK MODE: Using SQLite at {db_path}")

# Initialize database with Flask app after configuration is complete
db.init_app(app)
try:
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', None)
    print(f"[AMRS] Database initialized successfully - URI: {db_uri}")
except Exception as db_uri_exc:
    print(f"[AMRS] Could not retrieve SQLALCHEMY_DATABASE_URI: {db_uri_exc}")

# Perform all database setup within app context immediately on import
with app.app_context():
    try:
        # First run comprehensive schema validation and migration
        print("[AMRS] Running comprehensive schema validation...")
        from schema_validator import validate_and_migrate_schema, verify_schema_integrity
        
        # Get the database path from current configuration
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if 'sqlite:///' in db_uri:
            db_path = db_uri.replace('sqlite:///', '')
            print(f"[AMRS] Validating schema for SQLite database: {db_path}")
            
            # Run schema validation and migration
            success, results = validate_and_migrate_schema(db_path, verbose=False)
            if success:
                print(f"[AMRS] SUCCESS: Schema validation completed: {results['tables_created']} tables created, {results['columns_added']} columns added")
                
                # Verify schema integrity
                valid, issues = verify_schema_integrity(db_path, verbose=False)
                if not valid:
                    print(f"[AMRS] WARNING: Schema issues detected: {len(issues)} remaining issues")
                    for issue in issues[:3]:  # Show first 3 issues
                        print(f"[AMRS]   - {issue}")
                else:
                    print("[AMRS] SUCCESS: Schema integrity verified - all required columns present")
            else:
                print(f"[AMRS] ERROR: Schema validation failed: {results.get('error', 'Unknown error')}")
        else:
            print("[AMRS] Skipping schema validation for non-SQLite database")
        
        # Run legacy auto-migration for any remaining fixes
        print("[AMRS] Running legacy auto-migration...")
        try:
            run_auto_migration()
            print("[AMRS] Auto-migration completed successfully")
        except Exception as e:
            print(f"[AMRS] Warning: Auto-migration failed: {e}")
            print("[AMRS] Continuing without auto-migration...")
        
        # Create tables if needed
        db.create_all()
        print("[AMRS] Database tables ensured")
        # --- Generalized auto-migration: ensure all required columns exist in all critical tables ---
        try:
            import sqlite3
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if db_uri.startswith('sqlite:///'):
                db_path = db_uri.replace('sqlite:///', '')
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                table_columns = {
                    'security_events': {
                        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                        'timestamp': 'DATETIME',
                        'event_type': 'VARCHAR(64)',
                        'user_id': 'INTEGER',
                        'username': 'VARCHAR(255)',
                        'ip_address': 'VARCHAR(64)',
                        'location': 'VARCHAR(255)',
                        'details': 'TEXT',
                        'is_critical': 'BOOLEAN'
                    },
                    'parts': {
                        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                        'name': 'VARCHAR(255)',
                        'description': 'TEXT',
                        'machine_id': 'INTEGER',
                        'maintenance_frequency': 'INTEGER',
                        'maintenance_unit': 'VARCHAR(32)',
                        'maintenance_days': 'INTEGER',
                        'last_maintenance': 'DATETIME',
                        'next_maintenance': 'DATETIME',
                        'created_at': 'DATETIME',
                        'updated_at': 'DATETIME'
                    },
                    'sync_queue': {
                        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                        'table_name': 'VARCHAR(64)',
                        'record_id': 'INTEGER',
                        'operation': 'VARCHAR(32)',
                        'payload': 'TEXT',
                        'created_at': 'DATETIME',
                        'status': 'VARCHAR(32)'
                    },
                    # Add more tables and columns as needed
                }
                for table, required_columns in table_columns.items():
                    try:
                        c.execute(f"PRAGMA table_info({table});")
                        columns = [row[1] for row in c.fetchall()]
                        for col, coltype in required_columns.items():
                            if col not in columns:
                                print(f"[AMRS] Adding missing column {col} to {table} table...")
                                c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coltype};")
                                conn.commit()
                    except Exception as e:
                        print(f"[AMRS] Could not check/add columns in {table}: {e}")
                conn.close()
        except Exception as e:
            print(f"[AMRS] Generalized auto-migration error: {e}")
        
        # Ensure sync_queue and app_settings tables exist
        try:
            import add_sync_queue_table
            add_sync_queue_table.upgrade()
            print('[AMRS] Ensured sync_queue table exists')
        except Exception as e:
            print(f'[AMRS] Warning: Could not ensure sync_queue table: {e}')
        
        try:
            import migrate_app_settings
            migrate_app_settings.upgrade()
            print('[AMRS] Ensured app_settings table exists')
        except Exception as e:
            print(f'[AMRS] Warning: Could not ensure app_settings table: {e}')
        
        # Additional setup for online servers
        if not offline_mode:
            try:
                # Ensure sync columns exist
                ensure_sync_columns()
                print('[AMRS] Ensured sync columns exist')
                
                # Ensure audit task-machine associations exist for sync export
                try:
                    ensure_online_server_audit_associations()
                    print("[AMRS] Online server audit associations ensured")
                except Exception as e:
                    print(f"[AMRS] Warning: Could not ensure online server audit associations: {e}")
                
                # Run any additional startup tasks  
                try:
                    assign_colors_to_audit_tasks()
                    print("[AMRS] Audit task colors assigned")
                except Exception as e:
                    print(f"[AMRS] Warning: Could not assign audit task colors: {e}")
                
                print("[AMRS] Online mode database setup completed")
            except Exception as e:
                print(f"[AMRS] Warning: Online mode setup error: {e}")
    
    except Exception as e:
        print(f"[AMRS] Error during database setup: {e}")
        import traceback
        traceback.print_exc()

print("[AMRS] Database initialization and setup completed")

def initialize_bootstrap_only():
    """Run bootstrap operations only - database is already initialized above."""
    print("[AMRS] Running bootstrap operations...")
    
    # Use the same offline detection as above
    offline_mode = detect_offline_mode()
    
    # Initialize sync worker for offline clients only (after all setup is complete)
    if offline_mode:
        try:
            start_enhanced_sync_worker()
            print("[AMRS] Enhanced sync worker started for offline mode")
        except Exception as e:
            print(f"[AMRS] Warning: Failed to start sync worker: {e}")

    print("[AMRS] Bootstrap operations completed")

    # ========================================
    # AUTOMATIC BOOTSTRAP AND SYNC FOR OFFLINE APPLICATIONS
    # ========================================
    # This section automatically configures offline applications when they start
    from timezone_utils import is_offline_mode

    # Ensure audit task-machine associations exist for proper UI display
    try:
        if is_offline_mode():
            db_path = get_secure_database_path()
            ensure_audit_task_machine_associations(db_path)
    except Exception as e:
        print(f"[AMRS] Warning: Could not ensure audit task associations: {e}")

    if is_offline_mode():
        print("\n" + "="*60)
        print("AUTOMATIC BOOTSTRAP FOR OFFLINE APPLICATION")
        print("="*60)
        
        try:
            # Verify and complete bootstrap if needed
            if not verify_bootstrap_success():
                print("[AUTO-BOOTSTRAP] Bootstrap verification failed, attempting full bootstrap...")
                bootstrap_success = bootstrap_secrets_from_remote()
                
                if bootstrap_success:
                    print("[AUTO-BOOTSTRAP] SUCCESS: Bootstrap completed successfully")
                    
                    # Update database configuration to use secure database
                    secure_db_path = get_secure_database_path()
                    if os.path.exists(secure_db_path):
                        # Reinitialize database connection with secure database
                        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{secure_db_path}'
                        
                        # Reinitialize the database
                        with app.app_context():
                            db.engine.dispose()  # Close old connections
                            # db.init_app(app) - Already initialized, just dispose and recreate
                            db.create_all()      # Ensure all tables exist
                        
                        print(f"[AUTO-BOOTSTRAP] SUCCESS: Switched to secure database: {secure_db_path}")
                    else:
                        print("[AUTO-BOOTSTRAP] WARNING: Bootstrap completed but secure database not found")
                else:
                    print("[AUTO-BOOTSTRAP] ERROR: Bootstrap failed - application will use local configuration")
            else:
                print("[AUTO-BOOTSTRAP] SUCCESS: Bootstrap verification passed - application ready")
                
                # Ensure we're using the secure database
                secure_db_path = get_secure_database_path()
                current_db = app.config.get('SQLALCHEMY_DATABASE_URI', '')
                
                if secure_db_path not in current_db:
                    print("[AUTO-BOOTSTRAP] Updating to use secure database...")
                    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{secure_db_path}'
                    
                    with app.app_context():
                        db.engine.dispose()
                        # db.init_app(app) - Already initialized, just dispose
                        
                    print(f"[AUTO-BOOTSTRAP] SUCCESS: Using secure database: {secure_db_path}")
            
            # Final verification
            print("\nBOOTSTRAP STATUS SUMMARY:")
            print("-" * 40)
            
            # Check credentials
            import keyring
            service = get_secure_storage_service()
            creds_available = bool(keyring.get_password(service, 'AMRS_ADMIN_USERNAME'))
            print(f"[BOOTSTRAP] Credentials Available: {'YES' if creds_available else 'NO'}")
            
            # Check database
            secure_db_path = get_secure_database_path()
            db_available = os.path.exists(secure_db_path)
            print(f"[BOOTSTRAP] Secure Database: {'YES' if db_available else 'NO'}")
            
            if db_available:
                try:
                    import sqlite3
                    conn = sqlite3.connect(secure_db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM users WHERE active = 1")
                    user_count = cursor.fetchone()[0]
                    conn.close()
                    print(f"Active Users: {user_count}")
                    
                    if user_count > 0:
                        print("\nOFFLINE APPLICATION READY!")
                        print("Users can now login with their online credentials")
                    else:
                        print("\n[BOOTSTRAP] WARNING: DATABASE SYNC NEEDED")
                        print("No users found - database sync may have failed")
                except Exception as e:
                    print(f"[BOOTSTRAP] Database check error: {e}")
            
            print("="*60)
            
        except Exception as e:
            print(f"[AUTO-BOOTSTRAP] Error during automatic bootstrap: {e}")
            print("[AUTO-BOOTSTRAP] Application will continue with local configuration")
    else:
        print("[BOOTSTRAP] Online server mode - skipping automatic bootstrap")
    
    return offline_mode  # Return offline_mode for use in socketio.run

# Standard Flask app runner for local/offline mode (must be at the very end of the file)
if __name__ == "__main__":
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'NOT SET')
    print(f"[AMRS] Launching app with database URI: {db_uri}")
    # Initialize bootstrap operations - database is already initialized above
    offline_mode = initialize_bootstrap_only()
    
    # Run the Flask app with SocketIO for WebSocket support
    port = int(os.environ.get("PORT", 10000))
    debug = os.environ.get("FLASK_ENV", "production") == "development"
    host = "127.0.0.1" if offline_mode else "0.0.0.0"
    print(f"[AMRS] Starting Flask-SocketIO server on {host}:{port}")
    
    # Allow Werkzeug development server for Electron desktop app usage
    # This is safe for our use case since the app is running locally for offline functionality
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)