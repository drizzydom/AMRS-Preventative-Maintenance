import os
import sys
import logging
import base64
from cryptography.fernet import Fernet
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Electron environment detection
def is_electron():
    """Detect if running in Electron environment"""
    return os.environ.get('ELECTRON_RUN_AS_NODE') is not None or os.environ.get('AMRS_ELECTRON') == '1'

# Application paths
def get_app_dir():
    """Get the application directory for storing data"""
    if is_electron():
        # In Electron, use the user's AppData or equivalent
        if sys.platform == 'win32':
            app_dir = Path(os.environ.get('APPDATA', '')) / 'AMRS-Maintenance-Tracker'
        elif sys.platform == 'darwin':
            app_dir = Path.home() / 'Library' / 'Application Support' / 'AMRS-Maintenance-Tracker'
        else:  # Linux and others
            app_dir = Path.home() / '.amrs-maintenance-tracker'
        
        # Create directory if it doesn't exist
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir
    else:
        # For regular Flask app, use current directory
        return Path(os.getcwd())

# Database configuration
def get_database_uri():
    """Get the appropriate database URI based on environment"""
    if is_electron():
        db_path = get_app_dir() / 'amrs_maintenance.db'
        logger.info(f"Using SQLite database at: {db_path}")
        return f"sqlite:///{db_path}"
    else:
        # For regular web app, use PostgreSQL from environment variable
        return os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost/amrs_maintenance')

# Encryption key management
def get_encryption_key():
    """Get or create encryption key for user data"""
    key_path = get_app_dir() / 'encryption.key'
    
    if key_path.exists():
        with open(key_path, 'rb') as f:
            key = f.read()
    else:
        # Generate a new key
        key = Fernet.generate_key()
        with open(key_path, 'wb') as f:
            f.write(key)
        logger.info(f"Generated new encryption key at: {key_path}")
    
    return key.decode() if isinstance(key, bytes) else key

# Flask configuration for Electron
class ElectronConfig:
    """Configuration for Flask when running in Electron"""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'electron-dev-secret-key')
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail settings (disabled in electron mode)
    MAIL_SERVER = None
    MAIL_PORT = None
    MAIL_USE_TLS = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = 'noreply@example.com'
    
    # Set this to True when ready to ship
    ELECTRON_PRODUCTION = False