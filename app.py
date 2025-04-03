from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import click  # Add the missing click import
import secrets  # Add secrets for generating secure tokens
from datetime import datetime, timedelta
import logging
from functools import wraps
from flask_mail import Mail, Message
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.orm.attributes import flag_modified  # Add this import
import traceback
import jwt

# Get the directory of this file
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Define dotenv_path before using it
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)

# Function to ensure .env file exists
def ensure_env_file():
    if not os.path.exists(dotenv_path):
        with open(dotenv_path, 'w') as f:
            f.write("# Email Configuration\n")
            f.write("# WARNING: Replace these placeholders with your actual credentials\n")
            f.write("MAIL_SERVER=\n")
            f.write("MAIL_PORT=587\n")
            f.write("MAIL_USE_TLS=True\n")
            f.write("MAIL_USERNAME=\n")
            f.write("MAIL_PASSWORD=\n")
            f.write("MAIL_DEFAULT_SENDER=\n")
        print(f"Created default .env file at {dotenv_path}")
        print("IMPORTANT: Update with your actual email configuration")

# Ensure email template directories exist
def ensure_email_templates():
    templates_dir = os.path.join(BASE_DIR, 'templates')
    email_dir = os.path.join(templates_dir, 'email')
    # Create templates directory if it doesn't exist
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir, exist_ok=True)
        print(f"Created templates directory: {templates_dir}")
    # Create email directory if it doesn't exist
    if not os.path.exists(email_dir):
        os.makedirs(email_dir, exist_ok=True)
        print(f"Created email templates directory: {email_dir}")
        
    # Check if template files exist, no need to create them
    # since they're now part of the repository
    alert_path = os.path.join(email_dir, 'maintenance_alert.html')
    test_path = os.path.join(email_dir, 'test_email.html')
    notif_path = os.path.join(email_dir, 'maintenance_notification.html')
    
    missing_templates = []
    if not os.path.exists(alert_path):
        missing_templates.append('maintenance_alert.html')
    if not os.path.exists(test_path):
        missing_templates.append('test_email.html')
    if not os.path.exists(notif_path):
        missing_templates.append('maintenance_notification.html')
        
    if missing_templates:
        print(f"Warning: Missing email templates: {', '.join(missing_templates)}")
        print("Please ensure these files exist in the templates/email directory")
    else:
        print("Email templates verified.")

# Import cache configuration
from cache_config import configure_caching

# Import database configuration
from db_config import configure_database

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24).hex())

# Configure the database
configure_database(app)

# Initialize database
db = SQLAlchemy(app)

# Add session configuration to work across networks
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True only if using HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')  # Optional, use for multi-domain setup

# Configure caching for static assets
if 'configure_caching' in globals() or 'configure_caching' in locals():
    configure_caching(app)

# Email configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.example.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', 'yes', '1')
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'maintenance@example.com')
# Initialize Flask-Mail
mail = Mail(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Custom decorator to require admin access
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login', next=request.url))
        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Utility function for permission checking
def require_permission(permission):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.has_permission(permission):
                flash(f'Access denied. You need {permission} permission.')
                return redirect(url_for('dashboard'))
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Define permission constants for better organization and consistency
class Permissions:
    # User management
    USERS_VIEW = 'users.view'
    USERS_CREATE = 'users.create'
    USERS_EDIT = 'users.edit'
    USERS_DELETE = 'users.delete'
    
    # Role management
    ROLES_VIEW = 'roles.view'
    ROLES_CREATE = 'roles.create'
    ROLES_EDIT = 'roles.edit'
    ROLES_DELETE = 'roles.delete'
    
    # Site management
    SITES_VIEW = 'sites.view'
    SITES_VIEW_ASSIGNED = 'sites.view.assigned'  # New permission for viewing only assigned sites
    SITES_CREATE = 'sites.create'
    SITES_EDIT = 'sites.edit'
    SITES_DELETE = 'sites.delete'
    
    # Machine management
    MACHINES_VIEW = 'machines.view'
    MACHINES_CREATE = 'machines.create'
    MACHINES_EDIT = 'machines.edit'
    MACHINES_DELETE = 'machines.delete'
    
    # Part management
    PARTS_VIEW = 'parts.view'
    PARTS_CREATE = 'parts.create'
    PARTS_EDIT = 'parts.edit'
    PARTS_DELETE = 'parts.delete'
    
    # Maintenance management
    MAINTENANCE_VIEW = 'maintenance.view'
    MAINTENANCE_SCHEDULE = 'maintenance.schedule'
    MAINTENANCE_RECORD = 'maintenance.record'
    
    # Backup management
    BACKUP_VIEW = 'backup.view'
    BACKUP_CREATE = 'backup.create'
    BACKUP_RESTORE = 'backup.restore'
    BACKUP_EXPORT = 'backup.export'
    BACKUP_DELETE = 'backup.delete'
    BACKUP_SCHEDULE = 'backup.schedule'  # New permission for managing scheduled backups
    
    # Administration
    ADMIN_ACCESS = 'admin.access'
    ADMIN_FULL = 'admin.full'
    
    @classmethod
    def get_all_permissions(cls):
        """Return all available permissions as dict mapping permission to description"""
        permissions = {}
        for attr in dir(cls):
            if not attr.startswith('_') and not callable(getattr(cls, attr)) and attr != 'get_all_permissions':
                value = getattr(cls, attr)
                if isinstance(value, str):
                    # Format the name for display
                    category, action = value.split('.')[0:2]
                    if len(value.split('.')) > 2:
                        # Handle cases like 'sites.view.assigned'
                        modifier = value.split('.')[2]
                        display = f"{category.capitalize()} - {action.capitalize()} ({modifier})"
                    else:
                        display = f"{category.capitalize()} - {action.capitalize()}"
                    permissions[value] = display
        return permissions

# Define database models
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    permissions = db.Column(db.String(500), default="view")
    users = db.relationship('User', backref='role', lazy=True)
    def has_permission(self, permission):
        return permission in self.permissions.split(',')
    def get_permissions_list(self):
        return self.permissions.split(',')

user_site = db.Table('user_site',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('site_id', db.Integer, db.ForeignKey('site.id'), primary_key=True),
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    sites = db.relationship('Site', secondary=user_site, lazy='subquery',
                           backref=db.backref('users', lazy=True))
    email = db.Column(db.String(100))
    full_name = db.Column(db.String(100))
    reset_token = db.Column(db.String(100))
    reset_token_expiration = db.Column(db.DateTime)
    notification_preferences = db.Column(db.Text, default='{}')  # Add this column for storing preferences as JSON string
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    def has_permission(self, permission):
        if self.is_admin:
            return True
        if self.role:
            # Direct permission check
            if self.role.has_permission(permission):
                return True
            # Check for full admin access to this category
            if '.' in permission:
                category = permission.split('.')[0]
                if self.role.has_permission(f'{category}.full'):
                    return True
            # Check for admin permission
            if permission.startswith('admin.') and self.role.has_permission('admin.full'):
                return True
        return False
    def generate_reset_token(self):
        # Generate a secure token for password reset
        token = secrets.token_urlsafe(32)
        self.reset_token = token
        # Token expires after 1 hour
        self.reset_token_expiration = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        return token
    def verify_reset_token(self, token):
        # Verify the reset token is valid and not expired
        if self.reset_token != token:
            return False
        if not self.reset_token_expiration or self.reset_token_expiration < datetime.utcnow():
            return False
        return True
    def clear_reset_token(self):
        # Clear the reset token after use
        self.reset_token = None
        self.reset_token_expiration = None
        db.session.commit()
    def get_notification_preferences(self):
        """Get notification preferences with defaults for missing values"""
        import json
        try:
            # Try to parse stored preferences
            if self.notification_preferences:
                prefs = json.loads(self.notification_preferences)
            else:
                prefs = {}
        except:
            prefs = {}
        # Set defaults for missing keys
        if 'enable_email' not in prefs:
            prefs['enable_email'] = True
        if 'email_frequency' not in prefs:
            prefs['email_frequency'] = 'weekly'
        if 'notification_types' not in prefs:
            prefs['notification_types'] = ['overdue', 'due_soon']
        return prefs

class Site(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    machines = db.relationship('Machine', backref='site', lazy=True, cascade="all, delete-orphan")
    enable_notifications = db.Column(db.Boolean, default=False)
    contact_email = db.Column(db.String(100))  # Contact email for notifications
    notification_threshold = db.Column(db.Integer, default=30)  # Days before due date to notify
    def get_parts_status(self, now=None):
        """Return counts of parts by status (overdue, due_soon, ok)"""
        if now is None:
            now = datetime.utcnow()
        overdue_parts = []
        due_soon_parts = []
        ok_parts = []
        for machine in self.machines:
            for part in machine.parts:
                days_until = (part.next_maintenance - now).days
                if days_until < 0:
                    overdue_parts.append(part)
                elif days_until <= self.notification_threshold:
                    due_soon_parts.append(part)
                else:
                    ok_parts.append(part)
        return {
            'overdue': overdue_parts,
            'due_soon': due_soon_parts,
            'ok': ok_parts,
        }

class Machine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100))
    site_id = db.Column(db.Integer, db.ForeignKey('site.id'), nullable=False)
    parts = db.relationship('Part', backref='machine', lazy=True, cascade="all, delete-orphan")
    machine_number = db.Column(db.String(100))  # New column for machine number
    serial_number = db.Column(db.String(100))  # New column for serial number
    maintenance_logs = db.relationship('MaintenanceLog', backref='machine', lazy=True, cascade="all, delete-orphan")

class Part(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)
    maintenance_frequency = db.Column(db.Integer, default=7)  # in days
    maintenance_unit = db.Column(db.String(10), default='day')  # 'day', 'week', 'month', or 'year'
    last_maintenance = db.Column(db.DateTime, default=datetime.utcnow)
    next_maintenance = db.Column(db.DateTime)
    notification_sent = db.Column(db.Boolean, default=False)  # Track if notification has been sent
    last_maintained_by = db.Column(db.String(100))  # New field for who performed maintenance
    invoice_number = db.Column(db.String(50))  # New field for invoice tracking
    def __init__(self, **kwargs):
        # Extract frequency and unit if provided
        frequency = kwargs.get('maintenance_frequency', 7)
        unit = kwargs.get('maintenance_unit', 'day')
        # Convert to days for internal storage
        if 'maintenance_frequency' in kwargs and 'maintenance_unit' in kwargs:
            kwargs['maintenance_frequency'] = self.convert_to_days(frequency, unit)
        super(Part, self).__init__(**kwargs)
        if 'maintenance_frequency' in kwargs and 'last_maintenance' in kwargs:
            self.update_next_maintenance()
    def update_next_maintenance(self):
        """Update next maintenance date and reset notification status"""
        self.next_maintenance = self.last_maintenance + timedelta(days=self.maintenance_frequency)
        self.notification_sent = False  # Reset notification status when maintenance is done
    @staticmethod
    def convert_to_days(value, unit):
        """Convert a value from specified unit to days"""
        value = int(value)
        if unit == 'day':
            return value
        elif unit == 'week':
            return value * 7
        elif unit == 'month':
            return value * 30
        elif unit == 'year':
            return value * 365
        else:
            return value  # Default to days
    def get_frequency_display(self):
        """Return a human-readable frequency with appropriate unit"""
        days = self.maintenance_frequency
        if days % 365 == 0 and days >= 365:
            return f"{days // 365} {'year' if days // 365 == 1 else 'years'}"
        elif days % 30 == 0 and days >= 30:
            return f"{days // 30} {'month' if days // 30 == 1 else 'months'}"
        elif days % 7 == 0 and days >= 7:
            return f"{days // 7} {'week' if days // 7 == 1 else 'weeks'}"
        else:
            return f"{days} {'day' if days == 1 else 'days'}"

class MaintenanceLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)
    part_id = db.Column(db.Integer, db.ForeignKey('part.id'), nullable=False)
    performed_by = db.Column(db.String(100), nullable=False)
    invoice_number = db.Column(db.String(50))
    maintenance_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    # Reference to the part to track which part was maintained
    part = db.relationship('Part', backref='maintenance_logs')

# AFTER all models are defined, THEN create tables
if os.environ.get('RENDER', False):
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created/verified")
            
            # Check if any users exist, if not create an admin user
            user_count = db.session.query(db.func.count(User.id)).scalar()
            print(f"Found {user_count} users in database")
            
            if user_count == 0:
                print("No users found - creating default admin account")
                
                # Create admin role first
                admin_role = Role(
                    name='Administrator', 
                    description='Full system access',
                    permissions=','.join([
                        Permissions.ADMIN_FULL,
                        Permissions.SITES_VIEW, 
                        Permissions.SITES_CREATE,
                        Permissions.SITES_EDIT,
                        Permissions.SITES_DELETE,
                        Permissions.MACHINES_VIEW,
                        Permissions.MACHINES_CREATE,
                        Permissions.MACHINES_EDIT,
                        Permissions.MACHINES_DELETE,
                        Permissions.PARTS_VIEW,
                        Permissions.PARTS_CREATE,
                        Permissions.PARTS_EDIT,
                        Permissions.PARTS_DELETE,
                        Permissions.MAINTENANCE_VIEW,
                        Permissions.MAINTENANCE_SCHEDULE,
                        Permissions.MAINTENANCE_RECORD
                    ])
                )
                db.session.add(admin_role)
                db.session.commit()
                
                # Generate a secure password
                import secrets
                admin_password = secrets.token_urlsafe(8)  # 8 char secure random password
                
                # Create admin user
                admin = User(
                    username='admin',
                    full_name='Administrator',
                    email='admin@example.com',
                    is_admin=True,
                    role_id=admin_role.id
                )
                admin.set_password(admin_password)
                db.session.add(admin)
                db.session.commit()
                
                # Print credentials to console
                print("\n" + "="*50)
                print("DEFAULT ADMIN ACCOUNT CREATED")
                print("="*50)
                print(f"Username: admin")
                print(f"Password: {admin_password}")
                print("="*50)
                print("IMPORTANT: Please change this password after logging in!")
                print("="*50 + "\n")
            
        except Exception as e:
            print(f"Error during database initialization: {str(e)}")
            print(traceback.format_exc())  # Print full traceback for debugging

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            # Get the next parameter or default to dashboard
            next_page = request.args.get('next', 'dashboard')
            return redirect(url_for(next_page))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Filter sites based on user access and permissions
    if current_user.is_admin:
        # Admins see all sites
        sites = Site.query.all()
    elif current_user.has_permission(Permissions.SITES_VIEW):
        sites = Site.query.all()
    elif current_user.has_permission(Permissions.SITES_VIEW_ASSIGNED):
        sites = current_user.sites
    else:
        sites = []
    now = datetime.utcnow()
    machines = Machine.query.all()
    return render_template(
        'dashboard.html',
        sites=sites,
        machines=machines,
        now=now,
        is_admin=current_user.is_admin,
        current_user=current_user,
    )

@app.route('/sites', methods=['GET', 'POST'])
@login_required
def manage_sites():
    """Display and manage all sites"""
    # Check permissions
    if not current_user.has_permission(Permissions.SITES_VIEW) and not current_user.is_admin:
        if current_user.has_permission(Permissions.SITES_VIEW_ASSIGNED):
            # User can only view their assigned sites
            sites = current_user.sites
        else:
            flash("You don't have permission to view sites", "error")
            return redirect(url_for('dashboard'))
    else:
        # Admin or users with view permission can see all sites
        sites = Site.query.all()
    
    # Handle form submission for adding a new site
    if request.method == 'POST':
        if not current_user.has_permission(Permissions.SITES_CREATE) and not current_user.is_admin:
            flash("You don't have permission to create sites", "error")
            return redirect(url_for('manage_sites'))
        
        name = request.form.get('name')
        location = request.form.get('location')
        contact_email = request.form.get('contact_email')
        notification_threshold = request.form.get('notification_threshold', 30)
        enable_notifications = 'enable_notifications' in request.form
        
        if not name:
            flash("Site name is required", "error")
        else:
            # Create new site
            new_site = Site(
                name=name,
                location=location,
                contact_email=contact_email,
                notification_threshold=notification_threshold,
                enable_notifications=enable_notifications
            )
            db.session.add(new_site)
            
            # Assign users if provided
            user_ids = request.form.getlist('user_ids')
            if user_ids:
                for user_id in user_ids:
                    user = User.query.get(user_id)
                    if user:
                        new_site.users.append(user)
            
            db.session.commit()
            flash(f"Site '{name}' has been added successfully", "success")
            return redirect(url_for('manage_sites'))
    
    # Get users for site assignment
    users = User.query.all() if current_user.is_admin else []
    
    return render_template('sites.html', 
                          sites=sites, 
                          users=users,
                          now=datetime.utcnow(),
                          is_admin=current_user.is_admin,
                          can_create=current_user.has_permission(Permissions.SITES_CREATE) or current_user.is_admin,
                          can_edit=current_user.has_permission(Permissions.SITES_EDIT) or current_user.is_admin,
                          can_delete=current_user.has_permission(Permissions.SITES_DELETE) or current_user.is_admin)

@app.route('/sites/<int:site_id>/delete', methods=['POST'])
@login_required
def delete_site(site_id):
    """Delete a site"""
    if not current_user.has_permission(Permissions.SITES_DELETE) and not current_user.is_admin:
        flash("You don't have permission to delete sites", "error")
        return redirect(url_for('manage_sites'))
    
    site = Site.query.get_or_404(site_id)
    site_name = site.name
    
    # Delete the site and all related data due to cascade
    db.session.delete(site)
    db.session.commit()
    
    flash(f"Site '{site_name}' has been deleted", "success")
    return redirect(url_for('manage_sites'))

@app.route('/sites/<int:site_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_site(site_id):
    """Edit an existing site"""
    site = Site.query.get_or_404(site_id)
    
    # Check permissions
    if not current_user.has_permission(Permissions.SITES_EDIT) and not current_user.is_admin:
        flash("You don't have permission to edit sites", "error")
        return redirect(url_for('manage_sites'))
    
    if request.method == 'POST':
        site.name = request.form.get('name')
        site.location = request.form.get('location')
        site.contact_email = request.form.get('contact_email')
        site.notification_threshold = request.form.get('notification_threshold', 30)
        site.enable_notifications = 'enable_notifications' in request.form
        
        # Update assigned users if admin
        if current_user.is_admin:
            site.users = []  # Clear existing associations
            user_ids = request.form.getlist('user_ids')
            for user_id in user_ids:
                user = User.query.get(user_id)
                if user:
                    site.users.append(user)
        
        db.session.commit()
        flash(f"Site '{site.name}' has been updated", "success")
        return redirect(url_for('manage_sites'))
    
    users = User.query.all() if current_user.is_admin else []
    return render_template('edit_site.html', site=site, users=users, is_admin=current_user.is_admin)

@app.route('/machines', methods=['GET', 'POST'])
@login_required
def manage_machines():
    """Display and manage all machines"""
    # Check permissions
    if not current_user.has_permission(Permissions.MACHINES_VIEW) and not current_user.is_admin:
        flash("You don't have permission to view machines", "error")
        return redirect(url_for('dashboard'))
        
    # Get all machines, optionally filtered by site
    site_id = request.args.get('site_id', type=int)
    if site_id:
        machines = Machine.query.filter_by(site_id=site_id).all()
        site = Site.query.get_or_404(site_id)
        title = f"Machines at {site.name}"
    else:
        machines = Machine.query.all()
        title = "All Machines"
    
    # ...existing code...

@app.route('/parts', methods=['GET', 'POST'])
@login_required
def manage_parts():
    """Display and manage all parts"""
    # ...existing code...

@app.route('/profile')
@login_required
def user_profile():
    """User profile page"""
    return render_template('profile.html', 
                          user=current_user)

@app.route('/admin')
@login_required
@admin_required
def admin():
    """Admin dashboard page"""
    # Get counts for admin dashboard
    user_count = User.query.count()
    site_count = Site.query.count()
    machine_count = Machine.query.count()
    part_count = Part.query.count()
    users = User.query.all() if current_user.is_admin else []
    return render_template('admin.html', 
                          user_count=user_count,
                          site_count=site_count,
                          machine_count=machine_count,
                          part_count=part_count)

@app.route('/admin/users')
@login_required
@admin_required
def manage_users():
    """User management page for admins"""
    users = User.query.all()
    roles = Role.query.all()
    sites = Site.query.all()
    return render_template('admin_users.html', users=users, roles=roles, sites=sites)

@app.route('/admin/users/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    """Add a new user"""
    username = request.form.get('username')
    email = request.form.get('email')
    full_name = request.form.get('full_name')
    role_id = request.form.get('role_id')
    is_admin = 'is_admin' in request.form
    password = secrets.token_urlsafe(8)  # Generate random initial password
    # Validate input
    if User.query.filter_by(username=username).first():
        flash(f"Username '{username}' already exists", "error")
        return redirect(url_for('manage_users'))
    if not username or not email:
        flash("Username and email are required", "error")
        return redirect(url_for('manage_users'))
    # Create new user
    user = User(
        username=username,
        email=email,
        full_name=full_name,
        role_id=role_id,
        is_admin=is_admin,
    )
    user.set_password(password)
    # Add user to selected sites
    site_ids = request.form.getlist('site_ids')
    for site_id in site_ids:
        site = Site.query.get(site_id)
        if site:
            user.sites.append(site)
    db.session.add(user)
    db.session.commit()
    flash(f"User '{username}' has been created with temporary password: {password}", "success")
    return redirect(url_for('manage_users'))

@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit a user"""
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.full_name = request.form.get('full_name')
        user.role_id = request.form.get('role_id')
        user.is_admin = 'is_admin' in request.form
        
        # Reset password if requested
        if 'reset_password' in request.form:
            new_password = secrets.token_urlsafe(8)
            user.set_password(new_password)
            flash(f"Password has been reset to: {new_password}", "success")
        
        # Update site assignments
        user.sites = []  # Clear existing associations
        site_ids = request.form.getlist('site_ids')
        for site_id in site_ids:
            site = Site.query.get(site_id)
            if site:
                user.sites.append(site)
        db.session.commit()
        flash(f"User '{user.username}' has been updated", "success")
        return redirect(url_for('manage_users'))
    roles