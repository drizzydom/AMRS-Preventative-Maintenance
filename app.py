# Standard library imports
import os
import sys
import random
import string
import logging
import signal
import argparse
import calendar
from datetime import datetime, timedelta, date
from functools import wraps
import traceback
from io import BytesIO
from urllib.parse import urlencode

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
import json

# Local imports
from models import db, User, Role, Site, Machine, Part, MaintenanceRecord, AuditTask, AuditTaskCompletion, encrypt_value, hash_value
from auto_migrate import run_auto_migration

# Patch is_admin property to User class immediately after import
@property
def is_admin(self):
    """Add is_admin property to User class for template compatibility"""
    return is_admin_user(self)
User.is_admin = is_admin

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
            days_until = (part.next_maintenance - current_date).days
            
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

# Call this function before your database setup
storage_ok = check_persistent_storage()

# Initialize Flask app
app = Flask(__name__, instance_relative_config=True)

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
    return db.session.get(User, int(user_id)) if user_id else None

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
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        app.logger.error(f"Database connection error: {e}")
        return False

# Whitelist allowed table and column names for schema changes
ALLOWED_TABLES = {'users', 'roles', 'sites', 'machines', 'parts', 'maintenance_records', 'audit_tasks', 'audit_task_completions'}
ALLOWED_COLUMNS = {
    'users': {'last_login', 'reset_token', 'reset_token_expiration', 'created_at', 'updated_at'},
    'roles': {'created_at', 'updated_at'},
    'sites': {'created_at', 'updated_at'},
    'machines': {'created_at', 'updated_at'},
    'parts': {'created_at', 'updated_at'},
    'maintenance_records': {'created_at', 'updated_at', 'client_id', 'machine_id', 'maintenance_type', 'description', 'performed_by', 'status', 'notes'},
    'audit_tasks': {'created_at', 'updated_at', 'interval', 'custom_interval_days'},
    'audit_task_completions': {'created_at', 'updated_at'}
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

# --- Default admin creation logic ---
def add_default_admin_if_needed():
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
    
    This function:
    1. Finds tasks without colors and assigns them new ones
    2. Detects and fixes tasks with duplicate colors within the same site
    3. Ensures each site has its own independent color wheel (sites can reuse colors)
    4. Handles all task types that are visualized in the UI
    """
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
                    # No color assigned yet
                    tasks_to_update.append(task)
                elif task.color in used_colors:
                    # Duplicate color detected
                    tasks_to_update.append(task)
                else:
                    # Valid unique color
                    used_colors.add(task.color)
            
            # Second pass: Assign new colors to tasks needing updates
            if tasks_to_update:
                # Calculate evenly distributed colors based on total number of tasks at this site
                total_tasks = len(site_tasks)
                
                for task in tasks_to_update:
                    # Find an unused position in the color wheel
                    for i in range(total_tasks * 2):  # Double the range to ensure we find an available color
                        # Calculate a potential hue value with even distribution
                        hue = int((i * 360) / total_tasks) % 360
                        # Create a color with good contrast and brightness
                        potential_color = f"hsl({hue}, 70%, 50%)"
                        
                        # Use this color if it's not already in use
                        if potential_color not in used_colors:
                            task.color = potential_color
                            used_colors.add(potential_color)
                            tasks_updated += 1
                            break
            
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

# --- Move all startup DB logic inside a single app context ---
with app.app_context():
    try:
        run_auto_migration()  # Ensure columns exist before any queries
        print("[STARTUP] Auto-migration completed successfully")
    except Exception as e:
        print(f'[AUTO_MIGRATE ERROR] Critical migration failed: {e}')
        print("App startup may fail due to missing database columns")
        # Don't exit here, but log the critical error
        import traceback
        print(traceback.format_exc())
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
            admin_flag_users = []
            try:
                # Try to query is_admin column if it exists
                admin_flag_users = User.query.filter_by(is_admin=True).all()
            except:
                print("[APP] is_admin column not available, skipping that filter")
            
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
    
    # Then run the default admin creation logic
    add_default_admin_if_needed()
    
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
    initialize_db_connection()
    ensure_db_schema()
    ensure_maintenance_records_schema()
    assign_colors_to_audit_tasks()  # Add colors to any audit tasks that don't have them yet
    db.create_all()

# Add database connection check before requests
@app.before_request
def ensure_db_connection():
    """Ensure database connection is working before each request."""
    # Skip for static files and health checks
    if request.path.startswith('/static/') or request.path == '/health-check':
        return
        
    # Check DB connection for routes that need it
    if request.endpoint not in ['static', 'health_check'] and not check_db_connection():
        return jsonify({'error': 'Database connection failure'}), 500

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
                    if part.quantity == 0:
                        out_of_stock += 1
                    elif part.quantity < 5:  # Assume 5 is the low stock threshold
                        low_stock += 1
            
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

    # Define a safe_date function for templates (used in audit_history.html)
    def safe_date(year, month, day):
        """Return a valid date object, or None if invalid."""
        try:
            return datetime(year, month, day)
        except Exception:
            return None

    return {
        'is_admin_user': is_admin_user(current_user) if is_auth else False,
        'datetime': datetime,
        'now': datetime.now(),
        'hasattr': hasattr,  # Add hasattr function to be available in templates
        'has_permission': has_permission,  # Add permission checking helper
        'Role': Role,  # Add Role class to template context so it can be used in templates
        'safe_date': safe_date  # Add safe_date function for templates
    }

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username and password:
            user = User.query.filter_by(username=username).first()
            
            if user and check_password_hash(user.password_hash, password):
                login_user(user, remember=request.form.get('remember'))
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'error')
        else:
            flash('Please enter both username and password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Handle password reset requests."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        if email:
            user = User.query.filter_by(email=email).first()
            if user:
                # TODO: Implement actual password reset functionality with email
                # For now, just show a success message
                flash('If an account with that email exists, a password reset link has been sent.', 'success')
                return redirect(url_for('login'))
            else:
                # Don't reveal whether the email exists for security reasons
                flash('If an account with that email exists, a password reset link has been sent.', 'success')
                return redirect(url_for('login'))
        else:
            flash('Please enter your email address', 'error')
    
    return render_template('forgot_password.html')

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        show_decommissioned = request.args.get('show_decommissioned', 'false').lower() == 'true'
        site_filter = request.args.get('site_filter', 'all')  # Get the selected site filter
        
        if user_can_see_all_sites(current_user):
            all_sites = Site.query.options(joinedload(Site.machines).joinedload(Machine.parts)).all()
        else:
            if not hasattr(current_user, 'sites') or not current_user.sites:
                app.logger.warning(f"User {current_user.username} (ID: {current_user.id}) has no site assignments")
                return render_template('dashboard.html', 
                                      sites=[], 
                                      overdue_count=0, 
                                      due_soon_count=0, 
                                      ok_count=0, 
                                      total_parts=0,
                                      no_sites=True,  # Flag to show special message in template
                                      now=datetime.now(),
                                      show_decommissioned=show_decommissioned,
                                      decommissioned_count=0,
                                      site_filter=site_filter)
            all_sites = (
                Site.query.options(joinedload(Site.machines).joinedload(Machine.parts))
                .filter(Site.id.in_([site.id for site in current_user.sites]))
                .all()
            )
        
        # Apply site filter if a specific site is selected
        if site_filter != 'all' and site_filter.isdigit():
            sites = [site for site in all_sites if str(site.id) == site_filter]
        else:
            sites = all_sites
        site_ids = [site.id for site in sites]
        decommissioned_count = 0
        if site_ids:
            decommissioned_count = Machine.query.filter(
                Machine.site_id.in_(site_ids),
                Machine.decommissioned == True
            ).count()
        machines = []
        if site_ids:
            if show_decommissioned:
                machines = Machine.query.filter(Machine.site_id.in_(site_ids)).all()
            else:
                machines = Machine.query.filter(
                    Machine.site_id.in_(site_ids),
                    Machine.decommissioned == False
                ).all()
        parts = []
        machine_ids = [machine.id for machine in machines]
        if machine_ids:
            parts = Part.query.filter(Part.machine_id.in_(machine_ids)).all()
        now = datetime.now()
        machine_part_status = {}
        for machine in machines:
            m_parts = [p for p in parts if p.machine_id == machine.id]
            overdue = 0
            due_soon = 0
            ok = 0
            for part in m_parts:
                days_until = (part.next_maintenance - now).days if part.next_maintenance else None
                if days_until is None:
                    ok += 1  # treat as ok if no date
                elif days_until < 0:
                    overdue += 1
                elif days_until <= 30:
                    due_soon += 1
                else:
                    ok += 1
            machine_part_status[machine.id] = {
                'overdue': overdue,
                'due_soon': due_soon,
                'ok': ok,
                'total': len(m_parts)
            }
        # --- NEW: Limit Overdue/Due Soon Parts to 3 Most Relevant per Site ---
        site_part_highlights = {}
        site_part_totals = {}
        for site in sites:
            overdue_parts = []
            due_soon_parts = []
            for machine in site.machines:
                if not show_decommissioned and machine.decommissioned:
                    continue
                for part in machine.parts:
                    days_until = (part.next_maintenance - now).days if part.next_maintenance else None
                    if days_until is not None:
                        if days_until < 0:
                            overdue_parts.append((part, machine, site, days_until))
                        elif days_until <= (site.notification_threshold or 30):
                            due_soon_parts.append((part, machine, site, days_until))
            # Sort and limit
            overdue_parts_sorted = sorted(overdue_parts, key=lambda x: x[3])
            due_soon_parts_sorted = sorted(due_soon_parts, key=lambda x: x[3])
            site_part_highlights[site.id] = {
                'overdue': overdue_parts_sorted[:3],
                'due_soon': due_soon_parts_sorted[:3]
            }
            site_part_totals[site.id] = {
                'overdue': len(overdue_parts_sorted),
                'due_soon': len(due_soon_parts_sorted)
            }
        # For all sites view, aggregate top 3 overall and total counts
        all_overdue = []
        all_due_soon = []
        all_overdue_total = 0
        all_due_soon_total = 0
        for site in sites:
            all_overdue.extend(site_part_highlights[site.id]['overdue'])
            all_due_soon.extend(site_part_highlights[site.id]['due_soon'])
            all_overdue_total += site_part_totals[site.id]['overdue']
            all_due_soon_total += site_part_totals[site.id]['due_soon']
        all_overdue = sorted(all_overdue, key=lambda x: x[3])[:3]
        all_due_soon = sorted(all_due_soon, key=lambda x: x[3])[:3]
        
        # Calculate overall counts for status counters
        overdue_count = all_overdue_total
        due_soon_count = all_due_soon_total
        ok_count = 0
        total_parts = len(parts)
        
        # Calculate OK count (parts that are not overdue or due soon)
        for part in parts:
            days_until = (part.next_maintenance - now).days if part.next_maintenance else None
            if days_until is None:
                ok_count += 1
            elif days_until >= 0:
                # Find the part's machine's site for notification threshold
                part_machine = next((m for m in machines if m.id == part.machine_id), None)
                if part_machine:
                    part_site = next((s for s in sites if s.id == part_machine.site_id), None)
                    threshold = part_site.notification_threshold if part_site else 30
                    if days_until > threshold:
                        ok_count += 1
        
        return render_template(
            'dashboard.html',
            sites=sites,
            all_sites=all_sites,  # Pass all available sites for the dropdown
            site_filter=site_filter,  # Pass current filter selection
            machines=machines,
            parts=parts,
            machine_part_status=machine_part_status,
            now=now,
            show_decommissioned=show_decommissioned,
            decommissioned_count=decommissioned_count,
            site_part_highlights=site_part_highlights,
            site_part_totals=site_part_totals,
            all_overdue=all_overdue,
            all_due_soon=all_due_soon,
            all_overdue_total=all_overdue_total,
            all_due_soon_total=all_due_soon_total,
            overdue_count=overdue_count,
            due_soon_count=due_soon_count,
            ok_count=ok_count,
            total_parts=total_parts,
            )
    except Exception as e:
        app.logger.error(f"Error in dashboard view: {e}")
        return render_template('dashboard.html', 
                             error=True,
                             sites=[],
                             all_sites=[],
                             site_filter='all',
                             overdue_count=0,
                             due_soon_count=0,
                             ok_count=0,
                             total_parts=0,
                             now=datetime.now(),
                             show_decommissioned=False,
                             decommissioned_count=0)

@app.route('/maintenance/records')
@login_required
def maintenance_records_page():
    """Redirect /maintenance/records to /api/maintenance/records, preserving query parameters."""
    query_string = request.query_string.decode('utf-8')
    if query_string:
        return redirect(f'/api/maintenance/records?{query_string}')
    return redirect('/api/maintenance/records')

@app.route('/sites')
@login_required
def manage_sites():
    """Sites management page."""
    try:
        # Check if user has permission to view sites
        if not current_user.is_admin:
            flash('You do not have permission to manage sites.', 'error')
            return redirect(url_for('dashboard'))
        
        return render_template('sites.html', can_create=current_user.is_admin)
    except Exception as e:
        app.logger.error(f"Error in manage_sites view: {e}")
        flash('An error occurred while loading the sites page.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/machines')
@login_required
def manage_machines():
    """Machines management page."""
    try:
        # Check if user has permission to view machines
        if not current_user.is_admin:
            flash('You do not have permission to manage machines.', 'error')
            return redirect(url_for('dashboard'))
        
        # For now, redirect to dashboard as we don't have a machines template yet
        flash('Machine management page is coming soon.', 'info')
        return redirect(url_for('dashboard'))
    except Exception as e:
        app.logger.error(f"Error in manage_machines view: {e}")
        flash('An error occurred while loading the machines page.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/parts')
@login_required
def manage_parts():
    """Parts management page."""
    try:
        # Check if user has permission to view parts
        if not current_user.is_admin:
            flash('You do not have permission to manage parts.', 'error')
            return redirect(url_for('dashboard'))
        
        # For now, redirect to dashboard as we don't have a parts template yet
        flash('Parts management page is coming soon.', 'info')
        return redirect(url_for('dashboard'))
    except Exception as e:
        app.logger.error(f"Error in manage_parts view: {e}")
        flash('An error occurred while loading the parts page.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/admin')
@login_required
def admin():
    """Admin dashboard page."""
    try:
        # Check if user has admin privileges
        if not current_user.is_admin:
            flash('You do not have permission to access the admin area.', 'error')
            return redirect(url_for('dashboard'))
        
        # For now, redirect to dashboard as we don't have an admin template yet
        flash('Admin dashboard is coming soon.', 'info')
        return redirect(url_for('dashboard'))
    except Exception as e:
        app.logger.error(f"Error in admin view: {e}")
        flash('An error occurred while loading the admin page.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/admin/users')
@login_required  
def manage_users():
    """Manage users page"""
    try:
        from models import User, Role
        users = User.query.all()
        roles = Role.query.all()
        return render_template('admin/users.html', users=users, roles=roles)
    except Exception as e:
        app.logger.error(f"Error in manage_users view: {e}")
        flash('An error occurred while loading the users management page.', 'error')
        return redirect(url_for('admin'))

@app.route('/admin/roles')
@login_required
def manage_roles():
    """Manage roles page"""
    try:
        from models import Role
        roles = Role.query.all()
        return render_template('admin/roles.html', roles=roles)
    except Exception as e:
        app.logger.error(f"Error in manage_roles view: {e}")
        flash('An error occurred while loading the roles management page.', 'error')
        return redirect(url_for('admin'))

@app.route('/debug_info')
@login_required
def debug_info():
    """Debug info page"""
    try:
        return render_template('admin/debug_info.html')
    except Exception as e:
        app.logger.error(f"Error in debug_info view: {e}")
        flash('An error occurred while loading the debug info page.', 'error')
        return redirect(url_for('admin'))

@app.route('/test_email')
@login_required  
def test_email():
    """Test email page"""
    try:
        return render_template('admin/test_email.html')
    except Exception as e:
        app.logger.error(f"Error in test_email view: {e}")
        flash('An error occurred while loading the test email page.', 'error')
        return redirect(url_for('admin'))

@app.route('/profile')
@login_required
def user_profile():
    """User profile page."""
    try:
        # Use the existing profile template
        return render_template('profile.html')
    except Exception as e:
        app.logger.error(f"Error in user_profile view: {e}")
        flash('An error occurred while loading your profile.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/audits')
@login_required
def audits_page():
    """Audits page."""
    try:
        # For now, show a coming soon message
        flash('Audits page is coming soon.', 'info')
        return redirect(url_for('dashboard'))
    except Exception as e:
        app.logger.error(f"Error in audits_page view: {e}")
        flash('An error occurred while loading the audits page.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/audit_history')
@login_required
def audit_history_page():
    """Audit history page."""
    try:
        # For now, show a coming soon message
        flash('Audit history page is coming soon.', 'info')
        return redirect(url_for('dashboard'))
    except Exception as e:
        app.logger.error(f"Error in audit_history_page view: {e}")
        flash('An error occurred while loading the audit history page.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/maintenance')
@login_required
def maintenance_page():
    """Maintenance page for recording maintenance activities"""
    try:
        from models import Site
        sites = Site.query.order_by(Site.name).all()
        return render_template('maintenance.html', sites=sites)
    except Exception as e:
        app.logger.error(f"Error in maintenance_page view: {e}")
        flash('An error occurred while loading the maintenance page.', 'error')
        return redirect(url_for('dashboard'))














