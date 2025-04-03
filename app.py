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
            f.write("MAIL_SERVER=smtp.example.com\n")
            f.write("MAIL_PORT=587\n")
            f.write("MAIL_USE_TLS=True\n")
            f.write("MAIL_USERNAME=user@example.com\n")
            f.write("MAIL_PASSWORD=password\n")
            f.write("MAIL_DEFAULT_SENDER=maintenance@example.com\n")
        print(f"Created default .env file at {dotenv_path}")
        print("Please update with your actual email configuration")

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

# Initialize Flask appiguration
app = Flask(__name__) configure_database
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maintenance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PREFERRED_URL_SCHEME'] = 'http'  # Or 'https' if you're using SSL

# Add session configuration to work across networksabase URI)
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True only if using HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'= False
app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')  # Optional, use for multi-domain setup

# Configure caching for static assetscross networks
configure_caching(app)OKIE_SECURE'] = False  # Set to True only if using HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
# Email configurationOOKIE_SAMESITE'] = 'Lax'
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.example.com')r multi-domain setup
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', 'yes', '1')
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'user@example.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'password')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'maintenance@example.com')
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.example.com')
# Initialize Flask-Mail = int(os.environ.get('MAIL_PORT', 587))
mail = Mail(app)_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', 'yes', '1')
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'user@example.com')
# Initialize databaseWORD'] = os.environ.get('MAIL_PASSWORD', 'password')
db = SQLAlchemy(app)AULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'maintenance@example.com')

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
db = SQLAlchemy(app)
# Custom decorator to require admin access
def admin_required(f):ager
    @wraps(f) = LoginManager()
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login', next=request.url))
        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)thenticated:
    return decorated_function in to access this page.', 'error')
            return redirect(url_for('login', next=request.url))
# Utility function for permission checking
def require_permission(permission):permission to access this page.', 'error')
    def decorator(func):ect(url_for('dashboard'))
        @wraps(func)gs, **kwargs)
        def wrapper(*args, **kwargs):
            if not current_user.has_permission(permission):
                flash(f'Access denied. You need {permission} permission.')
                return redirect(url_for('dashboard'))
            return func(*args, **kwargs)
        return wrapper
    return decorator*args, **kwargs):
            if not current_user.has_permission(permission):
# Define permission constants for better organization and consistencyon.')
class Permissions:turn redirect(url_for('dashboard'))
    # User managementnc(*args, **kwargs)
    USERS_VIEW = 'users.view'
    USERS_CREATE = 'users.create'
    USERS_EDIT = 'users.edit'
    USERS_DELETE = 'users.delete' better organization and consistency
    s Permissions:
    # Role management
    ROLES_VIEW = 'roles.view'
    ROLES_CREATE = 'roles.create'
    ROLES_EDIT = 'roles.edit'
    ROLES_DELETE = 'roles.delete'
    
    # Site management
    SITES_VIEW = 'sites.view'
    SITES_VIEW_ASSIGNED = 'sites.view.assigned'  # New permission for viewing only assigned sites
    SITES_CREATE = 'sites.create'
    SITES_EDIT = 'sites.edit'ete'
    SITES_DELETE = 'sites.delete'
    # Site management
    # Machine managementview'
    MACHINES_VIEW = 'machines.view'ew.assigned'  # New permission for viewing only assigned sites
    MACHINES_CREATE = 'machines.create'
    MACHINES_EDIT = 'machines.edit'
    MACHINES_DELETE = 'machines.delete'
    
    # Part managementent
    PARTS_VIEW = 'parts.view'.view'
    PARTS_CREATE = 'parts.create'reate'
    PARTS_EDIT = 'parts.edit'.edit'
    PARTS_DELETE = 'parts.delete'elete'
    
    # Maintenance management
    MAINTENANCE_VIEW = 'maintenance.view'
    MAINTENANCE_SCHEDULE = 'maintenance.schedule'
    MAINTENANCE_RECORD = 'maintenance.record'
    PARTS_DELETE = 'parts.delete'
    # Backup management
    BACKUP_VIEW = 'backup.view'
    BACKUP_CREATE = 'backup.create'.view'
    BACKUP_RESTORE = 'backup.restore'ce.schedule'
    BACKUP_EXPORT = 'backup.export'ce.record'
    BACKUP_DELETE = 'backup.delete'
    BACKUP_SCHEDULE = 'backup.schedule'  # New permission for managing scheduled backups
    BACKUP_VIEW = 'backup.view'
    # Administration'backup.create'
    ADMIN_ACCESS = 'admin.access'ore'
    ADMIN_FULL = 'admin.full'xport'
    BACKUP_DELETE = 'backup.delete'
    @classmethodULE = 'backup.schedule'  # New permission for managing scheduled backups
    def get_all_permissions(cls):
        """Return all available permissions as dict mapping permission to description"""
        permissions = {}n.access'
        for attr in dir(cls):
            if not attr.startswith('_') and not callable(getattr(cls, attr)) and attr != 'get_all_permissions':
                value = getattr(cls, attr)
                if isinstance(value, str):
                    # Format the name for displayct mapping permission to description"""
                    category, action = value.split('.')[0:2]
                    if len(value.split('.')) > 2:
                        # Handle cases like 'sites.view.assigned'cls, attr)) and attr != 'get_all_permissions':
                        modifier = value.split('.')[2]
                        display = f"{category.capitalize()} - {action.capitalize()} ({modifier})"
                    else:mat the name for display
                        display = f"{category.capitalize()} - {action.capitalize()}"
                    permissions[value] = display:
        return permissionsHandle cases like 'sites.view.assigned'
                        modifier = value.split('.')[2]
# Define database modelsdisplay = f"{category.capitalize()} - {action.capitalize()} ({modifier})"
class Role(db.Model):lse:
    id = db.Column(db.Integer, primary_key=True)pitalize()} - {action.capitalize()}"
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    permissions = db.Column(db.String(500), default="view")
    users = db.relationship('User', backref='role', lazy=True)
    s Role(db.Model):
    def has_permission(self, permission):y=True)
        return permission in self.permissions.split(',')e=False)
    description = db.Column(db.String(200))
    def get_permissions_list(self):ng(500), default="view")
        return self.permissions.split(',')f='role', lazy=True)
    
user_site = db.Table('user_site',ission):
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('site_id', db.Integer, db.ForeignKey('site.id'), primary_key=True),
)   def get_permissions_list(self):
        return self.permissions.split(',')
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)y_key=True),
    password_hash = db.Column(db.String(200), nullable=False), primary_key=True),
    is_admin = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    sites = db.relationship('Site', secondary=user_site, lazy='subquery',
                           backref=db.backref('users', lazy=True))
    email = db.Column(db.String(100))0), unique=True, nullable=False)
    full_name = db.Column(db.String(100))00), nullable=False)
    reset_token = db.Column(db.String(100))t=False)
    reset_token_expiration = db.Column(db.DateTime)role.id'))
    notification_preferences = db.Column(db.Text, default='{}')  # Add this column for storing preferences as JSON string
                           backref=db.backref('users', lazy=True))
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    reset_token = db.Column(db.String(100))
    def check_password(self, password):db.DateTime)
        return check_password_hash(self.password_hash, password) # Add this column for storing preferences as JSON string
    
    def has_permission(self, permission):
        if self.is_admin:h = generate_password_hash(password)
            return True
        if self.role:d(self, password):
            # Direct permission checklf.password_hash, password)
            if self.role.has_permission(permission):
                return True, permission):
            # Check for full admin access to this category
            if '.' in permission:
                category = permission.split('.')[0]
                if self.role.has_permission(f'{category}.full'):
                    return Truermission(permission):
            # Check for admin permission
            if permission.startswith('admin.') and self.role.has_permission('admin.full'):
                return Truession:
        return Falsegory = permission.split('.')[0]
                if self.role.has_permission(f'{category}.full'):
    def generate_reset_token(self):
        # Generate a secure token for password reset
        token = secrets.token_urlsafe(32)in.') and self.role.has_permission('admin.full'):
        self.reset_token = token
        # Token expires after 1 hour
        self.reset_token_expiration = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()n(self):
        return token secure token for password reset
        token = secrets.token_urlsafe(32)
    def verify_reset_token(self, token):
        # Verify the reset token is valid and not expired
        if self.reset_token != token: datetime.utcnow() + timedelta(hours=1)
            return Falset()
        if not self.reset_token_expiration or self.reset_token_expiration < datetime.utcnow():
            return False
        return Truet_token(self, token):
        # Verify the reset token is valid and not expired
    def clear_reset_token(self):oken:
        # Clear the reset token after use
        self.reset_token = None_expiration or self.reset_token_expiration < datetime.utcnow():
        self.reset_token_expiration = None
        db.session.commit()
    
    def get_notification_preferences(self):
        """Get notification preferences with defaults for missing values"""
        import jsontoken = None
        try:.reset_token_expiration = None
            # Try to parse stored preferences
            if self.notification_preferences:
                prefs = json.loads(self.notification_preferences)
            else:tification preferences with defaults for missing values"""
                prefs = {}
        except:
            prefs = {}arse stored preferences
        # Set defaults for missing keysences:
        if 'enable_email' not in prefs:.notification_preferences)
            prefs['enable_email'] = True
        if 'email_frequency' not in prefs:
            prefs['email_frequency'] = 'weekly'
        if 'notification_types' not in prefs:
            prefs['notification_types'] = ['overdue', 'due_soon']
        return prefsmail' not in prefs:
            prefs['enable_email'] = True
class Site(db.Model):quency' not in prefs:
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))= ['overdue', 'due_soon']
    machines = db.relationship('Machine', backref='site', lazy=True, cascade="all, delete-orphan")
    enable_notifications = db.Column(db.Boolean, default=False)
    contact_email = db.Column(db.String(100))  # Contact email for notifications
    notification_threshold = db.Column(db.Integer, default=30)  # Days before due date to notify
    name = db.Column(db.String(100), nullable=False)
    def get_parts_status(self, now=None):
        """Return counts of parts by status (overdue, due_soon, ok)"""ascade="all, delete-orphan")
        if now is None:s = db.Column(db.Boolean, default=False)
            now = datetime.utcnow()ring(100))  # Contact email for notifications
        overdue_parts = [] = db.Column(db.Integer, default=30)  # Days before due date to notify
        due_soon_parts = []
        ok_parts = []tus(self, now=None):
        for machine in self.machines:status (overdue, due_soon, ok)"""
            for part in machine.parts:
                days_until = (part.next_maintenance - now).days
                if days_until < 0:
                    overdue_parts.append(part)
                elif days_until <= self.notification_threshold:
                    due_soon_parts.append(part)
                else:in machine.parts:
                    ok_parts.append(part)aintenance - now).days
        return {if days_until < 0:
            'overdue': overdue_parts,end(part)
            'due_soon': due_soon_parts,.notification_threshold:
            'ok': ok_parts,n_parts.append(part)
        }       else:
                    ok_parts.append(part)
class Machine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100))
    site_id = db.Column(db.Integer, db.ForeignKey('site.id'), nullable=False)
    parts = db.relationship('Part', backref='machine', lazy=True, cascade="all, delete-orphan")
    machine_number = db.Column(db.String(100))  # New column for machine number
    serial_number = db.Column(db.String(100))  # New column for serial number
    maintenance_logs = db.relationship('MaintenanceLog', backref='machine', lazy=True, cascade="all, delete-orphan")
    model = db.Column(db.String(100))
class Part(db.Model):mn(db.Integer, db.ForeignKey('site.id'), nullable=False)
    id = db.Column(db.Integer, primary_key=True)hine', lazy=True, cascade="all, delete-orphan")
    name = db.Column(db.String(100), nullable=False)w column for machine number
    description = db.Column(db.Text)ing(100))  # New column for serial number
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)ue, cascade="all, delete-orphan")
    maintenance_frequency = db.Column(db.Integer, default=7)  # in days
    maintenance_unit = db.Column(db.String(10), default='day')  # 'day', 'week', 'month', or 'year'
    last_maintenance = db.Column(db.DateTime, default=datetime.utcnow)
    next_maintenance = db.Column(db.DateTime)=False)
    notification_sent = db.Column(db.Boolean, default=False)  # Track if notification has been sent
    last_maintained_by = db.Column(db.String(100))  # New field for who performed maintenance
    invoice_number = db.Column(db.String(50))  # New field for invoice tracking
    maintenance_unit = db.Column(db.String(10), default='day')  # 'day', 'week', 'month', or 'year'
    def __init__(self, **kwargs):db.DateTime, default=datetime.utcnow)
        # Extract frequency and unit if provided
        frequency = kwargs.get('maintenance_frequency', 7)e)  # Track if notification has been sent
        unit = kwargs.get('maintenance_unit', 'day')# New field for who performed maintenance
        # Convert to days for internal storage # New field for invoice tracking
        if 'maintenance_frequency' in kwargs and 'maintenance_unit' in kwargs:
            kwargs['maintenance_frequency'] = self.convert_to_days(frequency, unit)
        super(Part, self).__init__(**kwargs)ided
        if 'maintenance_frequency' in kwargs and 'last_maintenance' in kwargs:
            self.update_next_maintenance()t', 'day')
        # Convert to days for internal storage
    def update_next_maintenance(self):kwargs and 'maintenance_unit' in kwargs:
        """Update next maintenance date and reset notification status"""ency, unit)
        self.next_maintenance = self.last_maintenance + timedelta(days=self.maintenance_frequency)
        self.notification_sent = False  # Reset notification status when maintenance is done
            self.update_next_maintenance()
    @staticmethod
    def convert_to_days(value, unit)::
        """Convert a value from specified unit to days"""ation status"""
        value = int(value)nce = self.last_maintenance + timedelta(days=self.maintenance_frequency)
        if unit == 'day':_sent = False  # Reset notification status when maintenance is done
            return value
        elif unit == 'week':
            return value * 7e, unit):
        elif unit == 'month':om specified unit to days"""
            return value * 30
        elif unit == 'year':
            return value * 365
        else:unit == 'week':
            return value  # Default to days
        elif unit == 'month':
    def get_frequency_display(self):
        """Return a human-readable frequency with appropriate unit"""
        days = self.maintenance_frequency
        if days % 365 == 0 and days >= 365:
            return f"{days // 365} {'year' if days // 365 == 1 else 'years'}"
        elif days % 30 == 0 and days >= 30:
            return f"{days // 30} {'month' if days // 30 == 1 else 'months'}"
        elif days % 7 == 0 and days >= 7:ncy with appropriate unit"""
            return f"{days // 7} {'week' if days // 7 == 1 else 'weeks'}"
        else:ys % 365 == 0 and days >= 365:
            return f"{days} {'day' if days == 1 else 'days'}"1 else 'years'}"
        elif days % 30 == 0 and days >= 30:
class MaintenanceLog(db.Model):0} {'month' if days // 30 == 1 else 'months'}"
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)
    part_id = db.Column(db.Integer, db.ForeignKey('part.id'), nullable=False)
    performed_by = db.Column(db.String(100), nullable=False)"
    invoice_number = db.Column(db.String(50))
    maintenance_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text) primary_key=True)
    # Reference to the part to track which part was maintainedid'), nullable=False)
    part = db.relationship('Part', backref='maintenance_logs')nullable=False)
    performed_by = db.Column(db.String(100), nullable=False)
@login_manager.user_loaderlumn(db.String(50))
def load_user(user_id):db.Column(db.DateTime, default=datetime.utcnow)
    return User.query.get(int(user_id))
    # Reference to the part to track which part was maintained
# Routes = db.relationship('Part', backref='maintenance_logs')
@app.route('/')
def index():er.user_loader
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))
# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':in'))
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)for('dashboard'))
            # Get the next parameter or default to dashboard
            next_page = request.args.get('next', 'dashboard')
            return redirect(url_for(next_page))
        flash('Invalid username or password')username).first()
    return render_template('login.html')  # Changed from login_modern.html
            login_user(user)
@app.route('/logout') next parameter or default to dashboard
@login_requiredt_page = request.args.get('next', 'dashboard')
def logout():eturn redirect(url_for(next_page))
    logout_user()valid username or password')
    return redirect(url_for('login'))l')  # Changed from login_modern.html

@app.route('/dashboard')
@login_required
def dashboard():
    # Filter sites based on user access and permissions
    if current_user.is_admin:login'))
        # Admins see all sites
        sites = Site.query.all()
    elif current_user.has_permission(Permissions.SITES_VIEW):
        sites = Site.query.all()
    elif current_user.has_permission(Permissions.SITES_VIEW_ASSIGNED):
        sites = current_user.sites
    else: Admins see all sites
        sites = []te.query.all()
    elif current_user.has_permission(Permissions.SITES_VIEW):
    now = datetime.utcnow()all()
    machines = Machine.query.all()on(Permissions.SITES_VIEW_ASSIGNED):
    return render_template(r.sites
        'dashboard.html',  # Changed from dashboard_modern.html
        sites=sites,
        machines=machines,
        now=now, e.utcnow()
        is_admin=current_user.is_admin,
        current_user=current_user
    )   'dashboard.html',  # Changed from dashboard_modern.html
        sites=sites,
# Admin routes  =machines,
@app.route('/admin')
@login_requiredn=current_user.is_admin,
def admin():ent_user=current_user
    if not current_user.is_admin:
        flash("You don't have permission to access the admin panel", "danger")
        return redirect(url_for('dashboard'))
    return render_template('admin.html')  # Changed from admin_modern.html
@login_required
# CRUD routes for Sites
@app.route('/admin/sites', methods=['GET', 'POST'])
@login_requiredYou don't have permission to access the admin panel", "danger")
def manage_sites():rect(url_for('dashboard'))
    if not current_user.is_admin:.html')  # Changed from admin_modern.html
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for('dashboard'))
    if request.method == 'POST':ds=['GET', 'POST'])
        name = request.form.get('name')
        location = request.form.get('location')
        contact_email = request.form.get('contact_email')
        enable_notifications = True if request.form.get('enable_notifications') else False
        notification_threshold = int(request.form.get('notification_threshold', 30))  # Changed default from 7 to 30
        new_site = Site(name=name, location=location, contact_email=contact_email,
                        enable_notifications=enable_notifications, notification_threshold=notification_threshold)
        db.session.add(new_site)get('location')
        db.session.commit()uest.form.get('contact_email')
        flash('Site added successfully')equest.form.get('enable_notifications') else False
    sites = Site.query.all()ld = int(request.form.get('notification_threshold', 30))  # Changed default from 7 to 30
    return render_template('admin/sites.html', sites=sites)  # Changed from admin_sites_modern.html
                        enable_notifications=enable_notifications, notification_threshold=notification_threshold)
@app.route('/admin/sites/edit/<int:site_id>', methods=['GET', 'POST'])
@login_requiredion.commit()
def edit_site(site_id):ed successfully')
    if not current_user.is_admin:
        flash("You don't have permission to access this page", "danger")rom admin_sites_modern.html
        return redirect(url_for('dashboard'))
    site = Site.query.get_or_404(site_id)d>', methods=['GET', 'POST'])
    if request.method == 'POST':
        site.name = request.form.get('name')
        site.location = request.form.get('location')
        site.contact_email = request.form.get('contact_email') "danger")
        site.enable_notifications = True if request.form.get('enable_notifications') else False
        site.notification_threshold = int(request.form.get('notification_threshold', 30))  # Changed default from 7 to 30
        db.session.commit()OST':
        flash(f'Site "{site.name}" updated successfully')
        return redirect(url_for('manage_sites'))on')
    return render_template('admin/edit_site.html', site=site)  # Changed from admin_edit_site_modern.html
        site.enable_notifications = True if request.form.get('enable_notifications') else False
# CRUD routes for Machinesthreshold = int(request.form.get('notification_threshold', 30))  # Changed default from 7 to 30
@app.route('/admin/machines', methods=['GET', 'POST'])
@login_required'Site "{site.name}" updated successfully')
def manage_machines():t(url_for('manage_sites'))
    if not current_user.is_admin:/edit_site.html', site=site)  # Changed from admin_edit_site_modern.html
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name = request.form.get('name')'GET', 'POST'])
        model = request.form.get('model')
        machine_number = request.form.get('machine_number')
        serial_number = request.form.get('serial_number')
        site_id = request.form.get('site_id')
        new_machine = Machine(':
            name=name, form.get('name')
            model=model, orm.get('model')
            machine_number=machine_number, machine_number')
            serial_number=serial_number,('serial_number')
            site_id=site_idorm.get('site_id')
        )ew_machine = Machine(
        db.session.add(new_machine)
        db.session.commit()
        flash('Machine added successfully!', 'success')
        return redirect(url_for('manage_machines'))
    machines = Machine.query.all()
    sites = Site.query.all()
    return render_template('admin/machines.html', machines=machines, sites=sites)  # Changed from admin_machines_modern.html
        db.session.commit()
@app.route('/admin/machines/edit/<int:machine_id>', methods=['GET', 'POST'])
@login_requiredredirect(url_for('manage_machines'))
def edit_machine(machine_id):all()
    if not current_user.is_admin:
        flash("You don't have permission to access this page", "danger")es=sites)  # Changed from admin_machines_modern.html
        return redirect(url_for('dashboard'))
    machine = Machine.query.get_or_404(machine_id), methods=['GET', 'POST'])
    if request.method == 'POST':
        machine.name = request.form.get('name')
        machine.model = request.form.get('model')
        machine.machine_number = request.form.get('machine_number')  # Update machine number
        machine.serial_number = request.form.get('serial_number')    # Update serial number
        machine.site_id = request.form.get('site_id')
        db.session.commit()OST':
        flash(f'Machine "{machine.name}" updated successfully')
        return redirect(url_for('manage_machines'))
    sites = Site.query.all()er = request.form.get('machine_number')  # Update machine number
    return render_template('admin/edit_machine.html', machine=machine, sites=sites)  # Changed from admin_edit_machine_modern.html
        machine.site_id = request.form.get('site_id')
# CRUD routes for Partsit()
@app.route('/parts')ine "{machine.name}" updated successfully')
@login_requiredredirect(url_for('manage_machines'))
def manage_parts():ery.all()
    # Get list of machines for part assignment dropdownachine=machine, sites=sites)  # Changed from admin_edit_machine_modern.html
    if current_user.is_admin:
        # Admins can see all machines
        machines = Machine.query.join(Site).order_by(Site.name, Machine.name).all()
        # Get all parts
        parts = Part.query.join(Machine).join(Site).order_by(Site.name, Machine.name, Part.name).all()
    else: list of machines for part assignment dropdown
        # Regular users only see machines from their assigned sites
        user_sites = current_user.sites
        site_ids = [site.id for site in user_sites]y(Site.name, Machine.name).all()
        # Get all parts
        machines = Machine.query.filter(Machine.site_id.in_(site_ids)).join(Site).order_by(Site.name, Machine.name).all()
        :
        # Filter parts based on user's assigned sitesassigned sites
        parts = Part.query.join(Machine).join(Site).filter(
            Site.id.in_(site_ids)ite in user_sites]
        ).order_by(Site.name, Machine.name, Part.name).all()
        machines = Machine.query.filter(Machine.site_id.in_(site_ids)).join(Site).order_by(Site.name, Machine.name).all()
    now = datetime.now()
    return render_template('admin/parts.html', parts=parts, machines=machines, now=now)
        parts = Part.query.join(Machine).join(Site).filter(
@app.route('/admin/parts/edit/<int:part_id>', methods=['GET', 'POST'])
@login_required_by(Site.name, Machine.name, Part.name).all()
def edit_part(part_id):
    if not current_user.is_admin and not current_user.has_permission(Permissions.PARTS_EDIT):
        flash("You don't have permission to edit parts", "danger")es=machines, now=now)
        return redirect(url_for('dashboard'))
        te('/admin/parts/edit/<int:part_id>', methods=['GET', 'POST'])
    part = Part.query.get_or_404(part_id)
    if request.method == 'POST':
        part.name = request.form.get('name')rent_user.has_permission(Permissions.PARTS_EDIT):
        part.description = request.form.get('description')danger")
        part.machine_id = request.form.get('machine_id')
        # Get frequency and unit from form
        frequency = int(request.form.get('maintenance_frequency'))
        unit = request.form.get('maintenance_unit', 'day')
        # Convert to days based on unitame')
        part.maintenance_frequency = Part.convert_to_days(frequency, unit)
        part.maintenance_unit = unitrm.get('machine_id')
        part.last_maintenance = datetime.utcnow()
        part.update_next_maintenance()et('maintenance_frequency'))
        db.session.commit().get('maintenance_unit', 'day')
        flash(f'Part "{part.name}" updated successfully')
        return redirect(url_for('manage_parts'))t_to_days(frequency, unit)
    machines = Machine.query.all()it
    return render_template('admin/edit_part.html', part=part, machines=machines)  # Changed from admin_edit_part_modern.html
        part.update_next_maintenance()
# Delete routes for Parts()
@app.route('/admin/sites/delete/<int:site_id>', methods=['POST'])
@login_requiredredirect(url_for('manage_parts'))
def delete_site(site_id):ery.all()
    if not current_user.is_admin:/edit_part.html', part=part, machines=machines)  # Changed from admin_edit_part_modern.html
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    site = Site.query.get_or_404(site_id)_id>', methods=['POST'])
    db.session.delete(site)
    db.session.commit()):
    flash(f'Site "{site.name}" and all associated machines and parts have been deleted')
    return redirect(url_for('manage_sites'))es required.')
        return redirect(url_for('dashboard'))
@app.route('/admin/machines/delete/<int:machine_id>', methods=['POST'])
@login_requireddelete(site)
def delete_machine(machine_id):
    if not current_user.is_admin:d all associated machines and parts have been deleted')
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    machine = Machine.query.get_or_404(machine_id)>', methods=['POST'])
    db.session.delete(machine)
    db.session.commit()ine_id):
    flash(f'Machine "{machine.name}" and all associated parts have been deleted')
    return redirect(url_for('manage_machines'))required.')
        return redirect(url_for('dashboard'))
@app.route('/admin/parts/delete/<int:part_id>', methods=['POST'])
@login_requireddelete(machine)
def delete_part(part_id):
    if not current_user.is_admin:e}" and all associated parts have been deleted')
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    part = Part.query.get_or_404(part_id)_id>', methods=['POST'])
    db.session.delete(part)
    db.session.commit()):
    flash(f'Part "{part.name}" has been deleted')
    return redirect(url_for('manage_parts'))es required.')
        return redirect(url_for('dashboard'))
@app.route('/admin/parts/update-maintenance/<int:part_id>', methods=['GET', 'POST'])
@login_requireddelete(part)
def update_maintenance(part_id):
    if not current_user.is_admin and not current_user.has_permission(Permissions.MAINTENANCE_RECORD):
        flash("You don't have permission to record maintenance", "danger")
        return redirect(url_for('dashboard'))
        te('/admin/parts/update-maintenance/<int:part_id>', methods=['GET', 'POST'])
    part = Part.query.get_or_404(part_id)
    if request.method == 'GET'::
        # Display form for entering maintenance detailsas_permission(Permissions.MAINTENANCE_RECORD):
        return render_template('admin/record_maintenance.html', part=part)  # Changed from record_maintenance_modern.html
            rn redirect(url_for('dashboard'))
    elif request.method == 'POST':
        # Update part maintenance information
        maintenance_date = datetime.utcnow()
        # Display form for entering maintenance details
        # Get form values - prioritize full name over username, part=part)  # Changed from record_maintenance_modern.html
        performed_by = request.form.get('maintained_by', '').strip()
        if not performed_by:POST':
            performed_by = current_user.full_name or current_user.username
        invoice_number = request.form.get('invoice_number', '')
        notes = request.form.get('notes', '')
        # Get form values - prioritize full name over username
        part.last_maintenance = maintenance_datened_by', '').strip()
        part.last_maintained_by = performed_by
        part.invoice_number = invoice_number_name or current_user.username
        part.update_next_maintenance()get('invoice_number', '')
        db.session.commit()m.get('notes', '')
        
        # Create maintenance log entrynance_date
        log = MaintenanceLog(by = performed_by
            machine_id=part.machine_id,umber
            part_id=part.id,ntenance()
            performed_by=performed_by,
            invoice_number=invoice_number,
            maintenance_date=maintenance_date,
            notes=notesceLog(
        )   machine_id=part.machine_id,
        db.session.add(log),
        db.session.commit()rformed_by,
        flash(f'Maintenance for "{part.name}" has been recorded')
        # Check if the request came from dashboard or admin page
        referrer = request.referrer
        if referrer and 'dashboard' in referrer:
            return redirect(url_for('dashboard'))
        else:ssion.commit()
            return redirect(url_for('manage_parts'))en recorded')
        # Check if the request came from dashboard or admin page
# New routes for Role managementrer
@app.route('/admin/roles', methods=['GET', 'POST'])
@login_requiredurn redirect(url_for('dashboard'))
def manage_roles():
    if not current_user.is_admin:or('manage_parts'))
        flash("You don't have permission to manage roles", "danger")
        return redirect(url_for('dashboard'))
    .route('/admin/roles', methods=['GET', 'POST'])
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        permissions = request.form.getlist('permissions'), "danger")
        new_role = Role(name=name, description=description, permissions=','.join(permissions))
        db.session.add(new_role)
        db.session.commit()OST':
        flash(f'Role "{name}" added successfully')
        return redirect(url_for('admin'))escription')
    roles = Role.query.all()t.form.getlist('permissions')
    return render_template('admin/roles.html', roles=roles, all_permissions=Permissions.get_all_permissions())  # Changed from admin_roles_modern.html
        db.session.add(new_role)
# Add a new route for editing a specific role
@app.route('/admin/roles/edit/<int:role_id>', methods=['GET', 'POST'])
@login_requiredredirect(url_for('admin'))
def edit_role(role_id):all()
    if not current_user.is_admin:/roles.html', roles=roles, all_permissions=Permissions.get_all_permissions())  # Changed from admin_roles_modern.html
        flash("You don't have permission to edit roles", "danger")
        return redirect(url_for('dashboard'))
    role = Role.query.get_or_404(role_id)d>', methods=['GET', 'POST'])
    role_permissions = role.get_permissions_list()
    edit_role(role_id):
    if request.method == 'POST'::
        role.name = request.form.get('name')edit roles", "danger")
        role.description = request.form.get('description')
        permissions = request.form.getlist('permissions')
        role.permissions = ','.join(permissions)()
        db.session.commit()
        flash(f'Role "{role.name}" updated successfully')
        return redirect(url_for('manage_roles'))
    return render_template('admin/edit_role.html', role=role, role_permissions=role_permissions, all_permissions=Permissions.get_all_permissions())  # Changed from admin_edit_role_modern.html
        permissions = request.form.getlist('permissions')
# New route for deleting a specific roleissions)
@app.route('/admin/roles/delete/<int:role_id>', methods=['POST'])
@login_required'Role "{role.name}" updated successfully')
def delete_role(role_id):rl_for('manage_roles'))
    if not current_user.is_admin:/edit_role.html', role=role, role_permissions=role_permissions, all_permissions=Permissions.get_all_permissions())  # Changed from admin_edit_role_modern.html
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    role = Role.query.get_or_404(role_id)_id>', methods=['POST'])
    if role.users:
        flash(f'Cannot delete role "{role.name}" because it has assigned users')
        return redirect(url_for('manage_roles'))
    role_name = role.nameied. Admin privileges required.')
    db.session.delete(role)_for('dashboard'))
    db.session.commit()et_or_404(role_id)
    flash(f'Role "{role_name}" deleted successfully')
    return redirect(url_for('manage_roles'))me}" because it has assigned users')
        return redirect(url_for('manage_roles'))
# New routes for User management
@app.route('/admin/users', methods=['GET', 'POST'])
@login_requiredcommit()
def manage_users():role_name}" deleted successfully')
    if not current_user.is_admin:ge_roles'))
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for('dashboard'))
    if request.method == 'POST':ds=['GET', 'POST'])
        # Existing form handling code
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')s this page", "danger")
        email = request.form.get('email')d'))
        role_id = request.form.get('role_id')
        is_admin = True if request.form.get('is_admin') else False
        site_ids = request.form.getlist('site_ids')
        if User.query.filter_by(username=username).first():
            flash(f'Username "{username}" already exists')
            roles = Role.query.all()ail')
            users = User.query.all()role_id')
            sites = Site.query.all()orm.get('is_admin') else False
            return render_template('admin/users.html', roles=roles, users=users, sites=sites, current_user=current_user)  # Changed from admin_users_modern.html
        new_user = User(username=username, full_name=full_name, email=email,
                        role_id=role_id if role_id else None, is_admin=is_admin)
        new_user.set_password(password)
        for site_id in site_ids:ll()
            site = Site.query.get(site_id)
            if site:ender_template('admin/users.html', roles=roles, users=users, sites=sites, current_user=current_user)  # Changed from admin_users_modern.html
                new_user.sites.append(site)full_name=full_name, email=email,
        db.session.add(new_user)role_id if role_id else None, is_admin=is_admin)
        db.session.commit()rd(password)
        flash(f'User "{username}" added successfully')
    roles = Role.query.all()y.get(site_id)
    users = User.query.all()
    sites = Site.query.all()es.append(site)
    return render_template('admin/users.html', roles=roles, users=users, sites=sites, current_user=current_user)  # Changed from admin_users_modern.html
        db.session.commit()
@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_requirede.query.all()
def delete_user(user_id):l()
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.'), users=users, sites=sites, current_user=current_user)  # Changed from admin_users_modern.html
        return redirect(url_for('dashboard'))
    if user_id == current_user.id:nt:user_id>', methods=['POST'])
        flash('Cannot delete your own user account', 'danger')
        return redirect(url_for('manage_users'))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)d. Admin privileges required.')
    db.session.commit()(url_for('dashboard'))
    flash(f'User "{user.username}" has been deleted', 'success')
    return redirect(url_for('manage_users'))ccount', 'danger')
        return redirect(url_for('manage_users'))
# Function to check for parts needing notification and send emails
def check_for_due_soon_parts():
    """Check for parts that have newly entered the 'due soon' threshold and send notifications"""
    sites_with_notifications = []" has been deleted', 'success')
    now = datetime.utcnow()('manage_users'))
    for site in Site.query.filter_by(enable_notifications=True).all():
        if not site.contact_email:ing notification and send emails
            app.logger.info(f"Site {site.name} has notifications enabled but no contact email")
            continuets that have newly entered the 'due soon' threshold and send notifications"""
        overdue_parts = []ns = []
        due_soon_parts = []
        parts_to_mark = []  # Parts to mark as notifiedns=True).all():
        for machine in site.machines:
            for part in machine.parts:te.name} has notifications enabled but no contact email")
                # Skip parts that have already had notifications sent
                if part.notification_sent:
                    continue
                days_until = (part.next_maintenance - now).days
                if days_until < 0:es:
                    overdue_parts.append({
                        'machine': machine.name,ad notifications sent
                        'part': part.name,
                        'days': abs(days_until),
                        'due_date': part.next_maintenance.strftime('%Y-%m-%d'),
                        'part_id': part.id
                    })erdue_parts.append({
                    parts_to_mark.append(part)e,
                elif days_until <= site.notification_threshold:
                    due_soon_parts.append({til),
                        'machine': machine.name,intenance.strftime('%Y-%m-%d'),
                        'part': part.name,
                        'days': days_until,
                        'due_date': part.next_maintenance.strftime('%Y-%m-%d'),
                        'part_id': part.idtification_threshold:
                    })e_soon_parts.append({
                    parts_to_mark.append(part)e,
        if overdue_parts or due_soon_parts:
            sites_with_notifications.append({
                'site': site,date': part.next_maintenance.strftime('%Y-%m-%d'),
                'overdue_parts': overdue_parts,
                'due_soon_parts': due_soon_parts,
                'parts_to_mark': parts_to_mark
            })rdue_parts or due_soon_parts:
    # Send emails for each sitetions.append({
    sent_count = 0ite': site,
    for site_info in sites_with_notifications:,
        site = site_info['site']: due_soon_parts,
        overdue_parts = site_info['overdue_parts']
        due_soon_parts = site_info['due_soon_parts']
        parts_to_mark = site_info['parts_to_mark']
        # Create email content
        subject = f"Maintenance Alert: {site.name}"
        html_body = render_template(
            'email/maintenance_alert.html',parts']
            site=site, = site_info['due_soon_parts']
            overdue_parts=overdue_parts,_to_mark']
            due_soon_parts=due_soon_parts,
            threshold=site.notification_threshold}"
        )tml_body = render_template(
        try:'email/maintenance_alert.html',
            msg = Message(
                subject=subject,e_parts,
                recipients=[site.contact_email],
                html=html_bodyification_threshold
            )
            mail.send(msg)
            app.logger.info(f"Maintenance notification sent to {site.contact_email} for site {site.name}")
            sent_count += 1ject,
            # Mark parts as notifiedtact_email],
            for part in parts_to_mark:
                part.notification_sent = True
            db.session.commit()
        except Exception as e:Maintenance notification sent to {site.contact_email} for site {site.name}")
            app.logger.error(f"Failed to send notification email: {str(e)}")
    return sent_countrts as notified
            for part in parts_to_mark:
def send_maintenance_notification(site, overdue_parts, due_soon_parts):
    """Send email notification about maintenance due for a site"""
    if not site.enable_notifications or not site.contact_email:
        return Falseer.error(f"Failed to send notification email: {str(e)}")
    # Get users associated with this site
    site_users = site.users
    send_maintenance_notification(site, overdue_parts, due_soon_parts):
    # For each user with this site assignednance due for a site"""
    for user in site_users:fications or not site.contact_email:
        # Check user notification preferences
        preferences = user.get_notification_preferences()
        # Skip if user has disabled email notifications
        if not preferences.get('enable_email', True) or not user.email:
            continuewith this site assigned
        user in site_users:
        # Check notification types the user wants to receive
        notification_types = preferences.get('notification_types', ['overdue', 'due_soon'])
        # Skip if user has disabled email notifications
        # Filter parts based on user preferencesrue) or not user.email:
        parts_to_notify = []
        if 'overdue' in notification_types and overdue_parts:
            parts_to_notify.extend(overdue_parts) to receive
        if 'due_soon' in notification_types and due_soon_parts:s', ['overdue', 'due_soon'])
            parts_to_notify.extend(due_soon_parts)
        # Filter parts based on user preferences
        # Skip if no parts to notify about after filtering
        if not parts_to_notify:ation_types and overdue_parts:
            continue_notify.extend(overdue_parts)
        if 'due_soon' in notification_types and due_soon_parts:
        # Prepare email contentend(due_soon_parts)
        subject = f"Maintenance Needed at {site.name}"
        # Create email content based on partster filtering
        html = render_template(
            'email/maintenance_notification.html',
            site=site,
            overdue_parts=overdue_parts if 'overdue' in notification_types else [],
            due_soon_parts=due_soon_parts if 'due_soon' in notification_types else [],
            user=userl content based on parts
        )tml = render_template(
        # Send emailaintenance_notification.html',
        try:site=site,
            msg = Message(subject=subject, 'overdue' in notification_types else [],
                        recipients=[user.email],e_soon' in notification_types else [],
                        html=html,
                        sender=app.config['MAIL_DEFAULT_SENDER'])
            mail.send(msg)
        except Exception as e:
            print(f"Failed to send email to {user.email}: {str(e)}")
            continue    recipients=[user.email],
    return True         html=html,
                        sender=app.config['MAIL_DEFAULT_SENDER'])
# Add the missing route for checking notifications
@app.route('/admin/check-notifications', methods=['GET'])
@login_requirednt(f"Failed to send email to {user.email}: {str(e)}")
def check_notifications():
    if not current_user.is_admin:
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for('dashboard'))tions
    count = check_for_due_soon_parts()', methods=['GET'])
    flash(f'Sent notifications for {count} sites with parts due soon or overdue.')
    return redirect(url_for('admin'))
    if not current_user.is_admin:
# CLI commands"You don't have permission to access this page", "danger")
@app.cli.command("init-db")_for('dashboard'))
def init_db():eck_for_due_soon_parts()
    """Initialize the database with sample data."""th parts due soon or overdue.')
    db.create_all()(url_for('admin'))
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        # Create roles first
        admin_role = Role(name='Administrator', description='Full system access',
                          permissions=','.join(["""
                              Permissions.ADMIN_ACCESS, Permissions.ADMIN_FULL,
                              Permissions.USERS_VIEW, Permissions.USERS_CREATE, Permissions.USERS_EDIT, Permissions.USERS_DELETE,
                              Permissions.ROLES_VIEW, Permissions.ROLES_CREATE, Permissions.ROLES_EDIT, Permissions.ROLES_DELETE,
                              Permissions.SITES_VIEW, Permissions.SITES_CREATE, Permissions.SITES_EDIT, Permissions.SITES_DELETE, Permissions.SITES_VIEW_ASSIGNED,
                              Permissions.MACHINES_VIEW, Permissions.MACHINES_CREATE, Permissions.MACHINES_EDIT, Permissions.MACHINES_DELETE,
                              Permissions.PARTS_VIEW, Permissions.PARTS_CREATE, Permissions.PARTS_EDIT, Permissions.PARTS_DELETE,
                              Permissions.MAINTENANCE_VIEW, Permissions.MAINTENANCE_RECORD,
                              # Add backup permissions to administrator role, including the new BACKUP_SCHEDULE permissionDELETE,
                              Permissions.BACKUP_VIEW, Permissions.BACKUP_CREATE, Permissions.BACKUP_RESTORE,ssions.ROLES_DELETE,
                              Permissions.BACKUP_EXPORT, Permissions.BACKUP_DELETE, Permissions.BACKUP_SCHEDULEions.SITES_DELETE, Permissions.SITES_VIEW_ASSIGNED,
                          ])) Permissions.MACHINES_VIEW, Permissions.MACHINES_CREATE, Permissions.MACHINES_EDIT, Permissions.MACHINES_DELETE,
        manager_role = Role(name='Manager', description='Can manage sites and view all data',ARTS_EDIT, Permissions.PARTS_DELETE,
                            permissions=','.join([NCE_VIEW, Permissions.MAINTENANCE_RECORD,
                                Permissions.SITES_VIEW, Permissions.SITES_CREATE, Permissions.SITES_EDIT, Permissions.SITES_DELETE,
                                Permissions.MACHINES_VIEW, Permissions.MACHINES_CREATE, Permissions.MACHINES_EDIT, Permissions.MACHINES_DELETE,
                                Permissions.PARTS_VIEW, Permissions.PARTS_CREATE, Permissions.PARTS_EDIT, Permissions.PARTS_DELETE,
                                Permissions.MAINTENANCE_VIEW, Permissions.MAINTENANCE_RECORD,
                                # Managers can view, create and schedule backups but not restore or delete them
                                Permissions.BACKUP_VIEW, Permissions.BACKUP_CREATE, Permissions.BACKUP_EXPORT, Permissions.BACKUP_SCHEDULE
                            ])) Permissions.SITES_VIEW, Permissions.SITES_CREATE, Permissions.SITES_EDIT, Permissions.SITES_DELETE,
        technician_role = Role(name='Technician', description='Can update maintenance records for assigned sites', Permissions.MACHINES_DELETE,
                               permissions=','.join([W, Permissions.PARTS_CREATE, Permissions.PARTS_EDIT, Permissions.PARTS_DELETE,
                                   Permissions.SITES_VIEW_ASSIGNED,ssions.MAINTENANCE_RECORD,
                                   Permissions.MACHINES_VIEW, Permissions.PARTS_VIEW,not restore or delete them
                                   Permissions.MAINTENANCE_VIEW, Permissions.MAINTENANCE_RECORD.BACKUP_EXPORT, Permissions.BACKUP_SCHEDULE
                               ]))
        db.session.add_all([admin_role, manager_role, technician_role])te maintenance records for assigned sites',
        db.session.commit()    permissions=','.join([
        # Create admin user        Permissions.SITES_VIEW_ASSIGNED,
        admin = User(username='admin', full_name='Administrator', email='admin@example.com', is_admin=True, role_id=admin_role.id)
        admin.set_password('admin')Permissions.MAINTENANCE_VIEW, Permissions.MAINTENANCE_RECORD
        db.session.add(admin)  ]))
        db.session.commit()[admin_role, manager_role, technician_role])
        # Create test sites
        site1 = Site(name='Main Factory', location='123 Industrial Ave')
        site2 = Site(name='Assembly Plant', location='456 Production Blvd', enable_notifications=True,True, role_id=admin_role.id)
                     contact_email='factory.manager@example.com', notification_threshold=7)
        db.session.add_all([site1, site2])
        db.session.commit()
        # Create test machines
        machine1 = Machine(name='CNC Mill', model='XYZ-1000', site_id=site1.id)
        machine2 = Machine(name='Lathe', model='LT-500', site_id=site1.id), enable_notifications=True,
        machine3 = Machine(name='Drill Press', model='DP-750', site_id=site2.id)hreshold=7)
        machine4 = Machine(name='Assembly Robot', model='AR-200', site_id=site2.id)
        db.session.add_all([machine1, machine2, machine3, machine4])
        db.session.commit()nes
        # Current date for reference Mill', model='XYZ-1000', site_id=site1.id)
        now = datetime.utcnow()='Lathe', model='LT-500', site_id=site1.id)
        # Create test parts with varying maintenance frequencies and past maintenance dates
        parts = [= Machine(name='Assembly Robot', model='AR-200', site_id=site2.id)
            # Overdue parts (past maintenance date)hine3, machine4])
            Part(name='Spindle', description='Main cutting spindle', machine_id=machine1.id,
                 maintenance_frequency=7, last_maintenance=now - timedelta(days=10)),  # 3 days overdue
            Part(name='Coolant System', description='Cutting fluid circulation', machine_id=machine1.id,
                 maintenance_frequency=14, last_maintenance=now - timedelta(days=20)),  # 6 days overdue
            Part(name='Tool Changer', description='Automatic tool changer', machine_id=machine1.id,
                 maintenance_frequency=30, last_maintenance=now - timedelta(days=20)),  # Due in 10 days
            Part(name='Chuck', description='Workholding device', machine_id=machine2.id,.id,
                 maintenance_frequency=21, last_maintenance=now - timedelta(days=15)),  # Due in 6 days
            Part(name='Tailstock', description='Supports workpiece end', machine_id=machine2.id,ine1.id,
                 maintenance_frequency=30, last_maintenance=now - timedelta(days=22)),  # Due in 8 dayse
            # Due soon parts (maintenance due within 14 days)tool changer', machine_id=machine1.id,
            Part(name='Servo Motor', description='Axis movement', machine_id=machine4.id, Due in 10 days
                 maintenance_frequency=60, last_maintenance=now - timedelta(days=58)),  # Due in 2 days
            Part(name='Coolant System', description='Cutting fluid circulation', machine_id=machine1.id,
                 maintenance_frequency=14, last_maintenance=now - timedelta(days=9)),  # Due in 5 days
            # OK parts (maintenance due beyond 14 days)ance=now - timedelta(days=22)),  # Due in 8 days
            Part(name='Drill Bit', description='Cutting tool', machine_id=machine3.id,
                 maintenance_frequency=45, last_maintenance=now - timedelta(days=20)),  # Due in 25 days
            Part(name='Table', description='Work surface', machine_id=machine3.id,8)),  # Due in 2 days
                 maintenance_frequency=60, last_maintenance=now - timedelta(days=15)),  # Due in 45 days
            Part(name='Servo Motor A', description='Axis 1 movement', machine_id=machine4.id,in 5 days
                 maintenance_frequency=60, last_maintenance=now - timedelta(days=20)),  # Due in 40 days
            Part(name='Servo Motor B', description='Axis 2 movement', machine_id=machine4.id,
                 maintenance_frequency=90, last_maintenance=now - timedelta(days=30)),  # Due in 60 days
            Part(name='Servo Motor C', description='Axis 3 movement', machine_id=machine4.id,
                 maintenance_frequency=90, last_maintenance=now - timedelta(days=30)),  # Due in 60 days
            Part(name='Controller', description='Robot brain', machine_id=machine4.id,ne4.id,
                 maintenance_frequency=180, last_maintenance=now - timedelta(days=30)),  # Due in 150 days
            Part(name='Power Supply', description='Electrical power unit', machine_id=machine4.id,
                 maintenance_frequency=365, last_maintenance=now - timedelta(days=90)),  # Due in 275 days
            Part(name='Gripper', description='End effector', machine_id=machine4.id,hine4.id,
                 maintenance_frequency=120, last_maintenance=now - timedelta(days=20))  # Due in 100 days
        ]   Part(name='Controller', description='Robot brain', machine_id=machine4.id,
        db.session.add_all(parts)uency=180, last_maintenance=now - timedelta(days=30)),  # Due in 150 days
        db.session.commit()r Supply', description='Electrical power unit', machine_id=machine4.id,
        # Update next_maintenance for all partst_maintenance=now - timedelta(days=90)),  # Due in 275 days
        for part in parts:pper', description='End effector', machine_id=machine4.id,
            part.update_next_maintenance(), last_maintenance=now - timedelta(days=20))  # Due in 100 days
        db.session.commit()
        print("Database initialized with test data.")
    else:b.session.commit()
        print("Database already contains data. Skipping initialization.")
        for part in parts:
@app.cli.command("send-notifications")ce()
def send_all_notifications():
    """Send maintenance notifications for all sites that have them enabled."""
    sent_count = check_for_due_soon_parts()
    print(f"Sent {sent_count} notification emails.")ing initialization.")

@app.cli.command("reset-db")ications")
def reset_db():tifications():
    """Drop and recreate all database tables."""tes that have them enabled."""
    db.drop_all()check_for_due_soon_parts()
    db.create_all()ent_count} notification emails.")
    print("Database has been reset. Run 'flask init-db' to initialize with sample data.")
@app.cli.command("reset-db")
@app.cli.command("check-db")
def check_db(): recreate all database tables."""
    """Check if the database schema needs to be updated."""
    with app.app_context():
        inspector = db.inspect(db.engine)flask init-db' to initialize with sample data.")
        tables_exist = inspector.has_table("part")
        if tables_exist:db")
            columns = [col['name'] for col in inspector.get_columns('part')]
            if 'notification_sent' not in columns:dated."""
                print("Database schema needs updating - 'notification_sent' column is missing.")
                print("Please run 'flask --app app reset-db' to update the database schema.")
            else:ist = inspector.has_table("part")
                print("Database schema is up to date.")
        else:olumns = [col['name'] for col in inspector.get_columns('part')]
            print("Database tables don't exist. Run 'flask --app app init-db' to initialize.")
                print("Database schema needs updating - 'notification_sent' column is missing.")
@app.cli.command("check-notification-settings")app reset-db' to update the database schema.")
def check_notification_settings():
    """Display notification settings for all sites.""")
    sites = Site.query.all()
    if not sites:("Database tables don't exist. Run 'flask --app app init-db' to initialize.")
        print("No sites found in database.")
        returnnd("check-notification-settings")
    check_notification_settings():
    print("\nNotification Settings for Sites:")tes."""
    print("--------------------------------------")
    for site in sites:
        print(f"\nSite: {site.name}")base.")
        print(f"  Notifications Enabled: {site.enable_notifications}")
        print(f"  Contact Email: {site.contact_email or 'NOT SET'}")
        print(f"  Notification Threshold: {site.notification_threshold} days")
        t("--------------------------------------")
        now = datetime.utcnow()
        parts_notified = 0ite.name}")
        parts_overdue = 0ations Enabled: {site.enable_notifications}")
        parts_due_soon = 0Email: {site.contact_email or 'NOT SET'}")
        print(f"  Notification Threshold: {site.notification_threshold} days")
        # Count parts by status
        for machine in site.machines:
            for part in machine.parts:
                if part.notification_sent:
                    parts_notified += 1
                else:
                    days_until = (part.next_maintenance - now).days
                    if days_until < 0:
                        parts_overdue += 1
                    elif days_until <= site.notification_threshold:
                        parts_due_soon += 1
        print(f"  Parts Status Summary:")
        print(f"    - Overdue: {parts_overdue}")tenance - now).days
        print(f"    - Due soon: {parts_due_soon}")
        print(f"    - Already notified: {parts_notified}")
                    elif days_until <= site.notification_threshold:
@app.cli.command("create-excel-template") 1
@click.argument("output_file", default="maintenance_import_template.xlsx")
def create_excel_template_cmd(output_file):ue}")
    """Create a template Excel file for importing maintenance data."""
    from create_excel_template import create_templateed}")
    create_template(output_file)
    print(f"Template created: {output_file}")
@click.argument("output_file", default="maintenance_import_template.xlsx")
@app.cli.command("import-excel")tput_file):
@click.argument("file_path")el file for importing maintenance data."""
def import_excel_cmd(file_path):mport create_template
    """Import maintenance data from an Excel file.
    FILE_PATH is the path to the Excel file to import.
    """
    from import_excel import import_excel
    try:rgument("file_path")
        stats = import_excel(file_path)
        print("Import completed successfully!")le.
        print(f"Sites: {stats['sites_added']} added, {stats['sites_skipped']} skipped")
        print(f"Machines: {stats['machines_added']} added, {stats['machines_skipped']} skipped")
        print(f"Parts: {stats['parts_added']} added, {stats['parts_skipped']} skipped")
        print(f"Errors: {stats['errors']}")
    except Exception as e:el(file_path)
        print(f"Import failed: {str(e)}")lly!")
        print(f"Sites: {stats['sites_added']} added, {stats['sites_skipped']} skipped")
@app.route('/admin/test-email', methods=['GET', 'POST'])d, {stats['machines_skipped']} skipped")
@login_required"Parts: {stats['parts_added']} added, {stats['parts_skipped']} skipped")
def test_email():rrors: {stats['errors']}")
    """Send a test email to verify email configuration."""
    if not current_user.is_admin:tr(e)}")
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))', 'POST'])
    in_required
    # Check if email templates exist before attempting to send
    templates_dir = os.path.join(BASE_DIR, 'templates')"""
    test_email_path = os.path.join(templates_dir, 'email', 'test_email.html')
        flash('Access denied. Admin privileges required.')
    if not os.path.exists(test_email_path):))
        flash(f'Email template not found: email/test_email.html', 'error')
        return redirect(url_for('admin'))re attempting to send
        lates_dir = os.path.join(BASE_DIR, 'templates')
    if request.method == 'POST':in(templates_dir, 'email', 'test_email.html')
        recipient = request.form.get('email')
        subject = request.form.get('subject', 'Maintenance Tracker - Test Email')
        message = request.form.get('message', 'This is a test email from the Maintenance Tracker system.')
        site_name = request.form.get('site_name', 'Test Site')
        site_location = request.form.get('site_location', 'Test Location')
        notification_threshold = int(request.form.get('notification_threshold', 7))
        include_samples = 'include_samples' in request.form
        subject = request.form.get('subject', 'Maintenance Tracker - Test Email')
        # Sample data for overdue and due-soon itemsis a test email from the Maintenance Tracker system.')
        sample_data = {}est.form.get('site_name', 'Test Site')
        if include_samples:uest.form.get('site_location', 'Test Location')
            now = datetime.utcnow()t(request.form.get('notification_threshold', 7))
            # Sample overdue parts_samples' in request.form
            sample_data['overdue_parts'] = [
                {data for overdue and due-soon items
                    'machine': 'CNC Mill',
                    'part': 'Spindle',
                    'days': 3,now()
                    'due_date': (now - timedelta(days=3)).strftime('%Y-%m-%d'),
                    'part_id': 1_parts'] = [
                },
                {   'machine': 'CNC Mill',
                    'machine': 'Lathe',
                    'part': 'Chuck',
                    'days': 5,: (now - timedelta(days=3)).strftime('%Y-%m-%d'),
                    'due_date': (now - timedelta(days=5)).strftime('%Y-%m-%d'),
                    'part_id': 2
                }
            ]       'machine': 'Lathe',
            # Sample due-soon parts,
            sample_data['due_soon_parts'] = [
                {   'due_date': (now - timedelta(days=5)).strftime('%Y-%m-%d'),
                    'machine': 'Assembly Robot',
                    'part': 'Servo Motor',
                    'days': 2,
                    'due_date': (now + timedelta(days=2)).strftime('%Y-%m-%d'),
                    'part_id': 3n_parts'] = [
                },
                {   'machine': 'Assembly Robot',
                    'machine': 'CNC Mill',
                    'part': 'Coolant System',
                    'days': notification_threshold - 1,)).strftime('%Y-%m-%d'),
                    'due_date': (now + timedelta(days=notification_threshold - 1)).strftime('%Y-%m-%d'),
                    'part_id': 4
                }
            ]       'machine': 'CNC Mill',
            # Sample site infooolant System',
            sample_data['site'] = {ation_threshold - 1,
                'name': site_name,ow + timedelta(days=notification_threshold - 1)).strftime('%Y-%m-%d'),
                'location': site_location
            }   }
            sample_data['threshold'] = notification_threshold
        try:# Sample site info
            # Add detailed logging{
            app.logger.info(f"Attempting to render email template: email/test_email.html")
                'location': site_location
            # Render the template with error handling
            try:le_data['threshold'] = notification_threshold
                html_content = render_template('email/test_email.html', 
                                   message=message,
                                   now=datetime.utcnow(),template: email/test_email.html")
                                   **sample_data)
            except Exception as template_error:ndling
                app.logger.error(f"Template rendering error: {str(template_error)}")
                flash(f'Template error: {str(template_error)}', 'error')
                return redirect(url_for('test_email'))
                                   now=datetime.utcnow(),
            msg = Message(         **sample_data)
                subject=subject,template_error:
                recipients=[recipient],late rendering error: {str(template_error)}")
                html=html_contenterror: {str(template_error)}', 'error')
            )   return redirect(url_for('test_email'))
            mail.send(msg)
            flash(f'Test email sent to {recipient} successfully!')
        except Exception as e:t,
            app.logger.error(f"Email sending error: {str(e)}")
            flash(f'Failed to send test email: {str(e)}')
        return redirect(url_for('test_email'))
    else:   mail.send(msg)
        # Get current email configurationecipient} successfully!')
        email_config = { as e:
            'MAIL_SERVER': app.config['MAIL_SERVER'],str(e)}")
            'MAIL_PORT': app.config['MAIL_PORT'],tr(e)}')
            'MAIL_USE_TLS': app.config['MAIL_USE_TLS'],
            'MAIL_USERNAME': app.config['MAIL_USERNAME'],
            'MAIL_DEFAULT_SENDER': app.config['MAIL_DEFAULT_SENDER']
        }mail_config = {
        return render_template('admin/test_email.html', config=email_config)
            'MAIL_PORT': app.config['MAIL_PORT'],
@app.cli.command("update-db-schema")ig['MAIL_USE_TLS'],
def update_db_schema():AME': app.config['MAIL_USERNAME'],
    """Update database schema with new fields without losing data."""
    with app.app_context():
        inspector = db.inspect(db.engine)t_email.html', config=email_config)
        # Check if maintenance_log table exists
        tables = inspector.get_table_names()
        if 'maintenance_log' not in tables:
            # Create the maintenance_log tablewithout losing data."""
            with db.engine.connect() as conn:
                conn.execute(db.text(''')
                    CREATE TABLE maintenance_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        machine_id INTEGER NOT NULL,
                        part_id INTEGER NOT NULL,
                        performed_by VARCHAR(100) NOT NULL,
                        invoice_number VARCHAR(50),
                        maintenance_date DATETIME NOT NULL,
                        notes TEXT,PRIMARY KEY AUTOINCREMENT,
                        FOREIGN KEY (machine_id) REFERENCES machine (id),
                        FOREIGN KEY (part_id) REFERENCES part (id)
                    )   performed_by VARCHAR(100) NOT NULL,
                '''))   invoice_number VARCHAR(50),
                conn.commit()enance_date DATETIME NOT NULL,
            print("Created maintenance_log table")
                        FOREIGN KEY (machine_id) REFERENCES machine (id),
        # Check Machine table columnspart_id) REFERENCES part (id)
        machine_columns = [col['name'] for col in inspector.get_columns('machine')]
        missing_machine_columns = []
        if 'machine_number' not in machine_columns:
            missing_machine_columns.append('machine_number')
        if 'serial_number' not in machine_columns:
            missing_machine_columns.append('serial_number')
        if missing_machine_columns:e'] for col in inspector.get_columns('machine')]
            # Add new columns to the table using the modern approach
            with db.engine.connect() as conn:lumns:
                for column in missing_machine_columns:mber')
                    conn.execute(db.text(f'ALTER TABLE machine ADD COLUMN {column} VARCHAR(100)'))
                conn.commit()olumns.append('serial_number')
            print(f"Added new columns to Machine table: {', '.join(missing_machine_columns)}")
        else: Add new columns to the table using the modern approach
            print("Machine table schema is already up to date.")
                for column in missing_machine_columns:
        # Check Part table columnsb.text(f'ALTER TABLE machine ADD COLUMN {column} VARCHAR(100)'))
        part_columns = [col['name'] for col in inspector.get_columns('part')]
        missing_part_columns = []umns to Machine table: {', '.join(missing_machine_columns)}")
        if 'last_maintained_by' not in part_columns:
            missing_part_columns.append('last_maintained_by').")
        if 'invoice_number' not in part_columns:
            missing_part_columns.append('invoice_number')
        if 'maintenance_unit' not in part_columns:pector.get_columns('part')]
            missing_part_columns.append('maintenance_unit')
        if missing_part_columns:not in part_columns:
            # Add new columns to the table using the modern approach
            with db.engine.connect() as conn:ns:
                for column in missing_part_columns:mber')
                    if column == 'last_maintained_by':
                        conn.execute(db.text(f'ALTER TABLE part ADD COLUMN {column} VARCHAR(100)'))
                    elif column == 'invoice_number':
                        conn.execute(db.text(f'ALTER TABLE part ADD COLUMN {column} VARCHAR(50)'))
                    elif column == 'maintenance_unit':
                        conn.execute(db.text(f'ALTER TABLE part ADD COLUMN {column} VARCHAR(10) DEFAULT "day"'))
                conn.commit() == 'last_maintained_by':
            print(f"Added new columns to Part table: {', '.join(missing_part_columns)}")HAR(100)'))
        else:       elif column == 'invoice_number':
            print("Part table schema is already up to date.")rt ADD COLUMN {column} VARCHAR(50)'))
                    elif column == 'maintenance_unit':
        # Check User table columnste(db.text(f'ALTER TABLE part ADD COLUMN {column} VARCHAR(10) DEFAULT "day"'))
        user_columns = [col['name'] for col in inspector.get_columns('user')]
        missing_user_columns = []umns to Part table: {', '.join(missing_part_columns)}")
        if 'reset_token' not in user_columns:
            missing_user_columns.append('reset_token')date.")
        if 'reset_token_expiration' not in user_columns:
            missing_user_columns.append('reset_token_expiration')
        if 'notification_preferences' not in user_columns:et_columns('user')]
            missing_user_columns.append('notification_preferences')
        if missing_user_columns:user_columns:
            # Add missing columns to the User tablen')
            with db.engine.connect() as conn:er_columns:
                for column in missing_user_columns:n_expiration')
                    if column == 'reset_token':er_columns:
                        conn.execute(db.text(f'ALTER TABLE user ADD COLUMN {column} VARCHAR(100)'))
                    elif column == 'reset_token_expiration':
                        conn.execute(db.text(f'ALTER TABLE user ADD COLUMN {column} DATETIME'))
                    elif column == 'notification_preferences':
                        conn.execute(db.text(f'ALTER TABLE user ADD COLUMN {column} TEXT DEFAULT \'{{}}\''))
                conn.commit() == 'reset_token':
            print(f"Added new columns to User table: {', '.join(missing_user_columns)}")HAR(100)'))
        else:       elif column == 'reset_token_expiration':
            print("User table schema is already up to date.")er ADD COLUMN {column} DATETIME'))
                    elif column == 'notification_preferences':
@app.route('/admin/debug/schema')ute(db.text(f'ALTER TABLE user ADD COLUMN {column} TEXT DEFAULT \'{{}}\''))
@login_required conn.commit()
def debug_schema():"Added new columns to User table: {', '.join(missing_user_columns)}")
    """Debug route to display database schema information."""
    if not current_user.is_admin:ema is already up to date.")
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    in_required
    inspector = db.inspect(db.engine)
    tables = {}ute to display database schema information."""
    if not current_user.is_admin:
    for table_name in inspector.get_table_names():uired.')
        columns = []ect(url_for('dashboard'))
        for column in inspector.get_columns(table_name):
            columns.append({b.engine)
                'name': column['name'],
                'type': str(column['type']),
                'nullable': column['nullable']s():
            })s = []
        tables[table_name] = columnscolumns(table_name):
    return render_template('debug_schema.html', tables=tables)
                'name': column['name'],
@app.route('/machine/<int:machine_id>/history')
@login_required 'nullable': column['nullable']
def machine_history(machine_id):
    machine = Machine.query.get_or_404(machine_id)
    return render_template('debug_schema.html', tables=tables)
    # Check if user has access to this machine's site
    if not current_user.is_admin and not current_user.has_permission(Permissions.MACHINES_VIEW):
        flash("You don't have permission to view this machine's history", "danger")
        return redirect(url_for('dashboard'))
    machine = Machine.query.get_or_404(machine_id)
    # Get maintenance logs sorted by date (newest first)
    logs = []f user has access to this machine's site
    try:ot current_user.is_admin and not current_user.has_permission(Permissions.MACHINES_VIEW):
        logs = MaintenanceLog.query.filter_by(machine_id=machine_id).order_by(MaintenanceLog.maintenance_date.desc()).all()
    except Exception as e:l_for('dashboard'))
        flash(f'Error retrieving maintenance history. Database might need to be updated: {str(e)}')
        # Create the table if it doesn't existest first)
        try:]
            with app.app_context():
                with db.engine.connect() as conn:hine_id=machine_id).order_by(MaintenanceLog.maintenance_date.desc()).all()
                    conn.execute(db.text('''
                        CREATE TABLE IF NOT EXISTS maintenance_log ( need to be updated: {str(e)}')
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            machine_id INTEGER NOT NULL,
                            part_id INTEGER NOT NULL,
                            performed_by VARCHAR(100) NOT NULL,
                            invoice_number VARCHAR(50),
                            maintenance_date DATETIME NOT NULL,log (
                            notes TEXT,PRIMARY KEY AUTOINCREMENT,
                            FOREIGN KEY (machine_id) REFERENCES machine (id),
                            FOREIGN KEY (part_id) REFERENCES part (id)
                        )   performed_by VARCHAR(100) NOT NULL,
                    '''))   invoice_number VARCHAR(50),
                    conn.commit()enance_date DATETIME NOT NULL,
            flash('Maintenance log table was created. Please try again.')
        except Exception as create_error:machine_id) REFERENCES machine (id),
            flash(f'Could not create maintenance log table: {str(create_error)}')
    return render_template('machine_history.html', machine=machine, logs=logs)  # Changed from machine_history_modern.html
                    '''))
# Import backup utilitiescommit()
from backup_utils import backup_database, restore_database, list_backups, delete_backup
        except Exception as create_error:
@app.route('/admin/backups', methods=['GET', 'POST'])table: {str(create_error)}')
@login_requireder_template('machine_history.html', machine=machine, logs=logs)  # Changed from machine_history_modern.html
@admin_required
def admin_backups():ities
    # Check if backup directory existsse, restore_database, list_backups, delete_backup
    from backup_utils import list_backups, backup_database, restore_database, delete_backup
    .route('/admin/backups', methods=['GET', 'POST'])
    if request.method == 'POST':
        action = request.form.get('action')
        n_backups():
        if action == 'create':y exists
            backup_name = request.form.get('backup_name', '').strip()atabase, delete_backup
            include_users = 'include_users' in request.form
            st.method == 'POST':
            # Make sure backup_name is a string, not a boolean
            if not backup_name:
                backup_name = None  # Let the backup function use the default timestamp
                up_name = request.form.get('backup_name', '').strip()
            filename = backup_database(backup_name, include_users)
            flash(f'Backup created successfully: {filename}', 'success')
            return redirect(url_for('admin_backups'))a boolean
            if not backup_name:
        elif action == 'restore':e  # Let the backup function use the default timestamp
            backup_file = request.form.get('backup_file')
            restore_users = 'restore_users' in request.form_users)
            flash(f'Backup created successfully: {filename}', 'success')
            from backup_utils import BACKUP_DIRups'))
            backup_path = os.path.join(BACKUP_DIR, backup_file)
             action == 'restore':
            try:up_file = request.form.get('backup_file')
                stats = restore_database(backup_path, restore_users)
                if stats['errors']:
                    flash(f'Backup restored with {len(stats["errors"])} errors. See logs for details.', 'warning')
                else:th = os.path.join(BACKUP_DIR, backup_file)
                    flash('Backup restored successfully!', 'success')
                return redirect(url_for('admin_backups'))
            except Exception as e:tabase(backup_path, restore_users)
                flash(f'Error restoring backup: {str(e)}', 'error')
                return redirect(url_for('admin_backups'))ts["errors"])} errors. See logs for details.', 'warning')
                else:
        elif action == 'delete':p restored successfully!', 'success')
            filename = request.form.get('filename')ups'))
            if delete_backup(filename):
                flash(f'Backup deleted: {filename}', 'success')or')
            else:eturn redirect(url_for('admin_backups'))
                flash(f'Error deleting backup: {filename}', 'error')
            return redirect(url_for('admin_backups'))
            filename = request.form.get('filename')
    # Gather information about available backups
    backups = list_backups()up deleted: {filename}', 'success')
            else:
    # Prepare the display info for each backup {filename}', 'error')
    for backup in backups:t(url_for('admin_backups'))
        # Format the size to MB
        size_mb = round(backup['size'] / (1024 * 1024), 2)
        backup['size_mb'] = size_mb
        
        # Create a more readable display namep
        if '_' in backup['filename']:
            parts = backup['filename'].split('_')
            if len(parts) >= 3:'size'] / (1024 * 1024), 2)
                # Extract date and time from filename
                date_part = parts[0]
                time_part = parts[1]play name
                name_part = '_'.join(parts[2:])
                s = backup['filename'].split('_')
                # Format the date
                try:tract date and time from filename
                    formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:]}"
                    formatted_time = f"{time_part[:2]}:{time_part[2:4]}"
                    display_name = f"{formatted_date} {formatted_time}"
                    
                    # Add custom name part if it exists
                    if name_part.endswith('.json'):
                        name_part = name_part[:-5]  # Remove .json extensione_part[6:]}"
                    if name_part:e = f"{time_part[:2]}:{time_part[2:4]}"
                        display_name += f" - {name_part}"rmatted_time}"
                except:
                    display_name = backup['filename']ts
            else:   if name_part.endswith('.json'):
                display_name = backup['filename']]  # Remove .json extension
        else:       if name_part:
            display_name = backup['filename']{name_part}"
                except:
        backup['display_name'] = display_namelename']
            else:
    # Add this return statement to fix the error]
    return render_template('admin/backups.html', backups=backups)
            display_name = backup['filename']
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():y_name'] = display_name
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))ror
    return render_template('admin/backups.html', backups=backups)
    if request.method == 'POST':
        email = request.form.get('email')GET', 'POST'])
        ot_password():
        # Find user by emailnticated:
        user = User.query.filter_by(email=email).first()
        
        if user:ethod == 'POST':
            # Generate reset tokenemail')
            token = user.generate_reset_token()
            # Build reset URL
            reset_url = url_for('reset_password', user_id=user.id, token=token, _external=True)
            # Create email
            subject = "Password Reset Request"
            html_body = f""" token
            <h1>Password Reset Request</h1>en()
            <p>Hello {user.full_name or user.username},</p>
            <p>You requested to reset your password. Please click the link below to reset your password:</p>
            <p><a href="{reset_url}">{reset_url}</a></p>
            <p>This link is only valid for 1 hour.</p>
            <p>If you did not request a password reset, please ignore this email.</p>
            """>Password Reset Request</h1>
            try:ello {user.full_name or user.username},</p>
                # Send email to reset your password. Please click the link below to reset your password:</p>
                msg = Message(_url}">{reset_url}</a></p>
                    subject=subject,id for 1 hour.</p>
                    recipients=[email], password reset, please ignore this email.</p>
                    html=html_body
                )
                mail.send(msg)
                flash("Password reset link has been sent to your email", "success")
            except Exception as e:t,
                app.logger.error(f"Failed to send password reset email: {str(e)}")
                flash("Failed to send password reset email. Please try again later.", "error")
        else:   )
            # Still show success message even if email not found
            # This prevents user enumeration attackssent to your email", "success")
            flash("If that email is in our system, a password reset link has been sent", "success")
        return redirect(url_for('login')) to send password reset email: {str(e)}")
                flash("Failed to send password reset email. Please try again later.", "error")
    return render_template('forgot_password.html')
            # Still show success message even if email not found
@app.route('/reset-password/<int:user_id>/<token>', methods=['GET', 'POST'])
def reset_password(user_id, token): in our system, a password reset link has been sent", "success")
    if current_user.is_authenticated:n'))
        return redirect(url_for('dashboard'))
    return render_template('forgot_password.html')
    # Find user
    user = User.query.get(user_id)ser_id>/<token>', methods=['GET', 'POST'])
    reset_password(user_id, token):
    # Verify user and tokenenticated:
    if not user or not user.verify_reset_token(token):
        flash("The password reset link is invalid or has expired.", "error")
        return redirect(url_for('forgot_password'))
    user = User.query.get(user_id)
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        flash("The password reset link is invalid or has expired.", "error")
        # Validate password_for('forgot_password'))
        if not password or len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return render_template('reset_password.html', user_id=user_id, token=token)
        confirm_password = request.form.get('confirm_password')
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template('reset_password.html', user_id=user_id, token=token)
            flash("Password must be at least 8 characters long.", "error")
        # Update password_template('reset_password.html', user_id=user_id, token=token)
        user.set_password(password)
        # Clear reset tokenirm_password:
        user.clear_reset_token()not match.", "error")
            return render_template('reset_password.html', user_id=user_id, token=token)
        db.session.commit()
        flash("Your password has been successfully reset. You can now log in with your new password.", "success")
        return redirect(url_for('login'))
        # Clear reset token
    return render_template('reset_password.html', user_id=user_id, token=token)
        
@app.cli.command("add-reset-columns")
def add_reset_columns_cmd(): has been successfully reset. You can now log in with your new password.", "success")
    """Add password reset columns to the user table."""
    inspector = db.inspect(db.engine)
    user_columns = [col['name'] for col in inspector.get_columns('user')]token)
    
    with db.engine.connect() as conn:
        columns_added = False
        if 'reset_token' not in user_columns: table."""
            print("Adding reset_token column to user table...")
            conn.execute(db.text("ALTER TABLE user ADD COLUMN reset_token VARCHAR(100)"))
            columns_added = True
         db.engine.connect() as conn:
        if 'reset_token_expiration' not in user_columns:
            print("Adding reset_token_expiration column to user table...")
            conn.execute(db.text("ALTER TABLE user ADD COLUMN reset_token_expiration DATETIME"))
            columns_added = True("ALTER TABLE user ADD COLUMN reset_token VARCHAR(100)"))
            columns_added = True
        if columns_added:
            conn.commit()xpiration' not in user_columns:
            print("Password reset columns added successfully!") table...")
        else:onn.execute(db.text("ALTER TABLE user ADD COLUMN reset_token_expiration DATETIME"))
            print("No changes needed. Password reset columns already exist.")
        
@app.route('/user/profile', methods=['GET'])
@login_requiredn.commit()
def user_profile():Password reset columns added successfully!")
    """Display the user profile page."""
    # IMPROVED: Better handling of notification preferences with defaultst.")
    notification_preferences = {
        'enable_email': False,thods=['GET'])
        'email_format': 'html', 
        'notification_frequency': 'daily'
    }""Display the user profile page."""
    # IMPROVED: Better handling of notification preferences with defaults
    if current_user.notification_preferences:
        if isinstance(current_user.notification_preferences, str):
            try:ormat': 'html', 
                import jsonency': 'daily'
                saved_prefs = json.loads(current_user.notification_preferences)
                # Update defaults with saved values
                notification_preferences.update(saved_prefs)
                app.logger.debug(f"Loaded preferences: {notification_preferences}")
            except (json.JSONDecodeError, TypeError) as e:
                app.logger.error(f"Error loading preferences: {str(e)}")
        else:   saved_prefs = json.loads(current_user.notification_preferences)
            # It's already a dictionarysaved values
            notification_preferences.update(current_user.notification_preferences)
                app.logger.debug(f"Loaded preferences: {notification_preferences}")
    return render_template('user_profile.html', ror) as e:
                          notification_preferences=notification_preferences)
        else:
@app.route('/user/profile/update', methods=['POST'])
@login_requiredification_preferences.update(current_user.notification_preferences)
def update_profile():
    """Update user profile information."""tml', 
    if request.method == 'POST':cation_preferences=notification_preferences)
        # Get form data
        full_name = request.form.get('full_name')'])
        email = request.form.get('email')
        te_profile():
        # Update user informationation."""
        current_user.full_name = full_name
        current_user.email = email
        db.session.commit().form.get('full_name')
        email = request.form.get('email')
        flash('Profile updated successfully', 'success')
        return redirect(url_for('user_profile'))
        current_user.full_name = full_name
@app.route('/user/profile/change-password', methods=['POST'])
@login_requiredion.commit()
def change_password():
    """Change user password."""successfully', 'success')
    if request.method == 'POST':'user_profile'))
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')OST'])
        confirm_password = request.form.get('confirm_password')
        ge_password():
        # Verify current password
        if not check_password_hash(current_user.password_hash, current_password):
            flash('Current password is incorrect', 'error')rd')
            return redirect(url_for('user_profile'))d')
        confirm_password = request.form.get('confirm_password')
        # Verify new passwords match
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')_hash, current_password):
            return redirect(url_for('user_profile'))error')
            return redirect(url_for('user_profile'))
        # Update password
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()confirm_password:
            flash('New passwords do not match', 'error')
        flash('Password changed successfully', 'success')
        return redirect(url_for('user_profile'))
        # Update password
@app.route('/user/notification_preferences', methods=['POST'])w_password)
@login_requiredion.commit()
def update_notification_preferences():
    """Update user notification preferences""" 'success')
    try:return redirect(url_for('user_profile'))
        # Get form data - ensure all fields are correctly retrieved
        enable_email = 'enable_email' in request.form['POST'])
        email_format = request.form.get('email_format', 'html')
        notification_frequency = request.form.get('notification_frequency', 'immediate')
        pdate user notification preferences"""
        app.logger.debug(f"Form data: enable_email={enable_email}, email_format={email_format}, notification_frequency={notification_frequency}")
        # Get form data - ensure all fields are correctly retrieved
        # Initialize preferences dictionaryquest.form
        notification_prefs = {}form.get('email_format', 'html')
        notification_frequency = request.form.get('notification_frequency', 'immediate')
        # Convert string to dictionary if necessary
        if isinstance(current_user.notification_preferences, str) and current_user.notification_preferences:_frequency={notification_frequency}")
            try:
                import jsonences dictionary
                notification_prefs = json.loads(current_user.notification_preferences)
            except (json.JSONDecodeError, TypeError) as e:
                app.logger.error(f"Error parsing preferences JSON: {str(e)}")
                notification_prefs = {}fication_preferences, str) and current_user.notification_preferences:
        elif current_user.notification_preferences is None or current_user.notification_preferences == '':
            notification_prefs = {}
        else:   notification_prefs = json.loads(current_user.notification_preferences)
            # If it's already a dictionaryTypeError) as e:
            notification_prefs = current_user.notification_preferencesr(e)}")
                notification_prefs = {}
        # Update the preferences - explicitly set each fieldr current_user.notification_preferences == '':
        notification_prefs['enable_email'] = enable_email
        notification_prefs['email_format'] = email_format
        notification_prefs['notification_frequency'] = notification_frequency
            notification_prefs = current_user.notification_preferences
        app.logger.debug(f"Updated preferences: {notification_prefs}")
        # Update the preferences - explicitly set each field
        # Save back to user object (always as a JSON string)
        import jsonn_prefs['email_format'] = email_format
        serialized_prefs = json.dumps(notification_prefs)tification_frequency
        app.logger.debug(f"Serialized preferences: {serialized_prefs}")
        current_user.notification_preferences = serialized_prefsefs}")
        
        # Verify database column can accommodate the serialized data
        if len(serialized_prefs) > 500:  # Assuming your db column has reasonable size
            app.logger.warning(f"Notification preferences JSON exceeds 500 chars: {len(serialized_prefs)}")
        app.logger.debug(f"Serialized preferences: {serialized_prefs}")
        # Save to databaseication_preferences = serialized_prefs
        db.session.commit()
        flash('Notification preferences updated successfully', 'success')
    except Exception as e:prefs) > 500:  # Assuming your db column has reasonable size
        db.session.rollback()g(f"Notification preferences JSON exceeds 500 chars: {len(serialized_prefs)}")
        app.logger.error(f"Error updating preferences: {str(e)}")
        flash(f'Error updating notification preferences: {str(e)}', 'error')
        db.session.commit()
    return redirect(url_for('user_profile'))ted successfully', 'success')
    except Exception as e:
@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_requiredger.error(f"Error updating preferences: {str(e)}")
def edit_user(user_id):pdating notification preferences: {str(e)}', 'error')
    if not current_user.is_admin:
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for('dashboard'))
    user = User.query.get_or_404(user_id)d>', methods=['GET', 'POST'])
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')s this page", "danger")
        email = request.form.get('email')d'))
        role_id = request.form.get('role_id') or None
        is_admin = 'is_admin' in request.form
        sites = request.form.getlist('sites')')
        password = request.form.get('password')
        # Update the user's detailst('full_name')
        user.username = username('email')
        user.full_name = full_name('role_id') or None
        user.email = emailin' in request.form
        user.role_id = role_idetlist('sites')
        user.is_admin = is_admin
        # Update the user's details
        # Update password only if provided
        if password:me = full_name
            user.set_password(password)
        user.role_id = role_id
        # Update site assignments
        user.sites = []
        for site_id in sites:y if provided
            site = Site.query.get(site_id)
            if site:_password(password)
                user.sites.append(site)
        # Update site assignments
        db.session.commit()
        flash(f'User "{username}" updated successfully!', 'success')
        return redirect(url_for('manage_users'))
    roles = Role.query.all()
    sites = Site.query.all()ppend(site)
    return render_template('admin/edit_user.html', user=user, roles=roles, sites=sites)  # Changed from admin_edit_user_modern.html
        db.session.commit()
# New routes for checking and sending notificationslly!', 'success')
@app.route('/admin/check_notifications')users'))
@login_requirede.query.all()
def admin_check_notifications():  # Changed from check_notifications to admin_check_notifications
    """Check for maintenance notifications"""tml', user=user, roles=roles, sites=sites)  # Changed from admin_edit_user_modern.html
    if not current_user.is_admin and not current_user.has_permission('admin.access'):
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for('dashboard'))
    in_required
    now = datetime.utcnow()ns():  # Changed from check_notifications to admin_check_notifications
    sites = Site.query.all() notifications"""
    if not current_user.is_admin and not current_user.has_permission('admin.access'):
    # Count statsu don't have permission to access this page", "danger")
    overdue_count = 0ct(url_for('dashboard'))
    due_soon_count = 0
    sites_with_notifications = 0
    sites = Site.query.all()
    for site in sites:
        if site.enable_notifications:
            sites_with_notifications += 1
        soon_count = 0
        for machine in site.machines:
            for part in machine.parts:
                days_until = (part.next_maintenance - now).days
                if days_until < 0:ns:
                    overdue_count += 1= 1
                elif days_until <= site.notification_threshold:
                    due_soon_count += 1
            for part in machine.parts:
    return render_template('admin/notifications.html',   # Changed from admin_notifications_modern.html
                          sites=sites,         
                          now=now, = 1
                          overdue_count=overdue_count,hreshold:
                          due_soon_count=due_soon_count,
                          sites_with_notifications=sites_with_notifications,
                          total_sites=len(sites))tml',   # Changed from admin_notifications_modern.html
                          sites=sites,         
@app.route('/admin/send_notifications', methods=['POST'])
@login_required           overdue_count=overdue_count,
def admin_send_notifications():  # Changed from send_notifications to admin_send_notifications
    """Send maintenance notifications to sites"""s=sites_with_notifications,
    if not current_user.is_admin and not current_user.has_permission('admin.access'):
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for('dashboard'))ds=['POST'])
    in_required
    success_count = 0cations():  # Changed from send_notifications to admin_send_notifications
    error_count = 0ance notifications to sites"""
    now = datetime.utcnow()admin and not current_user.has_permission('admin.access'):
    sites = Site.query.all()e permission to access this page", "danger")
        return redirect(url_for('dashboard'))
    for site in sites:
        if not site.enable_notifications or not site.contact_email:
            continue
        = datetime.utcnow()
        overdue_parts = []()
        due_soon_parts = []
        site in sites:
        for machine in site.machines:ons or not site.contact_email:
            for part in machine.parts:
                days_until = (part.next_maintenance - now).days
                if days_until < 0:
                    overdue_parts.append(part)
                elif days_until <= site.notification_threshold:
                    due_soon_parts.append(part)
            for part in machine.parts:
        # Skip if no parts need attentionaintenance - now).days
        if not overdue_parts and not due_soon_parts:
            continueoverdue_parts.append(part)
                elif days_until <= site.notification_threshold:
        # For all users assigned to this sitet)
        site_users = site.users
        for user in site_users: attention
            # Get notification preferencesoon_parts:
            preferences = user.get_notification_preferences()
            if not preferences.get('enable_email', True):
                continueassigned to this site
            _users = site.users
            # Check if this is an immediate notification
            if preferences.get('email_frequency') != 'immediate':
                continue= user.get_notification_preferences()
            if not preferences.get('enable_email', True):
            # Check notification types the user wants to receive
            notification_types = preferences.get('notification_types', ['overdue', 'due_soon'])
            # Check if this is an immediate notification
            # Only send if there are parts that match the user's notification types
            if ('overdue' in notification_types and overdue_parts) or ('due_soon' in notification_types and due_soon_parts):
                try:
                    # Prepare email contentuser wants to receive
                    subject = f"Maintenance Needed at {site.name}"es', ['overdue', 'due_soon'])
                    
                    # Filter parts based on user preferenceser's notification types
                    filtered_overdue = overdue_parts if 'overdue' in notification_types else []on_types and due_soon_parts):
                    filtered_due_soon = due_soon_parts if 'due_soon' in notification_types else []
                    # Prepare email content
                    # Create email contente Needed at {site.name}"
                    html = render_template(
                        'email/maintenance_notification.html',
                        site=site,ue = overdue_parts if 'overdue' in notification_types else []
                        overdue_parts=filtered_overdue,if 'due_soon' in notification_types else []
                        due_soon_parts=filtered_due_soon,
                        user=user, content
                        now=nower_template(
                    )   'email/maintenance_notification.html',
                        site=site,
                    # Send emailparts=filtered_overdue,
                    msg = Message(subject=subject,e_soon,
                                recipients=[user.email],
                                html=html,
                                sender=app.config['MAIL_DEFAULT_SENDER'])
                    mail.send(msg)
                    success_count += 1
                except Exception as e:ect=subject,
                    app.logger.error(f"Failed to send notification email: {str(e)}")
                    error_count += 1=html,
                                sender=app.config['MAIL_DEFAULT_SENDER'])
    if success_count > 0:send(msg)
        flash(f"Successfully sent {success_count} notification emails", "success")
    if error_count > 0:Exception as e:
        flash(f"Failed to send {error_count} notification emails. Check the logs for details.", "warning")
    if success_count == 0 and error_count == 0:
        flash("No notification emails were sent. This could mean there are no immediate notifications configured or no maintenance is currently due.", "info")
    if success_count > 0:
    return redirect(url_for('admin_check_notifications'))ation emails", "success")
    if error_count > 0:
@app.cli.command("add-notification-preferences")ification emails. Check the logs for details.", "warning")
def add_notification_preferences_cmd():nt == 0:
    """Add notification preferences column to the user table.""" there are no immediate notifications configured or no maintenance is currently due.", "info")
    inspector = db.inspect(db.engine)
    user_columns = [col['name'] for col in inspector.get_columns('user')]
    
    with db.engine.connect() as conn:eferences")
        if 'notification_preferences' not in user_columns:
            print("Adding notification_preferences column to user table...")
            conn.execute(text("ALTER TABLE user ADD COLUMN notification_preferences TEXT DEFAULT '{}'"))
            conn.commit()name'] for col in inspector.get_columns('user')]
            print("Notification preferences column added successfully!")
        else:ngine.connect() as conn:
            print("No changes needed. Notification preferences column already exists.")
            print("Adding notification_preferences column to user table...")
@app.route('/debug-info')text("ALTER TABLE user ADD COLUMN notification_preferences TEXT DEFAULT '{}'"))
def debug_info():commit()
    """Show debug information to help diagnose issues."""successfully!")
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # If this is an AJAX request, return JSONn preferences column already exists.")
        data = {
            "server_time": datetime.utcnow().isoformat(),
            "ajax_detected": True
        }ow debug information to help diagnose issues."""
        return jsonify(data)X-Requested-With') == 'XMLHttpRequest':
        # If this is an AJAX request, return JSON
    if not current_user.is_authenticated or not current_user.is_admin:
        return "Not authorized", 403utcnow().isoformat(),
            "ajax_detected": True
    # ...existing code...
        return jsonify(data)
@app.route('/api/health')
def api_health():t_user.is_authenticated or not current_user.is_admin:
    return jsonify({authorized", 403
        'status': 'ok',
        'version': '1.0.0',
        'message': 'API is running'
    })oute('/api/health')
def api_health():
@app.route('/debug/db-status')
def debug_db_status():',
    """Check database status and configuration"""
    if not current_user.is_authenticated or not current_user.is_admin:
        return "Not authorized", 403

















































    app.run(host='0.0.0.0', port=port)    port = int(os.environ.get('PORT', 5050))    ensure_email_templates()    ensure_env_file()if __name__ == '__main__':        return jsonify({'error': str(e), 'traceback': traceback.format_exc()})    except Exception as e:        return jsonify(info)                }            'db_stats': db_stats            'persistence_info': db_persistence_info,            'database_uri': db_uri,        info = {                db_stats['part_count'] = Part.query.count()        db_stats['machine_count'] = Machine.query.count()        db_stats['site_count'] = Site.query.count()        db_stats['user_count'] = User.query.count()        db_stats = {}        # Get basic statistics from database                        db_persistence_info['render_env'] = False        else:            db_persistence_info['disk_free'] = disk_usage.free            db_persistence_info['disk_used'] = disk_usage.used            db_persistence_info['disk_total'] = disk_usage.total            disk_usage = shutil.disk_usage(data_path)            import shutil            # Check disk space                            db_persistence_info['db_size'] = os.path.getsize(db_path)             if os.path.exists(db_path):                        db_persistence_info['db_exists'] = os.path.exists(db_path)            db_persistence_info['data_path_exists'] = os.path.exists(data_path)            db_persistence_info['render_env'] = True                        db_path = '/var/data/maintenance.db'            data_path = '/var/data'        if os.environ.get('RENDER'):        # Get Render disk info if applicable                db_persistence_info = {}        db_uri = app.config['SQLALCHEMY_DATABASE_URI']        # Database location info    try:    
if __name__ == '__main__':
    ensure_env_file()
    ensure_email_templates()
    port = int(os.environ.get('PORT', 5050))
    app.run(host='0.0.0.0', port=port)