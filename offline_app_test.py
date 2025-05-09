#!/usr/bin/env python3
"""
Test version of the Offline AMRS Maintenance Tracker app
Used for automated testing of offline functionality
"""
import os
import sys
import logging
from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
from db_controller import DatabaseController

# Configure logging
logging.basicConfig(level=logging.INFO, format='[TEST_OFFLINE_APP] %(levelname)s - %(message)s')
logger = logging.getLogger("test_offline_app")

# Get test database path from environment
test_db_path = os.environ.get('TEST_DATABASE')
if test_db_path:
    # Create a database controller pointing to the test database
    db_controller = DatabaseController(db_path=test_db_path, use_encryption=False)
    logger.info(f"Using test database at {test_db_path}")
else:
    # Fall back to default database
    db_controller = DatabaseController(use_encryption=False)
    logger.info("Using default database, TEST_DATABASE environment variable not set")

# Create Flask app
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
            static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))

# Force offline mode
os.environ['OFFLINE_MODE'] = 'true'

# Configure the app for testing
app.config['SECRET_KEY'] = 'test-secret-key'
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, is_admin=False, role_id=None):
        self.id = id
        self.username = username
        self.is_admin = is_admin
        self.role_id = role_id
        self.last_login = datetime.utcnow()

@login_manager.user_loader
def load_user(user_id):
    # Query the user from the database
    try:
        user_data = db_controller.fetch_one(
            "SELECT id, username, is_admin, role_id FROM users WHERE id = ?",
            (user_id,)
        )
        
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                is_admin=bool(user_data['is_admin']),
                role_id=user_data['role_id']
            )
    except Exception as e:
        logger.error(f"Error loading user: {e}")
    
    return None

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Authenticate user
        user_data = db_controller.authenticate_user(username, password)
        
        if user_data:
            # Create User object and log in
            user = User(
                id=user_data['id'],
                username=user_data['username'],
                is_admin=user_data['is_admin'],
                role_id=user_data['role_id']
            )
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html', offline_mode=True)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', offline_mode=True)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

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

# API routes for testing
@app.route('/api/connection/status', methods=['GET'])
def api_connection_status():
    """API endpoint to check connection status"""
    return jsonify({
        'status': 'offline_mode',
        'offline_mode': True,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/sync/status', methods=['GET'])
def api_sync_status():
    """API endpoint to check sync status"""
    last_sync = db_controller.get_last_sync_time()
    pending_sync = db_controller.get_pending_sync_count()
    
    return jsonify({
        'last_sync': last_sync,
        'pending_sync': pending_sync,
        'offline_mode': True
    })

@app.route('/api/sync/trigger', methods=['POST'])
@login_required
def api_trigger_sync():
    """API endpoint to trigger data synchronization"""
    # For this simplified app, we just update the last sync time
    success = db_controller.update_last_sync_time()
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Sync completed successfully',
            'offline_mode': True
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Sync failed',
            'offline_mode': True
        })

# Special testing API endpoints
@app.route('/api/test/initialize_db', methods=['POST'])
def api_test_initialize_db():
    """API endpoint to initialize the test database"""
    try:
        initialize_database()
        return jsonify({
            'success': True,
            'message': 'Test database initialized successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error initializing test database: {str(e)}'
        })

@app.route('/api/test/create_record', methods=['POST'])
def api_test_create_record():
    """API endpoint to create a test record"""
    try:
        data = request.json or {}
        site_id = data.get('site_id', 1)
        machine_id = data.get('machine_id', 1)
        notes = data.get('notes', 'Test record')
        
        client_id = f"test-{datetime.now().timestamp()}"
        
        # Make sure the maintenance_records table exists
        if not db_controller.table_exists('maintenance_records'):
            db_controller.execute_query('''
            CREATE TABLE maintenance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                machine_id INTEGER,
                maintenance_date TEXT,
                technician_id INTEGER,
                notes TEXT,
                is_synced INTEGER DEFAULT 0,
                client_id TEXT,
                server_id INTEGER,
                sync_status TEXT DEFAULT 'pending',
                last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
        
        # Insert the record
        cursor = db_controller.execute_query(
            "INSERT INTO maintenance_records (site_id, machine_id, maintenance_date, technician_id, notes, is_synced, client_id) " +
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (site_id, machine_id, datetime.now().isoformat(), 1, notes, 0, client_id)
        )
        
        return jsonify({
            'success': True,
            'record_id': cursor.lastrowid,
            'client_id': client_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error creating test record: {str(e)}'
        })

# Context processor for templates
@app.context_processor
def inject_offline_mode():
    return {'offline_mode': True}

def initialize_database():
    """Initialize the database with default data if needed"""
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
            
        # Initialize maintenance records table if it doesn't exist
        if not db_controller.table_exists('maintenance_records'):
            logger.info("Creating maintenance_records table")
            db_controller.execute_query('''
            CREATE TABLE maintenance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                machine_id INTEGER,
                maintenance_date TEXT,
                technician_id INTEGER,
                notes TEXT,
                is_synced INTEGER DEFAULT 0,
                client_id TEXT,
                server_id INTEGER,
                sync_status TEXT DEFAULT 'pending',
                last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

if __name__ == '__main__':
    # Initialize database
    initialize_database()
    
    # Start the app
    port = int(os.environ.get('PORT', 5001))
    app.run(host='127.0.0.1', port=port, debug=True)
