import os
import sys
import sqlite3
import secrets
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
from flask_mail import Mail, Message
from dotenv import load_dotenv
from sqlalchemy import text, inspect
from sqlalchemy.orm.attributes import flag_modified

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
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maintenance.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        return app

# Initialize Flask app with better error handling
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')
app.config['APPLICATION_ROOT'] = os.environ.get('APPLICATION_ROOT', '/')
app.config['PREFERRED_URL_SCHEME'] = os.environ.get('PREFERRED_URL_SCHEME', 'https')

# Ensure URLs work with and without trailing slashes
app.url_map.strict_slashes = False

# Initialize Flask-Login - CRITICAL: This must be done before using current_user
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

# Add error handlers with fallbacks
@app.errorhandler(404)
def page_not_found(e):
    try:
        return render_template('errors/404.html'), 404
    except:
        # Fallback to simple HTML response if template is missing
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>Page Not Found</title></head>
        <body style="font-family:Arial; text-align:center; padding:50px;">
            <h1 style="color:#FE7900;">Page Not Found</h1>
            <p>The requested page was not found. Please check the URL or go back to the <a href="/" style="color:#FE7900;">home page</a>.</p>
        </body>
        </html>
        ''', 404

@app.errorhandler(500)
def server_error(e):
    try:
        return render_template('errors/500.html'), 500
    except:
        # Fallback to simple HTML response if template is missing
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>Server Error</title></head>
        <body style="font-family:Arial; text-align:center; padding:50px;">
            <h1 style="color:#FE7900;">Server Error</h1>
            <p>Sorry, something went wrong on our end. Please try again later or go back to the <a href="/" style="color:#FE7900;">home page</a>.</p>
        </body>
        </html>
        ''', 500

# Root route handler
@app.route('/')
def index():
    """Root route that redirects to the dashboard or login page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

# Add debug route to check application
@app.route('/debug-info')
def debug_info():
    """Debug route to check application status"""
    output = {
        "status": "running",
        "time": datetime.now().isoformat(),
        "routes": [str(rule) for rule in app.url_map.iter_rules()],
        "flask_login_initialized": hasattr(app, 'login_manager'),
        "current_user": str(current_user) if 'current_user' in globals() else "Not available",
        "is_authenticated": current_user.is_authenticated if 'current_user' in globals() else False
    }
    return jsonify(output)

# Add health check route for diagnostics
@app.route('/health')
def health_check():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "environment": os.environ.get('FLASK_ENV', 'production'),
        "render": os.environ.get('RENDER', 'false')
    })

# Configure the database
try:
    print("[APP] Configuring database...")
    configure_database(app)
except Exception as e:
    print(f"[APP] Error configuring database: {str(e)}")
    # Set a fallback configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maintenance.db'

# Initialize database
print("[APP] Initializing SQLAlchemy...")
db = SQLAlchemy(app)

# Create admin function
def create_default_admin():
    """Create a default admin account if no users exist"""
    try:
        print("[APP] Checking for existing users...")
        
        # Check if users table exists
        inspector = inspect(db.engine)
        if 'user' not in inspector.get_table_names():
            print("[APP] Users table doesn't exist yet, creating all tables...")
            db.create_all()
        
        # Check for existing users
        user_count = User.query.count()
        
        if user_count == 0:
            print("[APP] No users found. Creating default admin user...")
            
            # Check if Roles table exists and has Administrator role
            admin_role = None
            if 'role' in inspector.get_table_names():
                admin_role = Role.query.filter_by(name="Administrator").first()
                
            # Create admin role if needed
            if not admin_role:
                print("[APP] Creating Administrator role...")
                
                # Handle case where get_all_permissions may not exist
                try:
                    permissions = Permissions.get_all_permissions() if hasattr(Permissions, 'get_all_permissions') else "admin"
                    permissions_string = ",".join(permissions)
                except:
                    permissions_string = "admin.full"
                
                admin_role = Role(
                    name="Administrator",
                    description="Full system access",
                    permissions=permissions_string
                )
                db.session.add(admin_role)
                db.session.commit()
            
            # Create admin user with username "admin" and password "admin"
            admin_user = User(
                username="admin",
                email="admin@example.com",
                full_name="System Administrator", 
                is_admin=True,
                role_id=admin_role.id if admin_role else None
            )
            
            # Set password - handle different implementations
            if hasattr(admin_user, 'set_password'):
                admin_user.set_password("admin")
            else:
                admin_user.password_hash = generate_password_hash("admin")
            
            db.session.add(admin_user)
            db.session.commit()
            
            print("[APP] Created default admin user 'admin' with password 'admin'")
            print("[APP] WARNING: This is intended for testing only.")
            print("[APP] IMPORTANT: Change this password when deploying to production!")
            
            return True
        else:
            print(f"[APP] {user_count} users already exist, not creating default admin")
            return False
            
    except Exception as e:
        print(f"[APP] Error creating default admin: {str(e)}")
        return False

# Add default user if none exist - ensures at least one admin exists after fresh deployments
def add_default_admin_if_needed():
    """Add a default admin user if no users exist in the database"""
    try:
        print("[APP] Checking for default admin user...")
        
        # First make sure tables exist
        with app.app_context():
            inspector = inspect(db.engine)
            if 'user' not in inspector.get_table_names():
                print("[APP] User table doesn't exist yet. Will create tables first.")
                db.create_all()
                print("[APP] Tables created.")
            
            # Check if any users exist
            user_count = User.query.count()
            
            if user_count == 0:
                print("[APP] No users found in database. Creating default admin user.")
                
                # Create default admin role if needed
                admin_role = Role.query.filter_by(name="Administrator").first()
                if not admin_role:
                    print("[APP] Creating Administrator role with full permissions.")
                    admin_role = Role(
                        name="Administrator",
                        description="Full system access",
                        permissions="admin.full"  # Full administrator access
                    )
                    db.session.add(admin_role)
                    db.session.commit()
                
                # Create default admin user with simple password for testing
                admin_user = User(
                    username="admin",
                    email="admin@example.com",
                    full_name="System Administrator",
                    is_admin=True,
                    role_id=admin_role.id if admin_role else None
                )
                admin_user.set_password("admin")  # Simple password for testing
                
                db.session.add(admin_user)
                db.session.commit()
                
                print("[APP] Created default admin user 'admin' with password 'admin'")
                print("[APP] WARNING: This is intended for testing only.")
                print("[APP] IMPORTANT: Please change this password immediately after login.")
                
                return admin_user
            else:
                print(f"[APP] Found {user_count} existing users in database - no default admin needed.")
                return None
    except Exception as e:
        print(f"[APP] Error creating default admin: {str(e)}")
        return None

# Call this function when app initializes
with app.app_context():
    try:
        create_default_admin()
    except Exception as e:
        print(f"[APP] Error during startup initialization: {str(e)}")

# AFTER all models are defined, THEN create tables
if os.environ.get('RENDER', False):
    print("[APP] Running on Render, creating database tables...")
    with app.app_context():
        try:
            db.create_all()
            print("[APP] Database tables created successfully.")
            # Add default admin user if needed
            add_default_admin_if_needed()
        except Exception as e:
            print(f"[APP] Error creating database tables: {str(e)}", file=sys.stderr)

# Make sure we can run the app directly for both development and production
if __name__ == '__main__':
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Add default admin account if no users exist
        add_default_admin_if_needed()
    
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 10000))
    print(f"[APP] Starting Flask server on port {port}")
    
    # Use host 0.0.0.0 to bind to all interfaces
    app.run(host='0.0.0.0', port=port)