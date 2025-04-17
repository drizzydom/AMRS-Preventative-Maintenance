# Standard library imports
import os
import sys
import random
import string
import logging
import signal
import argparse
from datetime import datetime, timedelta
from functools import wraps

# Third-party imports
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_mail import Mail, Message
import bleach
import jwt  # Added for password reset tokens
from sqlalchemy import or_, text  # Added text for SQL execution
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv  # Add the missing import for load_dotenv
import secrets  # Add import for secrets used later in the code
from sqlalchemy import inspect  # Add import for inspect
import psycopg2  # Add PostgreSQL driver

# Local imports
from models import db, User, Role, Site, Machine, Part, MaintenanceRecord

# Define PostgreSQL database URI
POSTGRESQL_DATABASE_URI = os.environ.get(
    'DATABASE_URL', 
    'postgresql://maintenance_tracker_data_user:mbVv4EmuXc0co5A0KcHe57SPhW7Kd0gi@dpg-cvv7vebe5dus73ec3ksg-a/maintenance_tracker_data'
)

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

# Call this function before your database setup
storage_ok = check_persistent_storage()

# Initialize Flask app
app = Flask(__name__, instance_relative_config=True)

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Get the directory of this file
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Define dotenv_path before using it
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)

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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')
app.config['APPLICATION_ROOT'] = os.environ.get('APPLICATION_ROOT', '/')
app.config['PREFERRED_URL_SCHEME'] = os.environ.get('PREFERRED_URL_SCHEME', 'https')

# Ensure URLs work with and without trailing slashes
app.url_map.strict_slashes = False

# Configure the database
try:
    print("[APP] Configuring database...")
    configure_database(app)
except Exception as e:
    print(f"[APP] Error configuring database: {str(e)}")
    # Set a fallback configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = POSTGRESQL_DATABASE_URI

# Initialize database
print("[APP] Initializing SQLAlchemy...")
db.init_app(app)

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
    return User.query.get(int(user_id)) if user_id else None

# Initialize database connection for API endpoints
@app.before_first_request
def initialize_db_connection():
    """Initialize database connection."""
    try:
        # Test database connection
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("[APP] Database connection established successfully")
    except Exception as e:
        print(f"[APP] Database connection error: {e}")

@app.before_first_requestr initialize_db_connection
def setup_application():chema():
    """Setup everything needed before handling the first request."""e database schema matches the models by adding missing columns."""
    initialize_db_connection()
    ensure_db_schema()e schema...")

# Add root route handlerspect the database
@app.route('/')            inspector = inspect(db.engine)
def index():
    """Homepage route that redirects to dashboard if logged in or shows login page."""heck User table for missing columns
    if current_user.is_authenticated:ting_columns = {column['name'] for column in inspector.get_columns('users')}
        return redirect(url_for('dashboard'))
    return render_template('login.html')        'last_login': 'TIMESTAMP',

@app.route('/dashboard')en_expiration': 'TIMESTAMP'
@login_required
def dashboard():
    """Main dashboard view after login."""            # Add any missing columns
    try:
        return render_template('dashboard.html')    for column_name, column_type in required_columns.items():
    except Exception as e:n_name not in existing_columns:
        app.logger.error(f"Error rendering dashboard: {e}") Adding missing column {column_name} to users table")
        return render_template('errors/500.html'), 500LTER TABLE users ADD COLUMN IF NOT EXISTS {column_name} {column_type}"))
                conn.commit()
@app.route('/login', methods=['GET', 'POST'])
def login():completed")
    """Handle user login."""
    if current_user.is_authenticated:print(f"[APP] Error checking database schema: {e}")
        return redirect(url_for('dashboard'))
        ot route handler
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')d if logged in or shows login page."""
        
        user = User.query.filter_by(username=username).first()n redirect(url_for('dashboard'))
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')@login_required
            return redirect(next_page or url_for('dashboard'))
        else:hboard view after login."""
            flash('Invalid username or password', 'danger')
    e('dashboard.html')
    return render_template('login.html')ion as e:
shboard: {e}")
@app.route('/logout')s/500.html'), 500
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():name')
    """Handle password reset request."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))ser.query.filter_by(username=username).first()
        
    if request.method == 'POST':rd_hash, password):
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()next_page = request.args.get('next')
         or url_for('dashboard'))
        if user:
            # Generate a password reset token 'danger')
            reset_token = secrets.token_urlsafe(32)
            expires = datetime.now() + timedelta(hours=24)ender_template('login.html')
            
            # Store token in database
            user.reset_token = reset_token
            user.reset_token_expiration = expires
            db.session.commit()e user logout."""
            
            # In a production app, you would send an email with the reset link
            # For now, just flash a message with the token (for demonstration)
            reset_url = url_for('reset_password', token=reset_token, _external=True)
            flash(f'Password reset link: {reset_url}', 'info')
            ():
        # Always show this message to prevent user enumerationdle password reset request."""
        flash('If an account with that email exists, a password reset link has been sent.', 'info')rent_user.is_authenticated:
        return redirect(url_for('login'))oard'))
        
    return render_template('forgot_password.html') if os.path.exists(os.path.join('templates', 'forgot_password.html')) else '''est.method == 'POST':
    <!DOCTYPE html>ail = request.form.get('email')
    <html>email=email).first()
    <head>
        <title>Forgot Password</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">t token
    </head>
    <body>a(hours=24)
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Reset Password</div>
                        <div class="card-body">
                            <form method="post">you would send an email with the reset link
                                <div class="mb-3">th the token (for demonstration)
                                    <label for="email" class="form-label">Email</label>
                                    <input type="email" class="form-control" id="email" name="email" required> link: {reset_url}', 'info')
                                </div>
                                <button type="submit" class="btn btn-primary">Send Reset Link</button> message to prevent user enumeration
                            </form>ccount with that email exists, a password reset link has been sent.', 'info')
                            <div class="mt-3">irect(url_for('login'))
                                <a href="/login" class="text-decoration-none">Back to Login</a>
                            </div>render_template('forgot_password.html') if os.path.exists(os.path.join('templates', 'forgot_password.html')) else '''
                        </div>PE html>
                    </div>ml>
                </div>    <head>
            </div>
        </div>//cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    </body>
    </html>
    '''
    <div class="row justify-content-center">
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):                <div class="card">
    """Handle password reset with token."""er">Reset Password</div>
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    user = User.query.filter_by(reset_token=token).first()                            <label for="email" class="form-label">Email</label>
        <input type="email" class="form-control" id="email" name="email" required>
    # Check if token is valid and not expired
    if not user or (user.reset_token_expiration and user.reset_token_expiration < datetime.now()):n btn-primary">Send Reset Link</button>
        flash('The password reset link is invalid or has expired.', 'danger')                    </form>
        return redirect(url_for('forgot_password'))>
        e">Back to Login</a>
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')       </div>
        
        if not password or len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match.', 'danger')
        else:
            # Update password and clear reset token
            user.password_hash = generate_password_hash(password)=['GET', 'POST'])
            user.reset_token = Nonessword(token):
            user.reset_token_expiration = None
            db.session.commit().is_authenticated:
            turn redirect(url_for('dashboard'))
            flash('Your password has been updated. Please log in.', 'success')
            return redirect(url_for('login'))_token=token).first()
            
    return render_template('reset_password.html', token=token) if os.path.exists(os.path.join('templates', 'reset_password.html')) else ''' if token is valid and not expired
    <!DOCTYPE html> user or (user.reset_token_expiration and user.reset_token_expiration < datetime.now()):
    <html>nk is invalid or has expired.', 'danger')
    <head>
        <title>Reset Password</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>nfirm_password')
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Reset Password</div>tch.', 'danger')
                        <div class="card-body">
                            <form method="post">
                                <div class="mb-3">
                                    <label for="password" class="form-label">New Password</label>
                                    <input type="password" class="form-control" id="password" name="password" required>
                                </div>
                                <div class="mb-3">
                                    <label for="confirm_password" class="form-label">Confirm Password</label>ssword has been updated. Please log in.', 'success')
                                    <input type="password" class="form-control" id="confirm_password" name="confirm_password" required>irect(url_for('login'))
                                </div>
                                <button type="submit" class="btn btn-primary">Reset Password</button>der_template('reset_password.html', token=token) if os.path.exists(os.path.join('templates', 'reset_password.html')) else '''
                            </form>PE html>
                        </div>
                    </div>ad>
                </div>        <title>Reset Password</title>
            </div>m/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        </div>
    </body>
    </html>
    '''s="row justify-content-center">

# Add a debug route to see all available routes            <div class="card">
@app.route('/debug-info')         <div class="card-header">Reset Password</div>
def debug_info():body">
    """Display debug information including all available routes."""     <form method="post">
    if not app.debug:lass="mb-3">
        return "Debug mode is disabled", 403="password" class="form-label">New Password</label>
              <input type="password" class="form-control" id="password" name="password" required>
    routes = []                      </div>
    for rule in app.url_map.iter_rules():                        <div class="mb-3">
        routes.append({
            'endpoint': rule.endpoint,                                    <input type="password" class="form-control" id="confirm_password" name="confirm_password" required>
            'methods': ','.join(rule.methods),
            'route': str(rule)utton type="submit" class="btn btn-primary">Reset Password</button>
        })
                        </div>
    return render_template('debug_info.html', routes=routes) if os.path.exists(os.path.join('templates', 'debug_info.html')) else jsonify(routes=routes)

# Add function to create default admin (referenced in __main__ block)
def add_default_admin_if_needed():
    """Add a default admin user if no users exist in the database."""
    try:
        user_count = User.query.count()
        if user_count == 0:
            print("[APP] No users found, creating default admin user") route to see all available routes
            admin = User(
                username='admin',
                email='admin@example.com',ble routes."""
                password_hash=generate_password_hash('admin'),
                role='admin'
            )        
            db.session.add(admin)
            db.session.commit()
            print("[APP] Default admin user created")end({
    except Exception as e:
        print(f"[APP] Error creating default admin: {e}")    'methods': ','.join(rule.methods),

# API endpoint for synchronization (to be used by desktop client)
@app.route('/api/sync/status', methods=['GET'])
def sync_status():outes) if os.path.exists(os.path.join('templates', 'debug_info.html')) else jsonify(routes=routes)
    """Get synchronization status information."""
    try:tion to create default admin (referenced in __main__ block)
        # Basic information about the server stateeeded():
        return jsonify({""
            'status': 'online',    try:
            'server_time': datetime.now().isoformat(),
            'version': '1.0.0'_count == 0:
        })t("[APP] No users found, creating default admin user")
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500        username='admin',
n@example.com',
@app.route('/api/sync/data', methods=['POST'])te_password_hash('admin'),
@login_required        role='admin'
def sync_data():
    """Handle data synchronization requests from desktop clients."""
    try:
        data = request.json
        sync_type = data.get('type')xception as e:
        ing default admin: {e}")
        if sync_type == 'push':
            # Handle data being pushed from client to serverop client)
            # Process items from the client
            return jsonify({'status': 'success', 'message': 'Data received successfully'})
            ynchronization status information."""
        elif sync_type == 'pull':
            # Handle client requesting data from serverabout the server state
            # Return requested data based on parameters
            entity_type = data.get('entity_type')line',
            timestamp = data.get('last_sync')).isoformat(),
            
            # This is simplified - in a real implementation you would fetch actual data
            return jsonify({eption as e:
                'status': 'success',rn jsonify({'status': 'error', 'message': str(e)}), 500
                'data': {
                    'type': entity_type,
                    'items': []  # Actual data would go herered
                }
            })"
                try:
        else:
            return jsonify({'status': 'error', 'message': 'Invalid sync type'}), 400 data.get('type')
            
    except Exception as e:if sync_type == 'push':
        return jsonify({'status': 'error', 'message': str(e)}), 500rver
nt
@app.route('/health-check')cess', 'message': 'Data received successfully'})
def health_check():
    """Basic health check endpoint."""'pull':
    try:er
        # Update to use connection-based execute pattern
        with db.engine.connect() as conn:            entity_type = data.get('entity_type')
            conn.execute(text("SELECT 1"))ast_sync')
        return jsonify({'status': 'ok'}), 200
    except Exception as e:simplified - in a real implementation you would fetch actual data
        app.logger.error(f"Health check failed: {e}")    return jsonify({
        return jsonify({'status': 'error', 'message': str(e)}), 500
     'data': {
# Add error handlers with fallbacks
@app.errorhandler(404)  'items': []  # Actual data would go here
def page_not_found(e):
    try:
        return render_template('errors/404.html'), 404
    except:
        # Fallback to simple HTML response if template is missing'Invalid sync type'}), 400
        return '''
        <!DOCTYPE html>ption as e:
        <html>jsonify({'status': 'error', 'message': str(e)}), 500
        <head><title>Page Not Found</title></head>
        <body style="font-family:Arial; text-align:center; padding:50px;">@app.route('/health-check')
            <h1 style="color:#FE7900;">Page Not Found</h1>
            <p>The requested page was not found. Please check the URL or go back to the <a href="/" style="color:#FE7900;">home page</a>.</p>check endpoint."""
        </body>
        </html>rn
        ''', 404h db.engine.connect() as conn:

@app.errorhandler(500)nify({'status': 'ok'}), 200
def server_error(e): e:
    try:gger.error(f"Health check failed: {e}")
        return render_template('errors/500.html'), 500age': str(e)}), 500
    except:
        # Fallback to simple HTML response if template is missing
        return '''
        <!DOCTYPE html>und(e):
        <html>
        <head><title>Server Error</title></head>ender_template('errors/404.html'), 404
        <body style="font-family:Arial; text-align:center; padding:50px;">    except:
            <h1 style="color:#FE7900;">Server Error</h1>
            <p>Sorry, something went wrong on our end. Please try again later or go back to the <a href="/" style="color:#FE7900;">home page</a>.</p>
        </body>
        </html>
        ''', 500

# Make sure we can run the app directly for both development and productionFE7900;">Page Not Found</h1>
if __name__ == '__main__':        <p>The requested page was not found. Please check the URL or go back to the <a href="/" style="color:#FE7900;">home page</a>.</p>
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='AMRS Maintenance Tracker Server')
    parser.add_argument('--port', type=int, default=10000, help='Port to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    args = parser.parse_args()
    
    with app.app_context():try:
        # Create tables if they don't exist
        db.create_all()
        
        # Add default admin account if no users exist    return '''
        add_default_admin_if_needed()
        <html>
    # Get port from command line argument, environment variable, or default
    port = args.port or int(os.environ.get('PORT', 10000))center; padding:50px;">






    app.run(host='0.0.0.0', port=port, debug=debug)    # Use host 0.0.0.0 to bind to all interfaces        print(f"[APP] Starting Flask server on port {port}")        debug = args.debug or os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'            <h1 style="color:#FE7900;">Server Error</h1>
            <p>Sorry, something went wrong on our end. Please try again later or go back to the <a href="/" style="color:#FE7900;">home page</a>.</p>
        </body>
        </html>
        ''', 500

# Make sure we can run the app directly for both development and production
if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='AMRS Maintenance Tracker Server')
    parser.add_argument('--port', type=int, default=10000, help='Port to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    args = parser.parse_args()
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Ensure all columns exist in the tables
        ensure_db_schema()
        
        # Add default admin account if no users exist
        add_default_admin_if_needed()
    
    # Get port from command line argument, environment variable, or default
    port = args.port or int(os.environ.get('PORT', 10000))
    debug = args.debug or os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    print(f"[APP] Starting Flask server on port {port}")
    
    # Use host 0.0.0.0 to bind to all interfaces
    app.run(host='0.0.0.0', port=port, debug=debug)