"""
Offline mode adapter for the AMRS Maintenance Tracker application.
This module provides functionality to adapt the main application for offline use.
"""
import os
import sqlite3
import logging
from datetime import datetime
from functools import wraps
from flask import session, g, redirect, url_for, request, flash, jsonify
import jwt

logger = logging.getLogger(__name__)

# Flag to indicate if we're in offline mode
OFFLINE_MODE = os.environ.get('OFFLINE_MODE', 'false').lower() == 'true'

class OfflineAdapter:
    """Adapter for offline functionality"""
    
    def __init__(self, app):
        self.app = app
        self.db_path = os.environ.get('DATABASE_PATH', 'maintenance_local.db')
        logger.info(f"Initializing offline adapter with DB: {self.db_path}")
    
    def setup(self):
        """Set up offline mode on the Flask app"""
        if not OFFLINE_MODE:
            logger.info("Not in offline mode, skipping offline adapter setup")
            return
        
        logger.info("Setting up offline mode")
        self.app.config['OFFLINE_MODE'] = True
        
        # Register offline database functions
        self.app.teardown_appcontext(self.close_db)
        
        # Inject offline helper functions into the template context
        @self.app.context_processor
        def inject_offline_mode():
            return {'offline_mode': True}
    
    def get_db(self):
        """Get SQLite database connection for offline mode"""
        if 'offline_db' not in g:
            try:
                logger.info(f"Opening offline database at: {self.db_path}")
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                g.offline_db = conn
            except Exception as e:
                logger.error(f"Error opening offline database: {e}")
                g.offline_db = None
        
        return g.offline_db
    
    def close_db(self, e=None):
        """Close the offline database connection"""
        db = g.pop('offline_db', None)
        if db is not None:
            db.close()
    
    def verify_token(self, token):
        """Verify a JWT token in offline mode"""
        try:
            # Use SQLite to check token
            db = self.get_db()
            if not db:
                return None
            
            # Find the token in the database
            user = db.execute(
                'SELECT * FROM users WHERE token = ? AND token_expiry > datetime("now")', 
                (token,)
            ).fetchone()
            
            if user:
                return {
                    'user_id': user['id'],
                    'username': user['username'],
                    'role_id': user['role_id']
                }
            
            return None
        except Exception as e:
            logger.error(f"Error verifying offline token: {e}")
            return None
    
def offline_login_required(f):
    """Decorator for routes that require login in offline mode"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not OFFLINE_MODE:
            # Use regular login_required in online mode
            from flask_login import login_required as flask_login_required
            return flask_login_required(f)(*args, **kwargs)
        
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_offline_user():
    """Get the current user in offline mode"""
    if not OFFLINE_MODE or 'user_id' not in session:
        return None
    
    from flask import current_app
    adapter = current_app.offline_adapter
    db = adapter.get_db()
    
    if not db:
        return None
    
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    return user

def is_admin_offline():
    """Check if the current user is an admin in offline mode"""
    if not OFFLINE_MODE:
        return False
    
    user = get_offline_user()
    if not user:
        return False
    
    # Role ID 1 is typically the admin role
    return user['role_id'] == 1

def check_offline_permission(user, permission):
    """Check if a user has a specific permission in offline mode"""
    if not user:
        return False
    
    from flask import current_app
    adapter = current_app.offline_adapter
    db = adapter.get_db()
    
    if not db:
        return False
    
    # Get user's role
    role = db.execute('SELECT * FROM roles WHERE id = ?', (user['role_id'],)).fetchone()
    
    if not role:
        return False
    
    # Check permissions
    permissions = role['permissions'].split(',') if role['permissions'] else []
    return permission in permissions

def get_user_permissions(user_id):
    """Get permissions for a user in offline mode"""
    from flask import current_app
    adapter = current_app.offline_adapter
    db = adapter.get_db()
    
    if not db:
        return []
    
    # Get user's role
    user = db.execute('SELECT role_id FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        return []
    
    # Get role's permissions
    role = db.execute('SELECT permissions FROM roles WHERE id = ?', (user['role_id'],)).fetchone()
    
    if not role or not role['permissions']:
        return []
    
    # Return permissions as a list
    return role['permissions'].split(',')

def has_permission(permission):
    """Decorator to check if user has a specific permission in offline mode"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not OFFLINE_MODE:
                # Use regular permission check in online mode
                from app import has_permission as online_has_permission
                return online_has_permission(permission)(f)(*args, **kwargs)
            
            if 'user_id' not in session:
                return redirect(url_for('login', next=request.url))
            
            # Check if user has the required permission
            permissions = get_user_permissions(session['user_id'])
            
            if 'admin' in permissions or permission in permissions:
                return f(*args, **kwargs)
            
            flash('You do not have permission to access that page.', 'danger')
            return redirect(url_for('index'))
            
        return decorated_function
    return decorator

# Helper function to initialize the offline database schema if needed
def init_offline_db(db_path):
    """Initialize the offline database schema if it doesn't exist"""
    if os.path.exists(db_path):
        return

    logger.info(f"Creating new offline database at {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.executescript('''
        -- Users table
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            role_id INTEGER,
            token TEXT,
            token_expiry TIMESTAMP
        );
        
        -- Roles table
        CREATE TABLE roles (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            permissions TEXT
        );
        
        -- Sites table
        CREATE TABLE sites (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT,
            last_sync TIMESTAMP
        );
        
        -- Machines table
        CREATE TABLE machines (
            id INTEGER PRIMARY KEY,
            site_id INTEGER,
            name TEXT NOT NULL,
            model TEXT,
            FOREIGN KEY (site_id) REFERENCES sites(id)
        );
        
        -- Parts table
        CREATE TABLE parts (
            id INTEGER PRIMARY KEY,
            machine_id INTEGER,
            name TEXT NOT NULL,
            part_number TEXT,
            last_maintenance_date TIMESTAMP,
            maintenance_frequency INTEGER,
            maintenance_unit TEXT,
            FOREIGN KEY (machine_id) REFERENCES machines(id)
        );
        
        -- Maintenance records
        CREATE TABLE maintenance_records (
            id INTEGER PRIMARY KEY,
            machine_id INTEGER,
            part_id INTEGER,
            user_id INTEGER,
            maintenance_date TIMESTAMP,
            notes TEXT,
            sync_status TEXT DEFAULT 'pending',
            FOREIGN KEY (machine_id) REFERENCES machines(id),
            FOREIGN KEY (part_id) REFERENCES parts(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        -- Sync tracking table
        CREATE TABLE sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT,
            record_id INTEGER,
            sync_action TEXT,
            sync_status TEXT DEFAULT 'pending',
            sync_timestamp TIMESTAMP,
            error_message TEXT
        );
        
        -- Insert default admin role
        INSERT INTO roles (id, name, description, permissions)
        VALUES (1, 'Admin', 'Administrator with full access', 'admin,view_sites,manage_sites,view_machines,manage_machines,view_parts,manage_parts,view_maintenance,manage_maintenance');
    ''')
    conn.commit()
    conn.close()
