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
from sqlalchemy import text
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

# Add default user if none exist - ensures at least one admin exists after fresh deployments
def add_default_admin_if_needed():
    """Add a default admin user if no users exist in the database"""
    try:
        print("[APP] Checking for default admin user...")
        from werkzeug.security import generate_password_hash
        
        # Check if User model is defined and users table exists
        if 'User' in globals() and db.engine.has_table('user'):
            # Check if any users exist
            user_count = User.query.count()
            
            if user_count == 0:
                print("[APP] No users found in database. Creating default admin user.")
                
                # Create default admin role if needed
                admin_role = Role.query.filter_by(name="Administrator").first()
                if not admin_role:
                    admin_role = Role(
                        name="Administrator",
                        description="Full system access",
                        permissions=",".join(Permissions.get_all_permissions())
                    )
                    db.session.add(admin_role)
                    db.session.commit()
                
                # Create default admin user
                default_password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123')  # Can be set in env vars
                admin_user = User(
                    username="admin",
                    password_hash=generate_password_hash(default_password),
                    email="admin@example.com",
                    full_name="System Administrator",
                    is_admin=True,
                    role_id=admin_role.id
                )
                
                db.session.add(admin_user)
                db.session.commit()
                print("[APP] Created default admin user 'admin' with provided or default password.")
                print("[APP] IMPORTANT: Please change this password immediately after first login.")
                
                return admin_user
            else:
                print(f"[APP] Found {user_count} existing users in database.")
                return None
        else:
            print("[APP] User model not defined or users table doesn't exist yet.")
            return None
    except Exception as e:
        print(f"[APP] Error checking/creating default admin: {str(e)}")
        return None

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

if __name__ == '__main__':
    print("[APP] Starting Flask development server...")
    app.run(debug=True)