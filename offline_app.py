#!/usr/bin/env python3
"""
Simplified AMRS Maintenance Tracker app for testing offline mode
"""
import os
import sys
import logging
import time
import json
from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
from pathlib import Path
from db_controller import DatabaseController

# Configure logging
logging.basicConfig(level=logging.INFO, format='[OFFLINE_APP] %(levelname)s - %(message)s')
logger = logging.getLogger("offline_app")

# Try to import token managers
try:
    from token_manager import TokenManager
    from enhanced_token_manager import EnhancedTokenManager
    has_token_manager = True
    
    # Determine which token manager to use
    use_enhanced_manager = os.environ.get('USE_ENHANCED_TOKEN_MANAGER', 'true').lower() == 'true'
    if use_enhanced_manager:
        logger.info("Using EnhancedTokenManager for token authentication")
    else:
        logger.info("Using basic TokenManager for token authentication")
    
    logger.info("Token manager modules imported successfully")
except ImportError:
    has_token_manager = False
    use_enhanced_manager = False
    logger.warning("Token manager modules not found, token authentication will be disabled")

# Create a database controller
db_controller = DatabaseController(use_encryption=False)

# Initialize token manager if available
token_manager = None
if has_token_manager:
    # Use the token expiry from environment variable or default to 30 days
    token_expiry_days = int(os.environ.get('TOKEN_EXPIRY_DAYS', '30'))
    # Use the secret key from environment variable or default to a secure value
    secret_key = os.environ.get('JWT_SECRET_KEY', 'secure_offline_jwt_secret_key_for_testing')
    
    if use_enhanced_manager:
        # Use enhanced token manager with additional features
        token_manager = EnhancedTokenManager(
            secret_key=secret_key,
            token_expiry_days=token_expiry_days,
            refresh_threshold_days=int(os.environ.get('TOKEN_REFRESH_THRESHOLD_DAYS', '5')),
            use_encrypted_storage=os.environ.get('ENCRYPT_TOKEN_STORAGE', 'false').lower() == 'true'
        )
    else:
        # Use basic token manager
        token_manager = TokenManager(
            secret_key=secret_key,
            token_expiry_days=token_expiry_days
        )
    logger.info(f"Token manager initialized with {token_expiry_days} days expiry")

# Create Flask app
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
            static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))

# Force offline mode
os.environ['OFFLINE_MODE'] = 'true'

# Configure the app
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'development-key')

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, is_admin=False, role_id=None, token=None):
        self.id = id
        self.username = username
        self.is_admin = is_admin
        self.role_id = role_id
        self.last_login = datetime.utcnow()
        self.token = token  # Store the user's token

    def get_token(self):
        """Get the user's token, refreshing if needed"""
        if has_token_manager and token_manager and not self.token:
            # Try to retrieve token from storage
            self.token = token_manager.retrieve_token(self.id)
            
        return self.token
        
    def check_token_expiry(self):
        """Check if the user's token is expired or needs refreshing"""
        if not self.token or not has_token_manager or not token_manager:
            return None
            
        # Validate token without auto-refresh
        payload = token_manager.validate_token(self.token, auto_refresh=False)
        
        if not payload:
            return {
                'is_valid': False,
                'needs_refresh': True
            }
            
        # Check if token is approaching expiry
        if 'exp' in payload:
            expiry_timestamp = payload['exp']
            now = int(time.time())
            seconds_remaining = expiry_timestamp - now
            days_remaining = seconds_remaining / (60 * 60 * 24)
            
            return {
                'is_valid': True,
                'expires_at': datetime.fromtimestamp(expiry_timestamp).isoformat(),
                'days_remaining': days_remaining,
                'seconds_remaining': seconds_remaining,
                'needs_refresh': days_remaining < 5  # If less than 5 days, suggest refresh
            }
        
        return {
            'is_valid': True,
            'needs_refresh': False
        }
        
    def refresh_token(self):
        """Refresh the user's token if needed"""
        if not self.token or not has_token_manager or not token_manager:
            return False
            
        # Check if token needs refreshing
        token_status = self.check_token_expiry()
        if not token_status or not token_status.get('is_valid') or token_status.get('needs_refresh'):
            # Refresh token
            new_token = token_manager.refresh_token(self.token)
            if new_token:
                self.token = new_token
                return True
                
        return False

@login_manager.user_loader
def load_user(user_id):
    # First try to load user from database
    try:
        user_data = db_controller.fetch_one(
            "SELECT id, username, is_admin, role_id FROM users WHERE id = ?",
            (user_id,)
        )
        
        if user_data:
            # Check if we have a token for this user
            token = None
            if has_token_manager and token_manager:
                token = token_manager.retrieve_token(user_id)
                
                # Validate token if found
                if token:
                    payload = token_manager.validate_token(token)
                    if not payload:
                        logger.warning(f"Invalid or expired token for user ID {user_id}")
                        token = None
            
            return User(
                id=user_data['id'],
                username=user_data['username'],
                is_admin=bool(user_data['is_admin']),
                role_id=user_data['role_id'],
                token=token
            )
    except Exception as e:
        logger.error(f"Error loading user: {e}")
    
    # If we get here, try loading from a token
    if has_token_manager and token_manager:
        try:
            # Check if we have a token stored in the session
            token = session.get('user_token')
            if token:
                # Validate the token
                payload = token_manager.validate_token(token)
                if payload:
                    # Create user from token payload
                    return User(
                        id=payload.get('sub'),
                        username=payload.get('username'),
                        is_admin=payload.get('is_admin', False),
                        role_id=payload.get('role_id'),
                        token=token
                    )
        except Exception as e:
            logger.error(f"Error loading user from token: {e}")
    
    return None

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login route for the offline app with token support"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    # Check if we're handling a JSON request (AJAX login)
    is_json_request = request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == 'POST':
        try:
            # Get credentials from form or JSON
            if is_json_request:
                data = request.get_json()
                username = data.get('username')
                password = data.get('password')
                remember_me = data.get('remember_me', False)
            else:
                username = request.form.get('username')
                password = request.form.get('password')
                remember_me = request.form.get('remember_me') == 'on'
            
            logger.info(f"Login attempt for user: {username}")
            
            if not username or not password:
                logger.warning("Login attempt with missing username or password")
                message = 'Username and password are required'
                
                if is_json_request:
                    return jsonify(success=False, message=message)
                else:
                    flash(message, 'danger')
                    return render_template('login.html', offline_mode=True)
            
            # Authenticate user
            user_data = db_controller.authenticate_user(username, password)
            
            if user_data:
                try:
                    # Create a token if token manager is available
                    token = None
                    if has_token_manager and token_manager:
                        # Generate a token for the user
                        token = token_manager.generate_token(
                            user_id=user_data['id'],
                            username=user_data['username'],
                            role_id=user_data['role_id'],
                            additional_data={
                                'is_admin': user_data['is_admin'],
                                'offline_access': True,
                                'remember_me': remember_me
                            }
                        )
                        
                        # Store the token
                        token_manager.store_token(user_data['id'], token)
                        
                        # Also store in session for quick access
                        session['user_token'] = token
                        logger.info(f"Generated authentication token for user: {username}")
                    
                    # Create User object and log in
                    user = User(
                        id=user_data['id'],
                        username=user_data['username'],
                        is_admin=user_data['is_admin'],
                        role_id=user_data['role_id'],
                        token=token
                    )
                    login_user(user, remember=remember_me)
                    logger.info(f"Login successful for user: {username}")
                    
                    if is_json_request:
                        return jsonify({
                            'success': True,
                            'message': 'Login successful',
                            'token': token,  # Include token in response
                            'user': {
                                'id': user_data['id'],
                                'username': user_data['username'],
                                'is_admin': user_data['is_admin']
                            },
                            'redirectTo': url_for('dashboard')
                        })
                    else:
                        flash('Login successful!', 'success')
                        return redirect(url_for('dashboard'))
                except Exception as e:
                    logger.error(f"Error during login_user: {str(e)}")
                    message = 'Error during login process. Please try again.'
                    
                    if is_json_request:
                        return jsonify(success=False, message=message)
                    else:
                        flash(message, 'danger')
            else:
                logger.warning(f"Invalid credentials for user: {username}")
                message = 'Invalid username or password'
                
                if is_json_request:
                    return jsonify(success=False, message=message)
                else:
                    flash(message, 'danger')
        except Exception as e:
            logger.error(f"Unexpected login error: {str(e)}")
            message = 'An unexpected error occurred. Please try again.'
            
            if is_json_request:
                return jsonify(success=False, message=message)
            else:
                flash(message, 'danger')
    
    # For GET requests, always render the login template
    now = datetime.now()
    return render_template('login.html', offline_mode=True, now=now)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', offline_mode=True)

@app.route('/logout')
@login_required
def logout():
    """Logout the user and clear token if present"""
    user_id = current_user.id if current_user.is_authenticated else None
    
    # Clear token from session
    if 'user_token' in session:
        session.pop('user_token', None)
    
    # Standard Flask-Login logout
    logout_user()
    
    # Clear token if token manager is available
    if has_token_manager and token_manager and user_id:
        try:
            # Don't delete the token, but note that we've logged out
            logger.info(f"User ID {user_id} logged out, token remains for offline access")
        except Exception as e:
            logger.error(f"Error handling token during logout: {e}")
    
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/api/connection/status', methods=['GET'])
def api_connection_status():
    """API endpoint to check connection status"""
    return jsonify({
        'status': 'offline_mode',
        'offline_mode': True,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/sync/status', methods=['GET'])
@login_required
def sync_status():
    """Return sync status information (when last sync occurred, pending changes, etc.)"""
    return jsonify({
        'last_sync': session.get('last_sync_time', None),
        'pending_sync': {
            'total': 0,
            'machines': 0,
            'parts': 0,
            'maintenance': 0
        },
        'sync_available': False
    })

@app.route('/api/sync/trigger', methods=['POST'])
@login_required
def trigger_sync():
    """Trigger a manual sync operation"""
    # In the offline test app, we just simulate a sync operation
    # In a real implementation, this would communicate with the server
    time.sleep(2)  # Simulate network delay
    
    # Update last sync time
    session['last_sync_time'] = datetime.utcnow().isoformat()
    
    return jsonify({
        'status': 'success',
        'message': 'Sync completed successfully',
        'last_sync': session.get('last_sync_time')
    })

@app.route('/api/auth/validate_token', methods=['POST'])
@login_required
def validate_auth_token():
    """API endpoint to validate a token"""
    is_json_request = request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if not is_json_request:
        return jsonify(success=False, message="JSON request required"), 400
    
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify(success=False, message="Token required"), 400
    
    # Validate the token using token manager
    if has_token_manager and token_manager:
        payload = token_manager.validate_token(token)
        if payload:
            # Return token info
            standard_claims = {'sub', 'jti', 'iat', 'exp'}
            user_data = {k: v for k, v in payload.items() if k not in standard_claims}
            
            # Calculate expiry
            if 'exp' in payload:
                expiry_timestamp = payload['exp']
                expiry_date = datetime.fromtimestamp(expiry_timestamp).isoformat()
                user_data['expires_at'] = expiry_date
            
            return jsonify({
                'success': True,
                'message': 'Token is valid',
                'user': user_data
            })
        else:
            return jsonify(success=False, message="Invalid or expired token"), 401
    else:
        return jsonify(success=False, message="Token validation not available"), 501

@app.route('/api/auth/refresh_token', methods=['POST'])
def refresh_auth_token():
    """API endpoint to refresh a token"""
    is_json_request = request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if not is_json_request:
        return jsonify(success=False, message="JSON request required"), 400
    
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify(success=False, message="Token required"), 400
    
    # Refresh the token using token manager
    if has_token_manager and token_manager:
        new_token = token_manager.refresh_token(token)
        if new_token:
            # Get token info
            payload = token_manager.validate_token(new_token, auto_refresh=False)
            if payload:
                # Return token info
                standard_claims = {'sub', 'jti', 'iat', 'exp'}
                user_data = {k: v for k, v in payload.items() if k not in standard_claims}
                
                # Calculate expiry
                if 'exp' in payload:
                    expiry_timestamp = payload['exp']
                    expiry_date = datetime.fromtimestamp(expiry_timestamp).isoformat()
                    user_data['expires_at'] = expiry_date
                
                return jsonify({
                    'success': True,
                    'message': 'Token refreshed successfully',
                    'token': new_token,
                    'user': user_data
                })
            else:
                return jsonify(success=False, message="Error validating refreshed token"), 500
        else:
            return jsonify(success=False, message="Failed to refresh token"), 400
    else:
        return jsonify(success=False, message="Token refresh not available"), 501

@app.route('/api/auth/check_token_status', methods=['POST'])
def check_token_status():
    """API endpoint to check token status and get info about expiry and refresh"""
    is_json_request = request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if not is_json_request:
        return jsonify(success=False, message="JSON request required"), 400
    
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify(success=False, message="Token required"), 400
    
    # Check token status using token manager
    if has_token_manager and token_manager:
        # Use validate_token with auto_refresh=False to check status without refreshing
        payload = token_manager.validate_token(token, auto_refresh=False)
        
        if payload:
            # Calculate token status
            standard_claims = {'sub', 'jti', 'iat', 'exp'}
            user_data = {k: v for k, v in payload.items() if k not in standard_claims}
            
            # Calculate expiry info
            token_status = {}
            if 'exp' in payload:
                expiry_timestamp = payload['exp']
                expiry_date = datetime.fromtimestamp(expiry_timestamp)
                now = datetime.now()
                time_remaining = expiry_date - now
                days_remaining = time_remaining.days
                seconds_remaining = time_remaining.total_seconds()
                
                token_status = {
                    'is_valid': True,
                    'expires_at': expiry_date.isoformat(),
                    'days_remaining': days_remaining,
                    'seconds_remaining': seconds_remaining,
                    'needs_refresh': days_remaining < 5  # If less than 5 days, suggest refresh
                }
            else:
                token_status = {
                    'is_valid': True,
                    'expires_at': None,
                    'needs_refresh': False
                }
            
            # Add user data
            token_status['user'] = user_data
            
            return jsonify({
                'success': True,
                'message': 'Token is valid',
                'token_status': token_status
            })
        else:
            return jsonify({
                'success': False, 
                'message': "Invalid or expired token",
                'token_status': {
                    'is_valid': False,
                    'needs_refresh': False
                }
            }), 401
    else:
        return jsonify(success=False, message="Token status check not available"), 501

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Simple mock forgot password route for the offline app"""
    if request.method == 'POST':
        email = request.form.get('email')
        flash('Password reset functionality is not available in offline mode.', 'warning')
        return redirect(url_for('login'))
    return render_template('forgot_password.html', offline_mode=True)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Simple mock reset password route for the offline app"""
    flash('Password reset functionality is not available in offline mode.', 'warning')
    return redirect(url_for('login'))

# Additional routes to handle possible navigation from templates
@app.route('/profile')
@login_required
def profile():
    """Simple mock profile route for the offline app"""
    return render_template('profile.html', offline_mode=True)

@app.route('/admin')
@login_required
def admin():
    """Simple mock admin route for the offline app"""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('admin.html', offline_mode=True)

# TEST LOGIN BYPASS ROUTE (for automated tests/demo only)
if os.environ.get('TEST_MODE', '').lower() == 'true':
    @app.route('/test-login-bypass')
    def test_login_bypass():
        """Bypass login and authenticate as admin for testing/demo purposes only."""
        try:
            logger.info(f"[TEST_LOGIN_BYPASS] Using DB file: {db_controller.db_path}")
            user_data = db_controller.fetch_one("SELECT id, username, is_admin, role_id FROM users WHERE username = 'admin'")
            logger.info(f"[TEST_LOGIN_BYPASS] user_data: {user_data}")
            if not user_data:
                logger.error("[TEST_LOGIN_BYPASS] Admin user not found!")
                return "Admin user not found", 404
            user = User(
                id=user_data['id'],
                username=user_data['username'],
                is_admin=user_data['is_admin'],
                role_id=user_data['role_id']
            )
            login_user(user)
            logger.info(f"[TEST_LOGIN_BYPASS] Successfully logged in as admin (user_id={user.id})")
            return redirect(url_for('dashboard'))
        except Exception as e:
            logger.error(f"Test login bypass failed: {e}")
            return f"Test login bypass failed: {e}", 500

# Context processor for templates
@app.context_processor
def inject_offline_mode():
    return {'offline_mode': True}

def initialize_database():
    """Initialize the database with default data if needed"""
    # Get the database filename from the environment or use default
    db_filename = os.environ.get('DB_FILE', 'maintenance.db')
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', db_filename)
    
    logger.info(f"Initializing database: {db_path}")
    
    # Check if we should recreate the database regardless of its state
    force_recreate = os.environ.get('RECREATE_DB', '').lower() == 'true'
    if force_recreate and os.path.exists(db_path):
        try:
            logger.info(f"Force recreating database due to RECREATE_DB environment variable")
            os.remove(db_path)
            logger.info(f"Removed database file: {db_path}")
        except Exception as e:
            logger.error(f"Error removing database file: {e}")
    
    # Check if database exists and is valid
    db_exists = os.path.exists(db_path)
    db_valid = False
    
    if db_exists:
        # Try to connect and check if it's a valid database
        try:
            # Test if we can query the database
            db_controller.get_connection().execute("SELECT 1")
            logger.info(f"Database exists and is valid: {db_path}")
            
            # Also check if users table exists and has the admin user
            try:
                if db_controller.table_exists('users'):
                    admin_user = db_controller.fetch_one("SELECT id FROM users WHERE username = 'admin'")
                    if admin_user:
                        logger.info("Admin user exists in the database")
                        db_valid = True
                    else:
                        logger.warning("Users table exists but admin user is missing")
                else:
                    logger.warning("Users table does not exist in the database")
            except Exception as e:
                logger.error(f"Error checking for admin user: {e}")
        except Exception as e:
            # If there's an error, remove the file and recreate it
            logger.warning(f"Database file exists but is not valid: {e}. Removing and recreating: {db_path}")
            try:
                os.remove(db_path)
                logger.info(f"Removed invalid database file: {db_path}")
                db_exists = False
            except Exception as e:
                logger.error(f"Error removing database file: {e}")
    
    # If database is valid, we're done
    if db_exists and db_valid:
        return
    
    # Now initialize tables if they don't exist
    try:
        # Create tables if they don't exist
        if not db_controller.table_exists('roles'):
            logger.info("Creating roles table")
            db_controller.execute_query('''
            CREATE TABLE roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                permissions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create default roles
            admin_role_id = db_controller.execute_query(
                "INSERT INTO roles (name, description, permissions) VALUES (?, ?, ?)",
                ('admin', 'Administrator', 'admin.full')
            ).lastrowid
            
            tech_role_id = db_controller.execute_query(
                "INSERT INTO roles (name, description, permissions) VALUES (?, ?, ?)",
                ('technician', 'Maintenance Technician', 'tech.full')
            ).lastrowid
            
        if not db_controller.table_exists('users'):
            logger.info("Creating users table")
            db_controller.execute_query('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                username_hash TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                email_hash TEXT NOT NULL UNIQUE,
                full_name TEXT,
                password_hash TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT 0,
                role_id INTEGER,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reset_token TEXT,
                reset_token_expiration TIMESTAMP,
                notification_preferences TEXT,
                FOREIGN KEY (role_id) REFERENCES roles (id)
            )
            ''')
            
            # Get admin role if exists
            role_result = db_controller.fetch_one("SELECT id FROM roles WHERE name = 'admin'")
            admin_role_id = role_result['id'] if role_result else None
            
            if admin_role_id is None:
                logger.warning("Admin role not found, creating it")
                admin_role_id = db_controller.execute_query(
                    "INSERT INTO roles (name, description, permissions) VALUES (?, ?, ?)",
                    ('admin', 'Administrator', 'admin.full')
                ).lastrowid
            
            # Create admin user
            admin_id = db_controller.create_user(
                username='admin',
                email='admin@example.com',
                full_name='Administrator',
                password='admin',
                is_admin=True,
                role_id=admin_role_id
            )
            
            logger.info("Database initialized with default admin user (username: admin, password: admin)")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

if __name__ == '__main__':
    # Initialize database
    initialize_database()
    
    # Start the app
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV', '') == 'development'
    test_mode = os.environ.get('TEST_MODE', '').lower() == 'true'
    
    if test_mode:
        print(f"Running in TEST mode on port {port}")
        
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
