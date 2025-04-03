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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')

# Configure the database
configure_database(app)

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

# Initialize database
db = SQLAlchemy(app)

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
    SITES_VIEW_ASSIGNED = 'sites.view.assigned'  # New permission for viewing only assigned siteses.view'
    SITES_CREATE = 'sites.create'tes.view.assigned'  # New permission for viewing only assigned sites
    SITES_EDIT = 'sites.edit'
    SITES_DELETE = 'sites.delete'
    # Machine management
    MACHINES_VIEW = 'machines.view'
    MACHINES_CREATE = 'machines.create'w'
    MACHINES_EDIT = 'machines.edit'achines.create'
    MACHINES_DELETE = 'machines.delete'
    # Part management
    PARTS_VIEW = 'parts.view'
    PARTS_CREATE = 'parts.create'
    PARTS_EDIT = 'parts.edit'
    PARTS_DELETE = 'parts.delete'ts.edit'
    # Maintenance managementete'
    MAINTENANCE_VIEW = 'maintenance.view'
    MAINTENANCE_SCHEDULE = 'maintenance.schedule'ce.view'
    MAINTENANCE_RECORD = 'maintenance.record'enance.schedule'
    # Backup managementance.record'
    BACKUP_VIEW = 'backup.view'
    BACKUP_CREATE = 'backup.create'
    BACKUP_RESTORE = 'backup.restore'
    BACKUP_EXPORT = 'backup.export'
    BACKUP_DELETE = 'backup.delete'
    BACKUP_SCHEDULE = 'backup.schedule'  # New permission for managing scheduled backupsckup.delete'
    # Administrationchedule'  # New permission for managing scheduled backups
    ADMIN_ACCESS = 'admin.access'
    ADMIN_FULL = 'admin.full'
    @classmethod
    def get_all_permissions(cls):
        """Return all available permissions as dict mapping permission to description"""
        permissions = {}
        for attr in dir(cls):l available permissions as dict mapping permission to description"""
            if not attr.startswith('_') and not callable(getattr(cls, attr)) and attr != 'get_all_permissions':
                value = getattr(cls, attr)
                if isinstance(value, str):swith('_') and not callable(getattr(cls, attr)) and attr != 'get_all_permissions':
                    # Format the name for displayvalue = getattr(cls, attr)
                    category, action = value.split('.')[0:2]ue, str):
                    if len(value.split('.')) > 2:
                        # Handle cases like 'sites.view.assigned'
                        modifier = value.split('.')[2]lue.split('.')) > 2:
                        display = f"{category.capitalize()} - {action.capitalize()} ({modifier})"
                    else:
                        display = f"{category.capitalize()} - {action.capitalize()}"ory.capitalize()} - {action.capitalize()} ({modifier})"
                    permissions[value] = display
        return permissions- {action.capitalize()}"

# Define database models
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    permissions = db.Column(db.String(500), default="view")
    users = db.relationship('User', backref='role', lazy=True)
    def has_permission(self, permission):n(db.String(500), default="view")
        return permission in self.permissions.split(',')hip('User', backref='role', lazy=True)
    def get_permissions_list(self):
        return self.permissions.split(',')

user_site = db.Table('user_site',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('site_id', db.Integer, db.ForeignKey('site.id'), primary_key=True),
)

class User(db.Model, UserMixin):.id'), primary_key=True),
    id = db.Column(db.Integer, primary_key=True).id'), primary_key=True),
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))imary_key=True)
    sites = db.relationship('Site', secondary=user_site, lazy='subquery',
                           backref=db.backref('users', lazy=True))
    email = db.Column(db.String(100))
    full_name = db.Column(db.String(100))   role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    reset_token = db.Column(db.String(100))e', secondary=user_site, lazy='subquery',
    reset_token_expiration = db.Column(db.DateTime)sers', lazy=True))
    notification_preferences = db.Column(db.Text, default='{}')  # Add this column for storing preferences as JSON string
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)is column for storing preferences as JSON string
    def has_permission(self, permission):
        if self.is_admin:
            return Truesword_hash(password)
        if self.role:
            # Direct permission check
            if self.role.has_permission(permission):
                return True
            # Check for full admin access to this categoryon):
            if '.' in permission:
                category = permission.split('.')[0]
                if self.role.has_permission(f'{category}.full'):
                    return True
            # Check for admin permission
            if permission.startswith('admin.') and self.role.has_permission('admin.full'):
                return True to this category
        return Falsemission:
    def generate_reset_token(self):y = permission.split('.')[0]
        # Generate a secure token for password resetission(f'{category}.full'):
        token = secrets.token_urlsafe(32)
        self.reset_token = token
        # Token expires after 1 hourle.has_permission('admin.full'):
        self.reset_token_expiration = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        return token
    def verify_reset_token(self, token):
        # Verify the reset token is valid and not expiredssword reset
        if self.reset_token != token:
            return False
        if not self.reset_token_expiration or self.reset_token_expiration < datetime.utcnow():er 1 hour
            return Falseoken_expiration = datetime.utcnow() + timedelta(hours=1)
        return True
    def clear_reset_token(self):
        # Clear the reset token after use
        self.reset_token = None
        self.reset_token_expiration = Nonevalid and not expired
        db.session.commit()
    def get_notification_preferences(self):
        """Get notification preferences with defaults for missing values"""oken_expiration or self.reset_token_expiration < datetime.utcnow():
        import jsonalse
        try:
            # Try to parse stored preferences
            if self.notification_preferences:
                prefs = json.loads(self.notification_preferences) use
            else:
                prefs = {}
        except:t()
            prefs = {}
        # Set defaults for missing keysnces(self):
        if 'enable_email' not in prefs:ith defaults for missing values"""
            prefs['enable_email'] = True
        if 'email_frequency' not in prefs:
            prefs['email_frequency'] = 'weekly'ces
        if 'notification_types' not in prefs:ation_preferences:
            prefs['notification_types'] = ['overdue', 'due_soon']ification_preferences)
        return prefs

class Site(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    machines = db.relationship('Machine', backref='site', lazy=True, cascade="all, delete-orphan")
    enable_notifications = db.Column(db.Boolean, default=False)y' not in prefs:
    contact_email = db.Column(db.String(100))  # Contact email for notificationsrequency'] = 'weekly'
    notification_threshold = db.Column(db.Integer, default=30)  # Days before due date to notifyon_types' not in prefs:
    def get_parts_status(self, now=None): = ['overdue', 'due_soon']
        """Return counts of parts by status (overdue, due_soon, ok)"""
        if now is None:
            now = datetime.utcnow()
        overdue_parts = [])
        due_soon_parts = []alse)
        ok_parts = []
        for machine in self.machines:ue, cascade="all, delete-orphan")
            for part in machine.parts:ions = db.Column(db.Boolean, default=False)
                days_until = (part.next_maintenance - now).daysb.Column(db.String(100))  # Contact email for notifications
                if days_until < 0:r, default=30)  # Days before due date to notify
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
next_maintenance - now).days
class Machine(db.Model):
    id = db.Column(db.Integer, primary_key=True)_parts.append(part)
    name = db.Column(db.String(100), nullable=False)ntil <= self.notification_threshold:
    model = db.Column(db.String(100))pend(part)
    site_id = db.Column(db.Integer, db.ForeignKey('site.id'), nullable=False)
    parts = db.relationship('Part', backref='machine', lazy=True, cascade="all, delete-orphan")
    machine_number = db.Column(db.String(100))  # New column for machine number
    serial_number = db.Column(db.String(100))  # New column for serial number
    maintenance_logs = db.relationship('MaintenanceLog', backref='machine', lazy=True, cascade="all, delete-orphan")

class Part(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)y_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)llable=False)
    maintenance_frequency = db.Column(db.Integer, default=7)  # in days
    maintenance_unit = db.Column(db.String(10), default='day')  # 'day', 'week', 'month', or 'year'Integer, db.ForeignKey('site.id'), nullable=False)
    last_maintenance = db.Column(db.DateTime, default=datetime.utcnow) = db.relationship('Part', backref='machine', lazy=True, cascade="all, delete-orphan")
    next_maintenance = db.Column(db.DateTime)Column(db.String(100))  # New column for machine number
    notification_sent = db.Column(db.Boolean, default=False)  # Track if notification has been sent New column for serial number
    last_maintained_by = db.Column(db.String(100))  # New field for who performed maintenanceog', backref='machine', lazy=True, cascade="all, delete-orphan")
    invoice_number = db.Column(db.String(50))  # New field for invoice tracking
    def __init__(self, **kwargs):
        # Extract frequency and unit if provided
        frequency = kwargs.get('maintenance_frequency', 7)
        unit = kwargs.get('maintenance_unit', 'day')
        # Convert to days for internal storage
        if 'maintenance_frequency' in kwargs and 'maintenance_unit' in kwargs:
            kwargs['maintenance_frequency'] = self.convert_to_days(frequency, unit)= db.Column(db.String(10), default='day')  # 'day', 'week', 'month', or 'year'
        super(Part, self).__init__(**kwargs)fault=datetime.utcnow)
        if 'maintenance_frequency' in kwargs and 'last_maintenance' in kwargs:
            self.update_next_maintenance()t=False)  # Track if notification has been sent
    def update_next_maintenance(self):aintenance
        """Update next maintenance date and reset notification status"""
        self.next_maintenance = self.last_maintenance + timedelta(days=self.maintenance_frequency)
        self.notification_sent = False  # Reset notification status when maintenance is done
    @staticmethod
    def convert_to_days(value, unit):
        """Convert a value from specified unit to days"""
        value = int(value)
        if unit == 'day':
            return valuerequency'] = self.convert_to_days(frequency, unit)
        elif unit == 'week':
            return value * 7ntenance' in kwargs:
        elif unit == 'month':
            return value * 30
        elif unit == 'year':
            return value * 365
        else:ance_frequency)
            return value  # Default to daysenance is done
    def get_frequency_display(self):
        """Return a human-readable frequency with appropriate unit"""
        days = self.maintenance_frequency
        if days % 365 == 0 and days >= 365:
            return f"{days // 365} {'year' if days // 365 == 1 else 'years'}"
        elif days % 30 == 0 and days >= 30:
            return f"{days // 30} {'month' if days // 30 == 1 else 'months'}"
        elif days % 7 == 0 and days >= 7: == 'week':
            return f"{days // 7} {'week' if days // 7 == 1 else 'weeks'}"
        else:
            return f"{days} {'day' if days == 1 else 'days'}"
':
class MaintenanceLog(db.Model):* 365
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)Default to days
    part_id = db.Column(db.Integer, db.ForeignKey('part.id'), nullable=False)
    performed_by = db.Column(db.String(100), nullable=False)(self):
    invoice_number = db.Column(db.String(50))dable frequency with appropriate unit"""
    maintenance_date = db.Column(db.DateTime, default=datetime.utcnow)e_frequency
    notes = db.Column(db.Text) days >= 365:
    # Reference to the part to track which part was maintainedif days // 365 == 1 else 'years'}"
    part = db.relationship('Part', backref='maintenance_logs')
month' if days // 30 == 1 else 'months'}"
@login_manager.user_loader
def load_user(user_id):s'}"
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))ble=False)
    return redirect(url_for('login'))lse)

@app.route('/login', methods=['GET', 'POST'])
def login():n(db.DateTime, default=datetime.utcnow)
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
            return redirect(url_for(next_page))henticated:
        flash('Invalid username or password')l_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')gin', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
username')
@app.route('/dashboard')')
@login_requiredusername).first()
def dashboard():rd(password):
    # Filter sites based on user access and permissions
    if current_user.is_admin:lt to dashboard
        # Admins see all sites, 'dashboard')
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
        'dashboard.html',d')
        sites=sites,
        machines=machines,:
        now=now,s based on user access and permissions
        is_admin=current_user.is_admin,
        current_user=current_user,
    )ry.all()
s_permission(Permissions.SITES_VIEW):
@app.cli.command("init-db")Site.query.all()
def init_db():VIEW_ASSIGNED):
    """Initialize the database with sample data."""
    db.create_all()
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        # Create roles first
        admin_role = Role(name='Administrator', description='Full system access',
                          permissions=','.join([
                              # ...existing permissions...
                          ]))achines,
        # ...existing code for other roles...
        db.session.add_all([admin_role, manager_role, technician_role])dmin,
        db.session.commit()
        
        # Create admin user with randomly generated password
        import secrets
        admin_password = secrets.token_urlsafe(12)  # Generate secure random password
        admin = User(username='admin', full_name='Administrator', email='admin@example.com', is_admin=True, role_id=admin_role.id)
        admin.set_password(admin_password)050))
        db.session.add(admin)port)        db.session.commit()                # Display the generated password to console only during initialization        print("\n" + "=" * 40)        print("ADMIN ACCOUNT CREATED")        print(f"Username: admin")
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