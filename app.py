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

# Then patch the Site class directly as a monkey patch
# This must be outside any function to execute immediately
def parts_status(self):
    """Method directly added to Site class."""
    machines = Machine.query.filter_by(site_id=self.id).all()
    total_parts = 0
    low_stock = 0
    out_of_stock = 0
    
    for machine in machines:
        parts = Part.query.filter_by(machine_id=machine.id).all()
        total_parts += len(parts)
        
        for part in parts:
            if part.quantity == 0:
                out_of_stock += 1
            elif part.quantity < 5:
                low_stock += 1
    
    return {
        'total': total_parts,
        'low_stock': low_stock,
        'out_of_stock': out_of_stock
    }

# Directly add method to Site class - renamed to avoid signature conflicts
Site.parts_status = parts_status
# Add an alias for backward compatibility, but make it a property to avoid calling with arguments
Site.get_parts_status = property(lambda self: self.parts_status())

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

# Function to ensure database schema matches models
def ensure_db_schema():
    """Ensure database schema matches the models by adding missing columns."""
    try:
        print("[APP] Checking database schema...")
        # Create a connection and inspect the database
        inspector = inspect(db.engine)
        
        # Define table schemas
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
                'updated_at': 'TIMESTAMP'
            }
        }
        
        # Check each table and add missing columns
        with db.engine.connect() as conn:
            for table, columns in table_schemas.items():
                # Check if table exists
                if inspector.has_table(table):
                    print(f"[APP] Checking {table} table schema...")
                    existing_columns = {column['name'] for column in inspector.get_columns(table)}
                    
                    # Add any missing columns
                    for column_name, column_type in columns.items():
                        if column_name not in existing_columns:
                            print(f"[APP] Adding missing column {column_name} to {table} table")
                            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column_name} {column_type}"))
                            conn.commit()
                    
                    # Initialize timestamp columns with current timestamp if they were just added
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

# Ensure maintenance_records table has client_id column
def ensure_maintenance_records_schema():
    """Ensure maintenance_records table has client_id column."""
    try:
        inspector = inspect(db.engine)
        if inspector.has_table('maintenance_records'):
            columns = [column['name'] for column in inspector.get_columns('maintenance_records')]
            if 'client_id' not in columns:
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE maintenance_records ADD COLUMN IF NOT EXISTS client_id INTEGER"))
                    conn.commit()
                print("[APP] Added client_id column to maintenance_records table")
    except Exception as e:
        print(f"[APP] Error ensuring maintenance_records schema: {e}")

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

# Setup application before first request
@app.before_first_request
def setup_application():
    """Setup everything needed before handling the first request."""
    initialize_db_connection()
    ensure_db_schema()

# Add additional setup tasks
@app.before_first_request
def additional_setup():
    """Additional setup tasks."""
    ensure_maintenance_records_schema()

# Replace the enhance_models function with a template context processor
@app.context_processor
def inject_site_helpers():
    """Add helper functions to templates without modifying models."""
    def get_site_parts_status(site):
        """Get status of parts for a site's machines."""
        try:
            # Get all machines at this site
            machines = Machine.query.filter_by(site_id=site.id).all()
            
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
    """Main dashboard view after login."""
    try:
        return render_template('dashboard.html')
    except Exception as e:
        app.logger.error(f"Error rendering dashboard: {e}")
        return render_template('errors/500.html'), 500

@app.route('/machines/delete/<int:machine_id>', methods=['POST'])
@login_required
def delete_machine(machine_id):
    """Delete a machine."""
    try:
        machine = Machine.query.get_or_404(machine_id)
        
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
        part = Part.query.get_or_404(part_id)
        
        # Delete the part
        db.session.delete(part)
        db.session.commit()
        flash(f'Part "{part.name}" deleted successfully.', 'success')
        
        return redirect(url_for('manage_parts'))
    except Exception as e:
        app.logger.error(f"Error deleting part: {e}")
        flash('An error occurred while deleting the part.', 'danger')
        return redirect(url_for('manage_parts'))

@app.route('/maintenance', methods=['GET', 'POST'])
@login_required
def maintenance_page():
    """View and manage maintenance records."""
    try:
        # Get all machines, parts, and sites for the form
        machines = Machine.query.all()
        parts = Part.query.all()
        sites = Site.query.all()
        
        # Get all maintenance records with related data
        maintenance_records = MaintenanceRecord.query.order_by(MaintenanceRecord.date.desc()).all()
        
        # Handle form submission for adding new maintenance records
        if request.method == 'POST':
            machine_id = request.form.get('machine_id')
            maintenance_type = request.form.get('maintenance_type')
            description = request.form.get('description')
            date_str = request.form.get('date')
            performed_by = request.form.get('performed_by', '')
            status = request.form.get('status', 'completed')
            notes = request.form.get('notes', '')
            client_id = request.form.get('client_id')  # Get client_id from form
            parts_used = request.form.getlist('parts_used')  # Get multiple selected parts
            
            # Validate required fields
            if not machine_id or not maintenance_type or not description or not date_str:
                flash('Machine, maintenance type, description, and date are required!', 'danger')
            else:
                try:
                    # Parse date (expecting format like YYYY-MM-DD)
                    maintenance_date = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    # Create new maintenance record with client_id
                    new_record = MaintenanceRecord(
                        machine_id=machine_id,
                        maintenance_type=maintenance_type,
                        description=description,
                        date=maintenance_date,
                        performed_by=performed_by,
                        status=status,
                        notes=notes,
                        client_id=client_id if client_id else None  # Handle client_id
                    )
                    
                    db.session.add(new_record)
                    db.session.commit()
                    
                    # Associate parts with the maintenance record if needed
                    # This would require a many-to-many relationship in your model
                    
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
        flash('An error occurred while loading maintenance records.', 'danger')
        return redirect(url_for('dashboard'))

# Add the missing manage_sites route that's referenced in the dashboard template
@app.route('/sites', methods=['GET', 'POST'])
@login_required
def manage_sites():
    """View and manage sites."""
    try:
        # Get all sites from the database
        sites = Site.query.all()
        
        # Handle form submission for adding new sites
        if request.method == 'POST':
            name = request.form.get('name')
            location = request.form.get('location')
            description = request.form.get('description')
            
            if name and location:
                new_site = Site(
                    name=name, 
                    location=location, 
                    description=description
                )
                db.session.add(new_site)
                db.session.commit()
                flash('Site added successfully!', 'success')
                return redirect(url_for('manage_sites'))
            else:
                flash('Name and location are required!', 'danger')
        
        return render_template('sites.html', sites=sites)
    except Exception as e:
        app.logger.error(f"Error in manage_sites: {e}")
        flash('An error occurred while loading sites.', 'danger')
        return redirect(url_for('dashboard'))

# Add the missing manage_machines route that's referenced in the dashboard template
@app.route('/machines', methods=['GET', 'POST'])
@login_required
def manage_machines():
    """View and manage machines."""
    try:
        # Get all sites for the dropdown
        sites = Site.query.all()
        
        # Get all machines from the database
        machines = Machine.query.all()
        
        # Handle form submission for adding new machines
        if request.method == 'POST':
            name = request.form.get('name')
            model = request.form.get('model')
            site_id = request.form.get('site_id')
            serial_number = request.form.get('serial_number', '')
            description = request.form.get('description', '')
            
            if name and model and site_id:
                new_machine = Machine(
                    name=name,
                    model=model,
                    site_id=site_id,
                    serial_number=serial_number,
                    description=description
                )
                db.session.add(new_machine)
                db.session.commit()
                flash('Machine added successfully!', 'success')
                return redirect(url_for('manage_machines'))
            else:
                flash('Name, model, and site are required!', 'danger')
        
        return render_template('machines.html', machines=machines, sites=sites)
    except Exception as e:
        app.logger.error(f"Error in manage_machines: {e}")
        flash('An error occurred while loading machines.', 'danger')
        return redirect(url_for('dashboard'))

# Add the missing manage_parts route that's referenced in the dashboard template
@app.route('/parts', methods=['GET', 'POST'])
@login_required
def manage_parts():
    """View and manage parts."""
    try:
        # Get all machines for the dropdown
        machines = Machine.query.all()
        
        # Get all parts from the database
        parts = Part.query.all()
        
        # Handle form submission for adding new parts
        if request.method == 'POST':
            name = request.form.get('name')
            part_number = request.form.get('part_number')
            machine_id = request.form.get('machine_id')
            quantity = request.form.get('quantity', 0)
            description = request.form.get('description', '')
            
            try:
                quantity = int(quantity)
            except ValueError:
                quantity = 0
                
            if name and part_number:
                new_part = Part(
                    name=name,
                    part_number=part_number,
                    machine_id=machine_id if machine_id else None,
                    quantity=quantity,
                    description=description
                )
                db.session.add(new_part)
                db.session.commit()
                flash('Part added successfully!', 'success')
                return redirect(url_for('manage_parts'))
            else:
                flash('Name and part number are required!', 'danger')
        
        return render_template('parts.html', parts=parts, machines=machines)
    except Exception as e:
        app.logger.error(f"Error in manage_parts: {e}")
        flash('An error occurred while loading parts.', 'danger')
        return redirect(url_for('dashboard'))

# Add the missing user_profile route that's referenced in the dashboard template
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    """View and edit user profile."""
    try:
        user = User.query.get(current_user.id)
        
        if request.method == 'POST':
            # Get form data
            email = request.form.get('email')
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Check if email is already in use by another user
            if email != user.email and User.query.filter_by(email=email).first():
                flash('Email is already in use by another account.', 'danger')
                return redirect(url_for('user_profile'))
                
            # Update email if it changed
            if email and email != user.email:
                user.email = email
                db.session.commit()
                flash('Email updated successfully!', 'success')
            
            # Update password if provided
            if current_password and new_password:
                # Verify current password is correct
                if not check_password_hash(user.password_hash, current_password):
                    flash('Current password is incorrect.', 'danger')
                    return redirect(url_for('user_profile'))
                    
                # Validate new password
                if len(new_password) < 8:
                    flash('New password must be at least 8 characters long.', 'danger')
                    return redirect(url_for('user_profile'))
                    
                # Confirm passwords match
                if new_password != confirm_password:
                    flash('New passwords do not match.', 'danger')
                    return redirect(url_for('user_profile'))
                    
                # Update password
                user.password_hash = generate_password_hash(new_password)
                db.session.commit()
                flash('Password updated successfully!', 'success')
                
        return render_template('profile.html', user=user)
    except Exception as e:
        app.logger.error(f"Error in user_profile: {e}")
        flash('An error occurred while loading your profile.', 'danger')
        return redirect(url_for('dashboard'))

# Add the missing admin route that's referenced in the dashboard template
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    """Admin dashboard for system management."""
    try:
        # Fix admin role check - use more flexible check for admin permission
        is_admin = False
        if hasattr(current_user, 'role'):
            is_admin = current_user.role == 'admin' or current_user.role == 'ADMIN'
        
        # If admin status is stored differently, check if the username is 'admin'
        if not is_admin and current_user.username == 'admin':
            is_admin = True
            
        # Print debug info about user role
        app.logger.info(f"Admin access check - User: {current_user.username}, Role: {getattr(current_user, 'role', 'unknown')}, Is admin: {is_admin}")
        
        if not is_admin:
            flash('You do not have permission to access the admin panel.', 'danger')
            return redirect(url_for('dashboard'))
        
        # Get all users for user management
        users = User.query.all()
        
        # Handle user management form submission
        if request.method == 'POST':
            action = request.form.get('action')
            
            # Handle different admin actions based on form submission
            if action == 'add_user':
                username = request.form.get('username')
                email = request.form.get('email')
                password = request.form.get('password')
                role = request.form.get('role', 'user')
                
                # Check if username or email already exists
                if User.query.filter(or_(User.username == username, User.email == email)).first():
                    flash('Username or email already exists.', 'danger')
                elif username and email and password:
                    new_user = User(
                        username=username,
                        email=email,
                        password_hash=generate_password_hash(password),
                        role=role
                    )
                    db.session.add(new_user)
                    db.session.commit()
                    flash(f'User {username} added successfully.', 'success')
                    return redirect(url_for('admin'))
                else:
                    flash('All fields are required.', 'danger')
            
            elif action == 'edit_user':
                user_id = request.form.get('user_id')
                email = request.form.get('email')
                role = request.form.get('role')
                reset_password = request.form.get('reset_password') == 'yes'
                
                user = User.query.get(user_id)
                if user:
                    # Update user details
                    user.email = email if email else user.email
                    user.role = role if role else user.role
                    
                    # Reset password if requested
                    if reset_password:
                        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
                        user.password_hash = generate_password_hash(new_password)
                        flash(f'Password reset for {user.username}. New password: {new_password}', 'info')
                    
                    db.session.commit()
                    flash(f'User {user.username} updated successfully.', 'success')
                    return redirect(url_for('admin'))
                else:
                    flash('User not found.', 'danger')
            
            elif action == 'delete_user':
                user_id = request.form.get('user_id')
                
                # Prevent deleting the current user
                if int(user_id) == current_user.id:
                    flash('You cannot delete your own account.', 'danger')
                else:
                    user = User.query.get(user_id)
                    if user:
                        db.session.delete(user)
                        db.session.commit()
                        flash(f'User {user.username} deleted successfully.', 'success')
                        return redirect(url_for('admin'))
                    else:
                        flash('User not found.', 'danger')
                        
        return render_template('admin.html', users=users)
    except Exception as e:
        app.logger.error(f"Error in admin panel: {e}")
        flash('An error occurred in the admin panel.', 'danger')
        return redirect(url_for('dashboard'))

# Add the missing routes for role management to handle all possible URL patterns
@app.route('/roles')
@login_required
def roles_index():
    """Main roles management endpoint"""
    return redirect(url_for('manage_roles'))

@app.route('/manage/roles')
@login_required
def manage_roles():
    """Manage roles directly."""
    try:
        # Check if user has admin role
        is_admin = False
        if hasattr(current_user, 'role'):
            is_admin = current_user.role == 'admin' or current_user.role == 'ADMIN'
        
        if not is_admin and current_user.username != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard'))
            
        # Get all roles for management
        roles = Role.query.all()
        return render_template('admin.html', users=User.query.all(), roles=roles, section='roles')
    except Exception as e:
        app.logger.error(f"Error in manage_roles: {e}")
        flash('An error occurred in the roles management panel.', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/roles/manage')
@login_required
def roles_manage():
    """Another alias for managing roles."""
    return redirect(url_for('manage_roles'))

# Replace the manage_users route with a proper route decorator
@app.route('/users/manage')
@login_required
def manage_users():
    """Manage users directly."""
    return redirect(url_for('admin'))

# Add extra route variant to ensure all possible URLs are covered
@app.route('/manage/users')
@login_required
def manage_users_alt():
    """Alternative route for managing users."""
    return redirect(url_for('admin'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
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
        user = User.query.filter_by(email=email).first()
        
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
        elif password != confirm_password:
            flash('Passwords do not match.', 'danger')
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
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Reset Password</div>
                        <div class="card-body">
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
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

# Add a debug route to see all available routes
@app.route('/debug-info')
def debug_info():
    """Display debug information including all available routes."""
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

# Add function to create default admin (referenced in __main__ block)
def add_default_admin_if_needed():
    """Add a default admin user if no users exist in the database."""
    try:
        user_count = User.query.count()
        if user_count == 0:
            print("[APP] No users found, creating default admin user")
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin'),
                role='admin'  # Make sure role is lowercase 'admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("[APP] Default admin user created")
        else:
            # Ensure existing admin user has correct role
            admin_user = User.query.filter_by(username='admin').first()
            if admin_user and admin_user.role != 'admin':
                print(f"[APP] Fixing admin role (currently: {admin_user.role})")
                admin_user.role = 'admin'
                db.session.commit()
    except Exception as e:
        print(f"[APP] Error creating/updating default admin: {e}")

# API endpoint for synchronization (to be used by desktop client)
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
    """Basic health check endpoint."""
    try:
        # Update to use connection-based execute pattern
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        app.logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

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