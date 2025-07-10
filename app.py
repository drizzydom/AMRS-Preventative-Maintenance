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
        
        # Simple fallbacks for common routes
        if endpoint == 'manage_machines':
            return '/machines'
        elif endpoint == 'manage_sites':
            return '/sites'  
        elif endpoint == 'manage_parts':
            return '/parts'
        elif endpoint == 'manage_users':
            return '/admin/users'
        elif endpoint == 'manage_roles':  # Add fallback for 'manage_roles'
            return '/admin/roles'
        elif endpoint == 'admin_roles':  # Add fallback for 'admin_roles' as well
            return '/admin/roles'
        elif endpoint == 'update_maintenance' and 'part_id' in values:
            return f'/update-maintenance/{values["part_id"]}'
        elif endpoint == 'machine_history' and 'machine_id' in values:
            return f'/machine-history/{values["machine_id"]}'
        elif endpoint == 'admin_dashboard':
            return '/admin'
        elif endpoint.startswith('admin_'):
            return '/admin'
        else:
            return '/dashboard'

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
                        if part.next_maintenance:
                            try:
                                # Ensure next_maintenance is a datetime object
                                if isinstance(part.next_maintenance, str):
                                    # Try to parse string to datetime
                                    try:
                                        part.next_maintenance = datetime.strptime(part.next_maintenance, '%Y-%m-%d %H:%M:%S')
                                    except ValueError:
                                        try:
                                            part.next_maintenance = datetime.strptime(part.next_maintenance, '%Y-%m-%d')
                                        except ValueError:
                                            app.logger.warning(f"Invalid date format for part {part.id}: {part.next_maintenance}")
                                            continue  # Skip invalid date strings
                                
                                days_until = (part.next_maintenance - now).days
                                if days_until < 0:
                                    site_overdue.append({
                                        'part': part,
                                        'machine': machine,
                                        'site': site,
                                        'days_until': days_until
                                    })
                                    if site in sites:  # Only count for displayed sites
                                        overdue_count += 1
                                    all_overdue.append({
                                        'part': part,
                                        'machine': machine,
                                        'site': site,
                                        'days_until': days_until
                                    })
                                elif days_until <= 30:
                                    site_due_soon.append({
                                        'part': part,
                                        'machine': machine,
                                        'site': site,
                                        'days_until': days_until
                                    })
                                    if site in sites:  # Only count for displayed sites
                                        due_soon_count += 1
                                    all_due_soon.append({
                                        'part': part,
                                        'machine': machine,
                                        'site': site,
                                        'days_until': days_until
                                    })
                                else:
                                    if site in sites:  # Only count for displayed sites
                                        ok_count += 1
                            except (TypeError, AttributeError) as e:
                                # Skip parts with invalid maintenance dates
                                app.logger.warning(f"Invalid maintenance date for part {part.id}: {e}")
                                continue
            
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
        app.logger.error(f"Dashboard error: {str(e)}")
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
                              now=datetime.now())
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
                              now=datetime.now())
        
        # Render admin dashboard view with safe navigation links
        return render_template('admin.html',
                              user_count=user_count,
                              roles_count=roles_count,
                              site_count=site_count,
                              sites_count=sites_count,  # Include both variables
                              machine_count=machine_count,
                              part_count=part_count,
                              admin_links=admin_links,
                              section='dashboard',
                              active_section='dashboard')
    except Exception as e:
        app.logger.error(f"Error in admin route: {e}")
        flash('An error occurred while loading the admin dashboard.', 'danger')
        return redirect('/dashboard')  # Use direct URL instead of url_for to avoid potential circular errors

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

    # Restrict sites for non-admins
    if current_user.is_admin:
        audit_tasks = AuditTask.query.all()
        sites = Site.query.all()
    else:
        user_site_ids = [site.id for site in current_user.sites]
        audit_tasks = AuditTask.query.filter(AuditTask.site_id.in_(user_site_ids)).all()
        sites = current_user.sites

    today = date.today()
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
                    if completions.get((task.id, machine.id)) and completions.get((task.id, machine.id)).completed:
                        continue
                    # Strictly enforce interval: only allow if no previous completion or today >= next eligible date
                    next_eligible = eligibility.get((task.id, machine.id))
                    if next_eligible is not None and today < next_eligible:
                        continue  # Not eligible yet
                    # Only record completion if eligible (either no previous completion or today >= next_eligible)
                    completion = AuditTaskCompletion(
                        audit_task_id=task.id,
                        machine_id=machine.id,
                        date=today,
                        completed=True,
                        completed_by=current_user.id,
                        completed_at=datetime.now()
                    )
                    db.session.add(completion)
                    updated += 1
        if updated:
            db.session.commit()
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

    return render_template('audit_history.html', audit_tasks=audit_tasks, sites=sites, completions=completions, today=today, can_delete_audits=can_delete_audits, can_complete_audits=can_complete_audits, eligibility=eligibility, get_calendar_weeks=get_calendar_weeks, month_completions=month_completions)

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def admin_users():
    """User management page."""
    # Use standardized admin check
    if not is_admin_user(current_user):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Handle form submission for creating a new user
    if request.method == 'POST':
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
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                role=role
            )
            
            # Add user to database
            db.session.add(new_user)
            db.session.commit()
            
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
    """Redirect or render the roles management page."""
    if not is_admin_user(current_user):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Handle form submission for creating a new role
    if request.method == 'POST':
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
        # Restrict sites for non-admins
        if current_user.is_admin:
            sites = Site.query.all()
        else:
            sites = current_user.sites

        # Get all machines, parts, and sites for the form
        machines = Machine.query.filter(Machine.site_id.in_([site.id for site in sites])).all()
        parts = Part.query.filter(Part.machine_id.in_([machine.id for machine in machines])).all()
        
        # Get all maintenance records with related data
        maintenance_records = MaintenanceRecord.query.filter(MaintenanceRecord.machine_id.in_([machine.id for machine in machines])).order_by(MaintenanceRecord.date.desc()).all()
        
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
                    flash('Maintenance record added successfully!', 'success')
                    return redirect(url_for('maintenance_page'))
                except ValueError:
                    flash('Invalid date format! Use YYYY-MM-DD.', 'danger')
        
        return render_template('maintenance.html', 
                              maintenance_records=maintenance_records,
                              machines=machines,
                              parts=parts,
                              sites=sites)
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
        # Add debug for login attempts
        app.logger.debug(f"Login attempt: username={username}, remember={remember}")
        user = User.query.filter_by(username_hash=hash_value(username)).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            # Set remember preference and token
            user.set_remember_preference(remember)
            if remember:
                token = user.generate_remember_token()
                db.session.commit()
                # Set cookie for persistent login (30 days)
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
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Handle user logout."""
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
        
        if user:
            # Generate a password reset token
            reset_token = secrets.token_urlsafe(32)
            expires = datetime.now() + timedelta(hours=24)
            
            # Store token in database
            user.reset_token = reset_token
            user.reset_token_expiration = expires
            db.session.commit()
            
            # In a production app, you would send an email with the reset link
            # For now, just flash a message with the token (for demonstration)
            reset_url = url_for('reset_password', token=reset_token, _external=True)
            flash(f'Password reset link: {reset_url}', 'info')
            
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
    
    # Check if token is valid and not expired
    if not user or (user.reset_token_expiration and user.reset_token_expiration < datetime.now()):
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if not password or len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return redirect(url_for('reset_password', token=token))
        elif password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('reset_password', token=token))
        else:
            # Update password and clear reset token
            user.password_hash = generate_password_hash(password)
            user.reset_token = None
            user.reset_token_expiration = None
            db.session.commit()
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
            'server_time': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/sync/data', methods=['POST'])
@login_required
def sync_data():
    """Handle data synchronization requests from desktop clients."""
    try:
        data = request.json
        sync_type = data.get('type')
        if sync_type == 'push':
            # Handle data being pushed from client to server
            # Process items from the client
            return jsonify({'status': 'success', 'message': 'Data received successfully'})
            
        elif sync_type == 'pull':
            # Handle client requesting data from server
            # Return requested data based on parameters
            entity_type = data.get('entity_type')
            timestamp = data.get('last_sync')
            
            # This is simplified - in a real implementation you would fetch actual data
            return jsonify({
                'status': 'success',
                'data': {
                    'type': entity_type,
                    'items': []  # Actual data would go here
                }
            })
        else:
            return jsonify({'status': 'error', 'message': 'Invalid sync type'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

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
                flash('You do not have access to this site.', 'danger')
                return redirect(url_for('manage_machines'))
                
            # Filter machines by selected site
            machines_query = Machine.query.filter_by(site_id=site_id)
            title = f"Machines for {Site.query.get_or_404(site_id).name}"
        else:
            # Show machines from all sites user has access to
            machines_query = Machine.query.filter(Part.machine_id.in_(machine_ids)) if machine_ids else Machine.query.filter(False)
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
    """Gather statistics for the admin dashboard."""
    from db_utils import get_table_row_counts
    success, result = get_table_row_counts()
    if not success or not isinstance(result, dict):
        # Return empty stats if error
        return {}
    # Add any additional stats here if needed
    # Optionally, add derived stats for dashboard
    stats = {
        'users': result.get('users', 0),
        'roles': result.get('roles', 0),
        'sites': result.get('sites', 0),
        'machines': result.get('machines', 0),
        'active_machines': result.get('machines', 0),  # For compatibility
        'decommissioned_machines': 0,  # Add logic if you track this
        'parts': result.get('parts', 0),
        'maintenance_records': result.get('maintenance_records', 0),
        'audit_tasks': 0,  # Add logic if you track this
        'maintenance_overdue': 0,  # Add logic if you track this
        'maintenance_due_soon': 0,  # Add logic if you track this
        'maintenance_ok': 0,  # Add logic if you track this
    }
    return stats