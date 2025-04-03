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

@app.route('/sites') methods=['GET', 'POST'])
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
    
    return render_template('sites.html',  new site
                          sites=sites, 
                          now=datetime.utcnow(),ssions.SITES_CREATE) and not current_user.is_admin:
                          is_admin=current_user.is_admin,tes", "error")
                          can_create=current_user.has_permission(Permissions.SITES_CREATE) or current_user.is_admin,
                          can_edit=current_user.has_permission(Permissions.SITES_EDIT) or current_user.is_admin,
                          can_delete=current_user.has_permission(Permissions.SITES_DELETE) or current_user.is_admin)
        location = request.form.get('location')
@app.route('/machines') request.form.get('contact_email')
@login_requiredation_threshold = request.form.get('notification_threshold', 30)
def manage_machines():ations = 'enable_notifications' in request.form
    """Display and manage all machines"""
    # Similar permission check as sites
    if current_user.is_admin or current_user.has_permission(Permissions.MACHINES_VIEW):
        # Get all machines, optionally filtered by site
        site_id = request.args.get('site_id', type=int)
        if site_id:e = Site(
            machines = Machine.query.filter_by(site_id=site_id).all()
            site = Site.query.get_or_404(site_id)
            title = f"Machines at {site.name}"
        else:   notification_threshold=notification_threshold,
            machines = Machine.query.all()e_notifications
            title = "All Machines"
    else:   db.session.add(new_site)
        flash("You don't have permission to view machines", "error")
        return redirect(url_for('dashboard'))
            user_ids = request.form.getlist('user_ids')
    return render_template('machines.html', 
                          machines=machines,
                          title=title,get(user_id)
                          is_admin=current_user.is_admin,
                          can_create=current_user.has_permission(Permissions.MACHINES_CREATE) or current_user.is_admin,
                          can_edit=current_user.has_permission(Permissions.MACHINES_EDIT) or current_user.is_admin,
                          can_delete=current_user.has_permission(Permissions.MACHINES_DELETE) or current_user.is_admin)
            flash(f"Site '{name}' has been added successfully", "success")
@app.route('/parts')edirect(url_for('manage_sites'))
@login_required
def manage_parts(): site assignment
    """Display and manage all parts"""t_user.is_admin else []
    # Similar permission check as machines
    if current_user.is_admin or current_user.has_permission(Permissions.PARTS_VIEW):
        # Get all parts, optionally filtered by machine
        machine_id = request.args.get('machine_id', type=int)
        if machine_id:    now=datetime.utcnow(),
            parts = Part.query.filter_by(machine_id=machine_id).all()
            machine = Machine.query.get_or_404(machine_id)ission(Permissions.SITES_CREATE) or current_user.is_admin,
            title = f"Parts for {machine.name}".has_permission(Permissions.SITES_EDIT) or current_user.is_admin,
        else:             can_delete=current_user.has_permission(Permissions.SITES_DELETE) or current_user.is_admin)
            parts = Part.query.all()
            title = "All Parts">/edit', methods=['GET', 'POST'])
    else:quired
        flash("You don't have permission to view parts", "error")
        return redirect(url_for('dashboard'))
    site = Site.query.get_or_404(site_id)
    return render_template('parts.html', 
                          parts=parts,
                          title=title,(Permissions.SITES_EDIT) and not current_user.is_admin:
                          now=datetime.utcnow(), sites", "error")
                          is_admin=current_user.is_admin,
                          can_create=current_user.has_permission(Permissions.PARTS_CREATE) or current_user.is_admin,
                          can_edit=current_user.has_permission(Permissions.PARTS_EDIT) or current_user.is_admin,
                          can_delete=current_user.has_permission(Permissions.PARTS_DELETE) or current_user.is_admin)
        site.location = request.form.get('location')
@app.route('/profile')mail = request.form.get('contact_email')
@login_requiredtification_threshold = request.form.get('notification_threshold', 30)
def user_profile():_notifications = 'enable_notifications' in request.form
    """User profile page"""
    return render_template('profile.html', 
                          user=current_user)
            site.users = []  # Clear existing associations
@app.route('/admin') = request.form.getlist('user_ids')
@login_required user_id in user_ids:
@admin_required user = User.query.get(user_id)
def admin():    if user:
    """Admin dashboard page""".append(user)
    # Get counts for admin dashboard
    user_count = User.query.count()
    site_count = Site.query.count()has been updated", "success")
    machine_count = Machine.query.count()ites'))
    part_count = Part.query.count()
    users = User.query.all() if current_user.is_admin else []
    return render_template('admin.html', l', site=site, users=users)
                          user_count=user_count,
                          site_count=site_count,s=['POST'])
                          machine_count=machine_count,
                          part_count=part_count)
    """Delete a site"""
@app.route('/admin/users')S_DELETE) and not current_user.is_admin:
@login_required't have permission to delete sites", "error")
@admin_requiredge_sites'))
def manage_users():
    """User management page for admins"""(site_id)
    users = User.query.all()
    roles = Role.query.all()
    sites = Site.query.all()e
    return render_template('admin_users.html', users=users, roles=roles, sites=sites)ession.delete(site)
ommit()
@app.route('/admin/users/add', methods=['POST'])
@login_required", "success")
@admin_requiredmanage_sites'))
def add_user():
    """Add a new user"""
    username = request.form.get('username')
    email = request.form.get('email')
    full_name = request.form.get('full_name')
    role_id = request.form.get('role_id')
    is_admin = 'is_admin' in request.form
    password = secrets.token_urlsafe(8)  # Generate random initial password
    )
    # Validate input
    if User.query.filter_by(username=username).first():hines = Machine.query.filter_by(site_id=site_id).all()
        flash(f"Username '{username}' already exists", "error") = Site.query.get_or_404(site_id)
        return redirect(url_for('manage_users'))es at {site.name}"
    
    if not username or not email:.all()
        flash("Username and email are required", "error")
        return redirect(url_for('manage_users'))
    u don't have permission to view machines", "error")
    # Create new userr('dashboard'))
    user = User(
        username=username,es.html', 
        email=email,
        full_name=full_name,
        role_id=role_id,             is_admin=current_user.is_admin,
        is_admin=is_admin(Permissions.MACHINES_CREATE) or current_user.is_admin,
    )permission(Permissions.MACHINES_EDIT) or current_user.is_admin,
    user.set_password(password)rrent_user.is_admin)
    
    # Add user to selected sites
    site_ids = request.form.getlist('site_ids')@login_required
    for site_id in site_ids:
        site = Site.query.get(site_id)"""
        if site:hines
            user.sites.append(site)has_permission(Permissions.PARTS_VIEW):
    ll parts, optionally filtered by machine
    db.session.add(user)get('machine_id', type=int)
    db.session.commit()
    chine_id).all()
    flash(f"User '{username}' has been created with temporary password: {password}", "success")
    return redirect(url_for('manage_users'))
    else:
@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])ll()
@login_required
@admin_required
def edit_user(user_id):ve permission to view parts", "error")
    """Edit a user"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':                  parts=parts,
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.full_name = request.form.get('full_name')
        user.role_id = request.form.get('role_id')                  can_create=current_user.has_permission(Permissions.PARTS_CREATE) or current_user.is_admin,
        user.is_admin = 'is_admin' in request.form can_edit=current_user.has_permission(Permissions.PARTS_EDIT) or current_user.is_admin,
        e=current_user.has_permission(Permissions.PARTS_DELETE) or current_user.is_admin)
        # Reset password if requested
        if 'reset_password' in request.form:
            new_password = secrets.token_urlsafe(8)equired
            user.set_password(new_password)
            flash(f"Password has been reset to: {new_password}", "success")
        return render_template('profile.html', 
        # Update site assignments
        user.sites = []  # Clear existing associations
        site_ids = request.form.getlist('site_ids')
        for site_id in site_ids:d
            site = Site.query.get(site_id)
            if site:
                user.sites.append(site)
        for admin dashboard
        db.session.commit()count()
        flash(f"User '{user.username}' has been updated", "success")
        return redirect(url_for('manage_users'))
    
    roles = Role.query.all()
    sites = Site.query.all()
    return render_template('edit_user.html', user=user, roles=roles, sites=sites)
ite_count=site_count,
@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])                  machine_count=machine_count,
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user"""
    user = User.query.get_or_404(user_id)
    or('dashboard'))
    # Prevent deleting selfOST':
    if user.id == current_user.id:
        flash("You cannot delete your own account", "error")
        return redirect(url_for('manage_users'))ail=email).first()
    
    username = user.username
    db.session.delete(user)reset token
    db.session.commit()
        # Build reset URL
    flash(f"User '{username}' has been deleted", "success")ssword', user_id=user.id, token=token, _external=True)
    return redirect(url_for('manage_users'))
            subject = "Password Reset Request"
@app.route('/forgot-password', methods=['GET', 'POST'])""
def forgot_password():ord Reset Request</h1>
    if current_user.is_authenticated:ull_name or user.username},</p>
        return redirect(url_for('dashboard'))assword. Please click the link below to reset your password:</p>
    if request.method == 'POST':reset_url}</a></p>













































































































    app.run(host='0.0.0.0', port=port)    port = int(os.environ.get('PORT', 5050))    ensure_email_templates()    ensure_env_file()if __name__ == '__main__':        # ...existing code...        # Continue with other sample data                print("\nIMPORTANT: Please change this password immediately after first login!\n")        print("=" * 40)        print(f"Password: {admin_password}")        print(f"Username: admin")        print("ADMIN ACCOUNT CREATED")        print("\n" + "=" * 40)        # Display the generated password to console only during initialization        db.session.commit()        db.session.add(admin)        admin.set_password(admin_password)        admin = User(username='admin', full_name='Administrator', email='admin@example.com', is_admin=True, role_id=admin_role.id)        admin_password = secrets.token_urlsafe(12)  # Generate secure random password        import secrets        # Create admin user with randomly generated password                db.session.commit()        db.session.add_all([admin_role, manager_role, technician_role])        # ...existing code for other roles...                          ]))                              # ...existing permissions...                          permissions=','.join([        admin_role = Role(name='Administrator', description='Full system access',        # Create roles first    if not admin:    admin = User.query.filter_by(username='admin').first()    db.create_all()    """Initialize the database with sample data."""def init_db():@app.cli.command("init-db")    return render_template('reset_password.html', user_id=user_id, token=token)            return redirect(url_for('login'))        flash("Your password has been successfully reset. You can now log in with your new password.", "success")                user.clear_reset_token()        # Clear reset token        user.set_password(password)        # Update password                    return render_template('reset_password.html', user_id=user_id, token=token)            flash("Passwords do not match.", "error")        if password != confirm_password:                    return render_template('reset_password.html', user_id=user_id, token=token)            flash("Password must be at least 8 characters long.", "error")        if not password or len(password) < 8:        # Validate password        confirm_password = request.form.get('confirm_password')        password = request.form.get('password')    if request.method == 'POST':            return redirect(url_for('forgot_password'))        flash("The password reset link is invalid or has expired.", "error")    if not user or not user.verify_reset_token(token):    # Verify user and token    user = User.query.get(user_id)    # Find user        return redirect(url_for('dashboard'))    if current_user.is_authenticated:def reset_password(user_id, token):@app.route('/reset-password/<int:user_id>/<token>', methods=['GET', 'POST'])    return render_template('forgot_password.html')        return redirect(url_for('login'))            flash("If that email is in our system, a password reset link has been sent", "success")            # This prevents user enumeration attacks            # Still show success message even if email not found        else:                flash("Failed to send password reset email. Please try again later.", "error")                app.logger.error(f"Failed to send password reset email: {str(e)}")            except Exception as e:                flash("Password reset link has been sent to your email", "success")                mail.send(msg)                )                    html=html_body                    recipients=[email],                    subject=subject,                msg = Message(                # Send email            try:            """            <p>If you did not request a password reset, please ignore this email.</p>            <p>This link is only valid for 1 hour.</p>            <p><a href="{reset_url}">{reset_url}</a></p>            <p>You requested to reset your password. Please click the link below to reset your password:</p>            <p>Hello {user.full_name or user.username},</p>            <h1>Password Reset Request</h1>            html_body = f"""            subject = "Password Reset Request"            # Create email            reset_url = url_for('reset_password', user_id=user.id, token=token, _external=True)            # Build reset URL            token = user.generate_reset_token()            # Generate reset token        if user:                user = User.query.filter_by(email=email).first()        # Find user by email        email = request.form.get('email')            <p>This link is only valid for 1 hour.</p>
            <p>If you did not request a password reset, please ignore this email.</p>
            """
            try:
                # Send email
                msg = Message(
                    subject=subject,
                    recipients=[email],
                    html=html_body
                )
                mail.send(msg)
                flash("Password reset link has been sent to your email", "success")
            except Exception as e:
                app.logger.error(f"Failed to send password reset email: {str(e)}")
                flash("Failed to send password reset email. Please try again later.", "error")
        else:
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