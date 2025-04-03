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

@app.route('/machines') methods=['GET', 'POST'])
@login_required
def manage_machines():
    """Display and manage all machines"""
    # Similar permission check as sites
    if current_user.is_admin or current_user.has_permission(Permissions.MACHINES_VIEW):is_admin:
        # Get all machines, optionally filtered by sitees", "error")
        site_id = request.args.get('site_id', type=int)
        if site_id:
            machines = Machine.query.filter_by(site_id=site_id).all()
            site = Site.query.get_or_404(site_id)t)
            title = f"Machines at {site.name}"
        else:nes = Machine.query.filter_by(site_id=site_id).all()
            machines = Machine.query.all()id)
            title = "All Machines"e.name}"
    else:
        flash("You don't have permission to view machines", "error")
        return redirect(url_for('dashboard'))
    return render_template('machines.html', 
                          machines=machines,w machine
                          title=title,
                          is_admin=current_user.is_admin,CHINES_CREATE) and not current_user.is_admin:
                          can_create=current_user.has_permission(Permissions.MACHINES_CREATE) or current_user.is_admin,
                          can_edit=current_user.has_permission(Permissions.MACHINES_EDIT) or current_user.is_admin,
                          can_delete=current_user.has_permission(Permissions.MACHINES_DELETE) or current_user.is_admin)
        name = request.form.get('name')
@app.route('/parts') methods=['GET', 'POST'])est.form.get('model')
@login_required_number = request.form.get('machine_number')
def manage_parts():er = request.form.get('serial_number')
    """Display and manage all parts"""te_id')
    # Similar permission check as machines
    if current_user.is_admin or current_user.has_permission(Permissions.PARTS_VIEW):is_admin:
        # Get all parts, optionally filtered by machine, "error") "error")
        machine_id = request.args.get('machine_id', type=int)
        if machine_id:
            parts = Part.query.filter_by(machine_id=machine_id).all()
            machine = Machine.query.get_or_404(machine_id)
            title = f"Parts for {machine.name}"
        else: = Part.query.filter_by(machine_id=machine_id).all()   machine_number=machine_number,
            parts = Part.query.all()or_404(machine_id)_number,
            title = "All Parts"chine.name}"
    else:   )
        flash("You don't have permission to view parts", "error")
        return redirect(url_for('dashboard'))
    return render_template('parts.html', 
                          parts=parts,g a new partas been added successfully", "success")
                          title=title,machines', site_id=site_id))
                          now=datetime.utcnow(),ssions.PARTS_CREATE) and not current_user.is_admin:
                          is_admin=current_user.is_admin,rts", "error")
                          can_create=current_user.has_permission(Permissions.PARTS_CREATE) or current_user.is_admin,
                          can_edit=current_user.has_permission(Permissions.PARTS_EDIT) or current_user.is_admin,
                          can_delete=current_user.has_permission(Permissions.PARTS_DELETE) or current_user.is_admin)
        description = request.form.get('description')                          machines=machines,
@app.route('/profile')equest.form.get('machine_id')    sites=sites,
@login_requiredance_frequency = request.form.get('maintenance_frequency')           title=title,
def user_profile():_unit = request.form.get('maintenance_unit')       site_id=site_id if site_id else None,
    """User profile page"""r.is_admin,
    return render_template('profile.html', r.has_permission(Permissions.MACHINES_CREATE) or current_user.is_admin,
                          user=current_user) required", "error")ser.has_permission(Permissions.MACHINES_EDIT) or current_user.is_admin,
        else:                          can_delete=current_user.has_permission(Permissions.MACHINES_DELETE) or current_user.is_admin)
@app.route('/admin') new part
@login_required_part = Part(chines/<int:machine_id>/edit', methods=['GET', 'POST'])
@admin_required name=name,
def admin():    description=description,hine(machine_id):
    """Admin dashboard page"""hine_id,e"""
    # Get counts for admin dashboardy=maintenance_frequency,04(machine_id)
    user_count = User.query.count()intenance_unit,
    site_count = Site.query.count()tetime.utcnow()
    machine_count = Machine.query.count() not current_user.is_admin:
    part_count = Part.query.count())ssion to edit machines", "error")
    users = User.query.all() if current_user.is_admin else []
    return render_template('admin.html', 
                          user_count=user_count, successfully", "success")
                          site_count=site_count,s', machine_id=machine_id))
                          machine_count=machine_count,
                          part_count=part_count)ine_number')
    machines = Machine.query.all()        machine.serial_number = request.form.get('serial_number')
@app.route('/admin/users')_id')
@login_requireder_template('parts.html', 
@admin_required           parts=parts,ion.commit()
def manage_users():       machines=machines,hine '{machine.name}' has been updated", "success")
    """User management page for admins"""ines', site_id=machine.site_id))
    users = User.query.all()w=datetime.utcnow(),
    roles = Role.query.all()chine_id=machine_id if machine_id else None,
    sites = Site.query.all()_admin=current_user.is_admin,edit_machine.html', machine=machine, sites=sites, is_admin=current_user.is_admin)
    return render_template('admin_users.html', users=users, roles=roles, sites=sites)EATE) or current_user.is_admin,
                          can_edit=current_user.has_permission(Permissions.PARTS_EDIT) or current_user.is_admin,@app.route('/machines/<int:machine_id>/delete', methods=['POST'])
@app.route('/admin/users/add', methods=['POST'])r.has_permission(Permissions.PARTS_DELETE) or current_user.is_admin)
@login_required:
@admin_requiredrts/<int:part_id>/edit', methods=['GET', 'POST']) machine"""
def add_user():ent_user.has_permission(Permissions.MACHINES_DELETE) and not current_user.is_admin:
    """Add a new user"""have permission to delete machines", "error")
    username = request.form.get('username')
    email = request.form.get('email')_id)
    full_name = request.form.get('full_name')
    role_id = request.form.get('role_id')
    is_admin = 'is_admin' in request.formrmissions.PARTS_EDIT) and not current_user.is_admin:
    password = secrets.token_urlsafe(8)  # Generate random initial password
        return redirect(url_for('manage_parts'))db.session.delete(machine)
    # Validate input
    if User.query.filter_by(username=username).first():
        flash(f"Username '{username}' already exists", "error")
        return redirect(url_for('manage_users'))cription')ite_id=site_id)
        part.machine_id = request.form.get('machine_id')
    if not username or not email:
        flash("Username and email are required", "error")
        return redirect(url_for('manage_users'))nance_frequency')
        new_unit = request.form.get('maintenance_unit')"""Display and manage all parts"""
    # Create new userncy and new_unit:ion check as machines
    user = User( = Part.convert_to_days(new_frequency, new_unit)ser.is_admin or current_user.has_permission(Permissions.PARTS_VIEW):
        username=username,ce_frequency = daysptionally filtered by machine
        email=email,ate_next_maintenance() request.args.get('machine_id', type=int)
        full_name=full_name,
        role_id=role_id,t().query.filter_by(machine_id=machine_id).all()
        is_admin=is_admin,t.name}' has been updated", "success")ine.query.get_or_404(machine_id)
    )   return redirect(url_for('manage_parts', machine_id=part.machine_id))       title = f"Parts for {machine.name}"
    user.set_password(password)
    machines = Machine.query.all()        parts = Part.query.all()
    # Add user to selected sites_part.html', part=part, machines=machines, is_admin=current_user.is_admin)
    site_ids = request.form.getlist('site_ids')
    for site_id in site_ids:_id>/delete', methods=['POST'])e permission to view parts", "error")
        site = Site.query.get(site_id)
        if site:part_id):r_template('parts.html', 
            user.sites.append(site)
    if not current_user.has_permission(Permissions.PARTS_DELETE) and not current_user.is_admin:                      title=title,
    db.session.add(user) have permission to delete parts", "error")  now=datetime.utcnow(),
    db.session.commit()(url_for('manage_parts'))   is_admin=current_user.is_admin,
    flash(f"User '{username}' has been created with temporary password: {password}", "success")
    return redirect(url_for('manage_users')).has_permission(Permissions.PARTS_EDIT) or current_user.is_admin,
    machine_id = part.machine_id                          can_delete=current_user.has_permission(Permissions.PARTS_DELETE) or current_user.is_admin)
@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_requireddelete(part)
def edit_user(user_id):
    """Edit a user"""
    user = User.query.get_or_404(user_id)eleted", "success"), 
    return redirect(url_for('manage_parts', machine_id=machine_id))                      user=current_user)
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.full_name = request.form.get('full_name')
        user.role_id = request.form.get('role_id')
        user.is_admin = 'is_admin' in request.form
                          user=current_user)t counts for admin dashboard
        # Reset password if requested
        if 'reset_password' in request.form:
            new_password = secrets.token_urlsafe(8)
            user.set_password(new_password)
            flash(f"Password has been reset to: {new_password}", "success")
        dmin dashboard page"""rn render_template('admin.html', 
        # Update site assignmentsardunt=user_count,
        user.sites = []  # Clear existing associations
        site_ids = request.form.getlist('site_ids')
        for site_id in site_ids:y.count()ount=part_count)
            site = Site.query.get(site_id)
            if site:ry.all() if current_user.is_admin else []sers')
                user.sites.append(site), 
                          user_count=user_count,equired
        db.session.commit()ite_count=site_count,
        flash(f"User '{user.username}' has been updated", "success")
        return redirect(url_for('manage_users'))
    s = Role.query.all()
    roles = Role.query.all()
    sites = Site.query.all()tml', users=users, roles=roles, sites=sites)
    return render_template('edit_user.html', user=user, roles=roles, sites=sites)
def manage_users():@app.route('/admin/users/add', methods=['POST'])
@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_requiredr.query.all()
@admin_requirede.query.all()
def delete_user(user_id):l()
    """Delete a user"""ate('admin_users.html', users=users, roles=roles, sites=sites)form.get('username')
    user = User.query.get_or_404(user_id)
    .route('/admin/users/add', methods=['POST'])full_name = request.form.get('full_name')
    # Prevent deleting self')
    if user.id == current_user.id:
        flash("You cannot delete your own account", "error")
        return redirect(url_for('manage_users'))
    username = request.form.get('username')# Validate input
    username = user.username('email')username=username).first():
    db.session.delete(user)m.get('full_name')username}' already exists", "error")
    db.session.commit()orm.get('role_id')(url_for('manage_users'))
    flash(f"User '{username}' has been deleted", "success")
    return redirect(url_for('manage_users'))enerate random initial password
            flash("Username and email are required", "error")
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():er_by(username=username).first():
    if current_user.is_authenticated: already exists", "error")
        return redirect(url_for('dashboard'))'))
    if request.method == 'POST':
        email = request.form.get('email')
        # Find user by emailemail are required", "error")sions.get_all_permissions()
        user = User.query.filter_by(email=email).first()permissions=all_permissions)
        if user:
            # Generate reset token)
            token = user.generate_reset_token()
            # Build reset URL
            reset_url = url_for('reset_password', user_id=user.id, token=token, _external=True)
            # Create emaile,getlist('site_ids')
            subject = "Password Reset Request"
            html_body = f""".get('description')t(site_id)
            <h1>Password Reset Request</h1>
            <p>Hello {user.full_name or user.username},</p>
            <p>You requested to reset your password. Please click the link below to reset your password:</p>
            <p><a href="{reset_url}">{reset_url}</a></p>
            <p>This link is only valid for 1 hour.</p>
            <p>If you did not request a password reset, please ignore this email.</p>
            """Site.query.get(site_id)r('manage_users'))
            try:
                # Send emaild(site)required", "error")t:user_id>/edit', methods=['GET', 'POST'])
                msg = Message(
                    subject=subject,
                    recipients=[email],
                    html=html_bodybeen created with temporary password: {password}", "success")
                )ct(url_for('manage_users')),uery.get_or_404(user_id)
                mail.send(msg)
                flash("Password reset link has been sent to your email", "success")
            except Exception as e:
                app.logger.error(f"Failed to send password reset email: {str(e)}")
                flash("Failed to send password reset email. Please try again later.", "error")
        else: user"""n.commit()role_id = request.form.get('role_id')
            # Still show success message even if email not found
            # This prevents user enumeration attacks
            flash("If that email is in our system, a password reset link has been sent", "success")
        return redirect(url_for('login'))'username')it', methods=['GET', 'POST'])rm:
    return render_template('forgot_password.html')
        user.full_name = request.form.get('full_name')@admin_required            user.set_password(new_password)
@app.route('/reset-password/<int:user_id>/<token>', methods=['GET', 'POST'])
def reset_password(user_id, token):in request.form
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    # Find useret_password' in request.form:method == 'POST':s = request.form.getlist('site_ids')
    user = User.query.get(user_id).token_urlsafe(8)et('name')
    # Verify user and tokenrd(new_password)request.form.get('description')ry.get(site_id)
    if not user or not user.verify_reset_token(token):assword}", "success")st('permissions'))
        flash("The password reset link is invalid or has expired.", "error")
        return redirect(url_for('forgot_password'))
        user.sites = []  # Clear existing associations    flash(f"Role '{role.name}' has been updated", "success")    db.session.commit()
    if request.method == 'POST':getlist('site_ids')'manage_roles'))name}' has been updated", "success")
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        # Validate passwordrmissions_list())
        if not password or len(password) < 8:ole, all_permissions=all_permissions, role_permissions=role_permissions)
            flash("Password must be at least 8 characters long.", "error")
            return render_template('reset_password.html', user_id=user_id, token=token)
        flash(f"User '{user.username}' has been updated", "success")equiredte('/admin/users/<int:user_id>/delete', methods=['POST'])
        if password != confirm_password:users'))
            flash("Passwords do not match.", "error")
            return render_template('reset_password.html', user_id=user_id, token=token)
        s = Site.query.all() = Role.query.get_or_404(role_id)elete a user"""
        # Update passworde('edit_user.html', user=user, roles=roles, sites=sites)
        user.set_password(password)
        # Clear reset tokennt:user_id>/delete', methods=['POST'])(role_id=role.id).first():
        user.clear_reset_token()because it is assigned to users", "error")d:
        equiredreturn redirect(url_for('manage_roles'))flash("You cannot delete your own account", "error")
        flash("Your password has been successfully reset. You can now log in with your new password.", "success")
        return redirect(url_for('login'))
    user = User.query.get_or_404(user_id)db.session.delete(role)username = user.username
    return render_template('reset_password.html', user_id=user_id, token=token)
    # Prevent deleting self        db.session.commit()
@app.route('/admin/backup')ser.id:e}' has been deleted", "success")}' has been deleted", "success")
@login_required"You cannot delete your own account", "error")irect(url_for('manage_roles'))irect(url_for('manage_users'))
@admin_required
def manage_backups():hods=['GET', 'POST'])-password', methods=['GET', 'POST'])
    """Backup management page for admins"""
    # Get database pathlete(user)er.is_authenticated:er.is_authenticated:
    if os.environ.get('RENDER'):dashboard'))for('dashboard'))
        if os.environ.get('RENDER_MOUNT_PATH'):
            data_dir = os.environ.get('RENDER_MOUNT_PATH')
        else:
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance'), methods=['GET', 'POST'])ter_by(email=email).first()ter_by(email=email).first()
        db_path = os.path.join(data_dir, 'maintenance.db')
    else:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'maintenance.db')_for('dashboard'))nerate_reset_token()nerate_reset_token()
    equest.method == 'POST':    # Build reset URL    # Build reset URL
    # Get backup directory _external=True)er.id, token=token, _external=True)
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups') emailmailmail
    os.makedirs(backup_dir, exist_ok=True)
    
    # Get list of existing backups
    backups = []rate_reset_token()ll_name or user.username},</p>ll_name or user.username},</p>
    if os.path.exists(backup_dir):RLd to reset your password. Please click the link below to reset your password:</p>d to reset your password. Please click the link below to reset your password:</p>
        for file in os.listdir(backup_dir):, _external=True)
            if file.endswith('.db'):alid for 1 hour.</p>ly valid for 1 hour.</p>
                file_path = os.path.join(backup_dir, file)Request"a password reset, please ignore this email.</p>a password reset, please ignore this email.</p>
                backup_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                file_size = os.path.getsize(file_path)
                backups.append({ser.full_name or user.username},</p>emailemail
                    'filename': file,your password:</p>
                    'timestamp': backup_time,    <p><a href="{reset_url}">{reset_url}</a></p>            subject=subject,            subject=subject,
                    'size': file_sizer 1 hour.</p>
                }) request a password reset, please ignore this email.</p>_body_body
                """                )                )
    # Sort backups by timestamp (newest first)
    backups = sorted(backups, key=lambda x: x['timestamp'], reverse=True)d email("Password reset link has been sent to your email", "success")("Password reset link has been sent to your email", "success")
    e( as e: as e:
    return render_template('admin_backup.html', backups=backups, db_path=db_path)ssword reset email: {str(e)}") send password reset email: {str(e)}")
,password reset email. Please try again later.", "error")password reset email. Please try again later.", "error")




















































































































































    app.run(host='0.0.0.0', port=port)    port = int(os.environ.get('PORT', 5050))    ensure_email_templates()    ensure_env_file()if __name__ == '__main__':        # ...existing code...        # Continue with other sample data                print("\nIMPORTANT: Please change this password immediately after first login!\n")        print("=" * 40)        print(f"Password: {admin_password}")        print(f"Username: admin")        print("ADMIN ACCOUNT CREATED")        print("\n" + "=" * 40)        # Display the generated password to console only during initialization        db.session.commit()        db.session.add(admin)        admin.set_password(admin_password)        admin = User(username='admin', full_name='Administrator', email='admin@example.com', is_admin=True, role_id=admin_role.id)        admin_password = secrets.token_urlsafe(12)  # Generate secure random password        import secrets        # Create admin user with randomly generated password                db.session.commit()        db.session.add_all([admin_role, manager_role, technician_role])        # ...existing code for other roles...                          ]))                              # ...existing permissions...                          permissions=','.join([        admin_role = Role(name='Administrator', description='Full system access',        # Create roles first    if not admin:    admin = User.query.filter_by(username='admin').first()    db.create_all()    """Initialize the database with sample data."""def init_db():@app.cli.command("init-db")    return redirect(url_for('manage_backups'))            flash(f"Error deleting backup: {str(e)}", "error")    except Exception as e:        flash("Backup deleted successfully", "success")        os.remove(backup_path)        # Delete backup file    try:            return redirect(url_for('manage_backups'))        flash("Backup file not found", "error")    if not os.path.exists(backup_path):    # Check if backup exists        backup_path = os.path.join(backup_dir, filename)    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')    """Delete a database backup"""def delete_backup(filename):@admin_required@login_required@app.route('/admin/backup/delete/<filename>', methods=['POST'])    return redirect(url_for('manage_backups'))            flash(f"Error restoring backup: {str(e)}", "error")    except Exception as e:        flash("Backup restored successfully. Please restart the application for changes to take effect.", "success")        shutil.copy2(backup_path, db_path)        # Restore backup                    shutil.copy2(db_path, current_backup_path)        if os.path.exists(db_path):        current_backup_path = os.path.join(backup_dir, f"maintenance_auto_backup_before_restore_{timestamp}.db")        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")        # Create a backup of current database before restoring    try:            return redirect(url_for('manage_backups'))        flash("Backup file not found", "error")    if not os.path.exists(backup_path):    # Check if backup exists        backup_path = os.path.join(backup_dir, filename)    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')    # Get backup file path            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'maintenance.db')    else:        db_path = os.path.join(data_dir, 'maintenance.db')            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')        else:            data_dir = os.environ.get('RENDER_MOUNT_PATH')        if os.environ.get('RENDER_MOUNT_PATH'):    if os.environ.get('RENDER'):    # Get database path        import shutil    """Restore a database backup"""def restore_backup(filename):@admin_required@login_required@app.route('/admin/backup/restore/<filename>', methods=['POST'])    return send_file(os.path.join(backup_dir, filename), as_attachment=True)    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')    """Download a database backup"""def download_backup(filename):@admin_required@login_required@app.route('/admin/backup/download/<filename>')    return redirect(url_for('manage_backups'))            flash(f"Error creating backup: {str(e)}", "error")    except Exception as e:        flash("Backup created successfully", "success")        shutil.copy2(db_path, backup_path)        # Copy database file    try:        backup_path = os.path.join(backup_dir, f"maintenance_backup_{timestamp}.db")    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")    # Create backup with timestamp        os.makedirs(backup_dir, exist_ok=True)    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')    # Get backup directory            return redirect(url_for('manage_backups'))        flash("Database file not found", "error")    if not os.path.exists(db_path):    # Check if database exists            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'maintenance.db')    else:        db_path = os.path.join(data_dir, 'maintenance.db')            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')        else:            data_dir = os.environ.get('RENDER_MOUNT_PATH')        if os.environ.get('RENDER_MOUNT_PATH'):    if os.environ.get('RENDER'):    # Get database path        import shutil    """Create a database backup"""def create_backup():@admin_required@login_required@app.route('/admin/backup/create', methods=['POST'])




















































































    app.run(host='0.0.0.0', port=port)    port = int(os.environ.get('PORT', 5050))    ensure_email_templates()    ensure_env_file()if __name__ == '__main__':        # ...existing code...        # Continue with other sample data                print("\nIMPORTANT: Please change this password immediately after first login!\n")        print("=" * 40)        print(f"Password: {admin_password}")        print(f"Username: admin")        print("ADMIN ACCOUNT CREATED")        print("\n" + "=" * 40)        # Display the generated password to console only during initialization        db.session.commit()        db.session.add(admin)        admin.set_password(admin_password)        admin = User(username='admin', full_name='Administrator', email='admin@example.com', is_admin=True, role_id=admin_role.id)        admin_password = secrets.token_urlsafe(12)  # Generate secure random password        import secrets        # Create admin user with randomly generated password                db.session.commit()        db.session.add_all([admin_role, manager_role, technician_role])        # ...existing code for other roles...                          ]))                              # ...existing permissions...                          permissions=','.join([        admin_role = Role(name='Administrator', description='Full system access',        # Create roles first    if not admin:    admin = User.query.filter_by(username='admin').first()    db.create_all()    """Initialize the database with sample data."""def init_db():@app.cli.command("init-db")    return render_template('reset_password.html', user_id=user_id, token=token)            return redirect(url_for('login'))        flash("Your password has been successfully reset. You can now log in with your new password.", "success")                user.clear_reset_token()        # Clear reset token        user.set_password(password)        # Update password                    return render_template('reset_password.html', user_id=user_id, token=token)            flash("Passwords do not match.", "error")        if password != confirm_password:                    return render_template('reset_password.html', user_id=user_id, token=token)            flash("Password must be at least 8 characters long.", "error")        if not password or len(password) < 8:        # Validate password        confirm_password = request.form.get('confirm_password')        password = request.form.get('password')    if request.method == 'POST':            return redirect(url_for('forgot_password'))        flash("The password reset link is invalid or has expired.", "error")    if not user or not user.verify_reset_token(token):    # Verify user and token    user = User.query.get(user_id)    # Find user        return redirect(url_for('dashboard'))    if current_user.is_authenticated:def reset_password(user_id, token):@app.route('/reset-password/<int:user_id>/<token>', methods=['GET', 'POST'])    return render_template('forgot_password.html')        return redirect(url_for('login'))            flash("If that email is in our system, a password reset link has been sent", "success")            # This prevents user enumeration attacks            # Still show success message even if email not found        else:                flash("Failed to send password reset email. Please try again later.", "error")                app.logger.error(f"Failed to send password reset email: {str(e)}")            except Exception as e:                flash("Password reset link has been sent to your email", "success")                mail.send(msg)                )                    html=html_body













































































    app.run(host='0.0.0.0', port=port)    port = int(os.environ.get('PORT', 5050))    ensure_email_templates()    ensure_env_file()if __name__ == '__main__':        # ...existing code...        # Continue with other sample data                print("\nIMPORTANT: Please change this password immediately after first login!\n")        print("=" * 40)        print(f"Password: {admin_password}")        print(f"Username: admin")        print("ADMIN ACCOUNT CREATED")        print("\n" + "=" * 40)        # Display the generated password to console only during initialization        db.session.commit()        db.session.add(admin)        admin.set_password(admin_password)        admin = User(username='admin', full_name='Administrator', email='admin@example.com', is_admin=True, role_id=admin_role.id)        admin_password = secrets.token_urlsafe(12)  # Generate secure random password        import secrets        # Create admin user with randomly generated password                db.session.commit()        db.session.add_all([admin_role, manager_role, technician_role])        # ...existing code for other roles...                          ]))                              # ...existing permissions...                          permissions=','.join([        admin_role = Role(name='Administrator', description='Full system access',        # Create roles first    if not admin:    admin = User.query.filter_by(username='admin').first()    db.create_all()    """Initialize the database with sample data."""def init_db():@app.cli.command("init-db")    return render_template('reset_password.html', user_id=user_id, token=token)            return redirect(url_for('login'))        flash("Your password has been successfully reset. You can now log in with your new password.", "success")                user.clear_reset_token()        # Clear reset token        user.set_password(password)        # Update password                    return render_template('reset_password.html', user_id=user_id, token=token)            flash("Passwords do not match.", "error")        if password != confirm_password:                    return render_template('reset_password.html', user_id=user_id, token=token)            flash("Password must be at least 8 characters long.", "error")        if not password or len(password) < 8:        # Validate password        confirm_password = request.form.get('confirm_password')        password = request.form.get('password')    if request.method == 'POST':            return redirect(url_for('forgot_password'))        flash("The password reset link is invalid or has expired.", "error")    if not user or not user.verify_reset_token(token):    # Verify user and token    user = User.query.get(user_id)    # Find user        return redirect(url_for('dashboard'))    if current_user.is_authenticated:def reset_password(user_id, token):@app.route('/reset-password/<int:user_id>/<token>', methods=['GET', 'POST'])    return render_template('forgot_password.html')        return redirect(url_for('login'))            flash("If that email is in our system, a password reset link has been sent", "success")            # This prevents user enumeration attacks            # Still show success message even if email not found        else:        else:
            # Still show success message even if email not found
            # This prevents user enumeration attacks
            flash("If that email is in our system, a password reset link has been sent", "success")
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/reset-password/<int:user_id>/<token>', methods=['GET', 'POST'])
def reset_password(user_id, token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    # Find user
    user = User.query.get(user_id)
    # Verify user and token
    if not user or not user.verify_reset_token(token):
        flash("The password reset link is invalid or has expired.", "error")
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        # Validate password
        if not password or len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return render_template('reset_password.html', user_id=user_id, token=token)
        
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template('reset_password.html', user_id=user_id, token=token)
        
        # Update password
        user.set_password(password)
        # Clear reset token
        user.clear_reset_token()
        
        flash("Your password has been successfully reset. You can now log in with your new password.", "success")
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', user_id=user_id, token=token)

@app.cli.command("init-db")
def init_db():
    """Initialize the database with sample data."""
    db.create_all()
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        # Create roles first
        admin_role = Role(name='Administrator', description='Full system access',
                          permissions=','.join([
                              # ...existing permissions...
                          ]))
        # ...existing code for other roles...
        db.session.add_all([admin_role, manager_role, technician_role])
        db.session.commit()
        
        # Create admin user with randomly generated password
        import secrets
        admin_password = secrets.token_urlsafe(12)  # Generate secure random password
        admin = User(username='admin', full_name='Administrator', email='admin@example.com', is_admin=True, role_id=admin_role.id)
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        # Display the generated password to console only during initialization
        print("\n" + "=" * 40)
        print("ADMIN ACCOUNT CREATED")
        print(f"Username: admin")
        print(f"Password: {admin_password}")
        print("=" * 40)
        print("\nIMPORTANT: Please change this password immediately after first login!\n")
        
        # Continue with other sample data
        # ...existing code...

if __name__ == '__main__':
    ensure_env_file()
    ensure_email_templates()
    port = int(os.environ.get('PORT', 5050))
    app.run(host='0.0.0.0', port=port)