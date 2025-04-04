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

# Add session configuration to work across networks one admin exists after fresh deployments
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True only if using HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = Trueexist in the database"""
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')  # Optional, use for multi-domain setup
        
# Configure caching for static assetsned and users table exists
if 'configure_caching' in globals() or 'configure_caching' in locals():
    configure_caching(app) users exist
            user_count = User.query.count()
# Email configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.example.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))eating default admin user.")
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', 'yes', '1')
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')ator").first()
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'maintenance@example.com')
# Initialize Flask-Mailin_role = Role(
mail = Mail(app)        name="Administrator",
                        description="Full system access",
# Initialize login managerrmissions=",".join(Permissions.get_all_permissions())
login_manager = LoginManager()
login_manager.init_app(app)ion.add(admin_role)
login_manager.login_view = 'login'mit()
                
# Custom decorator to require admin accessr
def admin_required(f):t_password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123')  # Can be set in env vars
    @wraps(f)   admin_user = User(
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:ssword_hash(default_password),
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login', next=request.url))
        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_functiond(admin_user)
                db.session.commit()
# Utility function for permission checkingefault admin user 'admin' with provided or default password.")
def require_permission(permission):PORTANT: Please change this password immediately after first login.")
    def decorator(func):
        @wraps(func)t(f"[STARTUP] Found {user_count} existing users in database.")
        def wrapper(*args, **kwargs):
            if not current_user.has_permission(permission):dmin: {str(e)}")
                flash(f'Access denied. You need {permission} permission.')
                return redirect(url_for('dashboard'))
            return func(*args, **kwargs)lse  # Set to True only if using HTTPS
        return wrapperOKIE_HTTPONLY'] = True
    return decoratorCOOKIE_SAMESITE'] = 'Lax'
app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')  # Optional, use for multi-domain setup
# Define permission constants for better organization and consistency
class Permissions:g for static assets
    # User management' in globals() or 'configure_caching' in locals():
    USERS_VIEW = 'users.view'
    USERS_CREATE = 'users.create'
    USERS_EDIT = 'users.edit'
    USERS_DELETE = 'users.delete'viron.get('MAIL_SERVER', 'smtp.example.com')
    config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    # Role managementTLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', 'yes', '1')
    ROLES_VIEW = 'roles.view' os.environ.get('MAIL_USERNAME', '')
    ROLES_CREATE = 'roles.create'environ.get('MAIL_PASSWORD', '')
    ROLES_EDIT = 'roles.edit'ER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'maintenance@example.com')
    ROLES_DELETE = 'roles.delete'
     = Mail(app)
    # Site management
    SITES_VIEW = 'sites.view'
    SITES_VIEW_ASSIGNED = 'sites.view.assigned'  # New permission for viewing only assigned sites
    SITES_CREATE = 'sites.create'
    SITES_EDIT = 'sites.edit'ogin'
    SITES_DELETE = 'sites.delete'
    stom decorator to require admin access
    # Machine management
    MACHINES_VIEW = 'machines.view'
    MACHINES_CREATE = 'machines.create'rgs):
    MACHINES_EDIT = 'machines.edit'enticated:
    MACHINES_DELETE = 'machines.delete'ess this page.', 'error')
            return redirect(url_for('login', next=request.url))
    # Part managementt_user.is_admin:
    PARTS_VIEW = 'parts.view' have permission to access this page.', 'error')
    PARTS_CREATE = 'parts.create'or('dashboard'))
    PARTS_EDIT = 'parts.edit'rgs)
    PARTS_DELETE = 'parts.delete'
    
    # Maintenance managementssion checking
    MAINTENANCE_VIEW = 'maintenance.view'
    MAINTENANCE_SCHEDULE = 'maintenance.schedule'
    MAINTENANCE_RECORD = 'maintenance.record'
        def wrapper(*args, **kwargs):
    # Backup managementent_user.has_permission(permission):
    BACKUP_VIEW = 'backup.view'denied. You need {permission} permission.')
    BACKUP_CREATE = 'backup.create'_for('dashboard'))
    BACKUP_RESTORE = 'backup.restore'gs)
    BACKUP_EXPORT = 'backup.export'
    BACKUP_DELETE = 'backup.delete'
    BACKUP_SCHEDULE = 'backup.schedule'  # New permission for managing scheduled backups
    fine permission constants for better organization and consistency
    # Administration
    ADMIN_ACCESS = 'admin.access'
    ADMIN_FULL = 'admin.full'
    USERS_CREATE = 'users.create'
    @classmethod 'users.edit'
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
                        # Handle cases like 'sites.view.assigned' for viewing only assigned sites
                        modifier = value.split('.')[2]
                        display = f"{category.capitalize()} - {action.capitalize()} ({modifier})"
                    else:.delete'
                        display = f"{category.capitalize()} - {action.capitalize()}"
                    permissions[value] = display
        return permissionsnes.view'
    MACHINES_CREATE = 'machines.create'
# Define database modelshines.edit'
class Role(db.Model): 'machines.delete'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    permissions = db.Column(db.String(500), default="view")
    users = db.relationship('User', backref='role', lazy=True)
    def has_permission(self, permission):
        return permission in self.permissions.split(',')
    def get_permissions_list(self):
        return self.permissions.split(',')
    MAINTENANCE_SCHEDULE = 'maintenance.schedule'
user_site = db.Table('user_site',ance.record'
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('site_id', db.Integer, db.ForeignKey('site.id'), primary_key=True),
)   BACKUP_VIEW = 'backup.view'
    BACKUP_CREATE = 'backup.create'
class User(db.Model, UserMixin):tore'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False) managing scheduled backups
    is_admin = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    sites = db.relationship('Site', secondary=user_site, lazy='subquery',
                           backref=db.backref('users', lazy=True))
    email = db.Column(db.String(100))
    full_name = db.Column(db.String(100))
    reset_token = db.Column(db.String(100))
    reset_token_expiration = db.Column(db.DateTime) mapping permission to description"""
    notification_preferences = db.Column(db.Text, default='{}')  # Add this column for storing preferences as JSON string
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)ttr(cls, attr)) and attr != 'get_all_permissions':
    def check_password(self, password):tr)
        return check_password_hash(self.password_hash, password)
    def has_permission(self, permission): display
        if self.is_admin:ory, action = value.split('.')[0:2]
            return Truelen(value.split('.')) > 2:
        if self.role:   # Handle cases like 'sites.view.assigned'
            # Direct permission checklue.split('.')[2]
            if self.role.has_permission(permission):lize()} - {action.capitalize()} ({modifier})"
                return True
            # Check for full admin access to this category} - {action.capitalize()}"
            if '.' in permission:alue] = display
                category = permission.split('.')[0]
                if self.role.has_permission(f'{category}.full'):
                    return True
            # Check for admin permission
            if permission.startswith('admin.') and self.role.has_permission('admin.full'):
                return Trueing(50), unique=True, nullable=False)
        return False.Column(db.String(200))
    def generate_reset_token(self):ng(500), default="view")
        # Generate a secure token for password resetlazy=True)
        token = secrets.token_urlsafe(32)
        self.reset_token = tokenf.permissions.split(',')
        # Token expires after 1 hour
        self.reset_token_expiration = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        return token('user_site',
    def verify_reset_token(self, token):ForeignKey('user.id'), primary_key=True),
        # Verify the reset token is valid and not expiredid'), primary_key=True),
        if self.reset_token != token:
            return False
        if not self.reset_token_expiration or self.reset_token_expiration < datetime.utcnow():
            return Falseteger, primary_key=True)
        return Trueolumn(db.String(100), unique=True, nullable=False)
    def clear_reset_token(self):.String(200), nullable=False)
        # Clear the reset token after useult=False)
        self.reset_token = Noneger, db.ForeignKey('role.id'))
        self.reset_token_expiration = Noneary=user_site, lazy='subquery',
        db.session.commit()backref=db.backref('users', lazy=True))
    def get_notification_preferences(self):
        """Get notification preferences with defaults for missing values"""
        import jsonb.Column(db.String(100))
        try:ken_expiration = db.Column(db.DateTime)
            # Try to parse stored preferencesext, default='{}')  # Add this column for storing preferences as JSON string
            if self.notification_preferences:
                prefs = json.loads(self.notification_preferences)
            else:sword(self, password):
                prefs = {}ord_hash(self.password_hash, password)
        except:mission(self, permission):
            prefs = {}in:
        # Set defaults for missing keys
        if 'enable_email' not in prefs:
            prefs['enable_email'] = True
        if 'email_frequency' not in prefs:rmission):
            prefs['email_frequency'] = 'weekly'
        if 'notification_types' not in prefs:this category
            prefs['notification_types'] = ['overdue', 'due_soon']
        return prefsgory = permission.split('.')[0]
                if self.role.has_permission(f'{category}.full'):
class Site(db.Model):eturn True
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)elf.role.has_permission('admin.full'):
    location = db.Column(db.String(200))
    machines = db.relationship('Machine', backref='site', lazy=True, cascade="all, delete-orphan")
    enable_notifications = db.Column(db.Boolean, default=False)
    contact_email = db.Column(db.String(100))  # Contact email for notifications
    notification_threshold = db.Column(db.Integer, default=30)  # Days before due date to notify
    def get_parts_status(self, now=None):
        """Return counts of parts by status (overdue, due_soon, ok)"""
        if now is None:n_expiration = datetime.utcnow() + timedelta(hours=1)
            now = datetime.utcnow()
        overdue_parts = []
        due_soon_parts = []self, token):
        ok_parts = []reset token is valid and not expired
        for machine in self.machines:
            for part in machine.parts:
                days_until = (part.next_maintenance - now).daysexpiration < datetime.utcnow():
                if days_until < 0:
                    overdue_parts.append(part)
                elif days_until <= self.notification_threshold:
                    due_soon_parts.append(part)
                else:ken = None
                    ok_parts.append(part)e
        return {on.commit()
            'overdue': overdue_parts,self):
            'due_soon': due_soon_parts, with defaults for missing values"""
            'ok': ok_parts,
        }ry:
            # Try to parse stored preferences
class Machine(db.Model):fication_preferences:
    id = db.Column(db.Integer, primary_key=True)tion_preferences)
    name = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100))
    site_id = db.Column(db.Integer, db.ForeignKey('site.id'), nullable=False)
    parts = db.relationship('Part', backref='machine', lazy=True, cascade="all, delete-orphan")
    machine_number = db.Column(db.String(100))  # New column for machine number
    serial_number = db.Column(db.String(100))  # New column for serial number
    maintenance_logs = db.relationship('MaintenanceLog', backref='machine', lazy=True, cascade="all, delete-orphan")
        if 'email_frequency' not in prefs:
class Part(db.Model):ail_frequency'] = 'weekly'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False), 'due_soon']
    description = db.Column(db.Text)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)
    maintenance_frequency = db.Column(db.Integer, default=7)  # in days
    maintenance_unit = db.Column(db.String(10), default='day')  # 'day', 'week', 'month', or 'year'
    last_maintenance = db.Column(db.DateTime, default=datetime.utcnow)
    next_maintenance = db.Column(db.DateTime)
    notification_sent = db.Column(db.Boolean, default=False)  # Track if notification has been sent
    last_maintained_by = db.Column(db.String(100))  # New field for who performed maintenance
    invoice_number = db.Column(db.String(50))  # New field for invoice trackings
    def __init__(self, **kwargs):olumn(db.Integer, default=30)  # Days before due date to notify
        # Extract frequency and unit if provided
        frequency = kwargs.get('maintenance_frequency', 7)soon, ok)"""
        unit = kwargs.get('maintenance_unit', 'day')
        # Convert to days for internal storage
        if 'maintenance_frequency' in kwargs and 'maintenance_unit' in kwargs:
            kwargs['maintenance_frequency'] = self.convert_to_days(frequency, unit)
        super(Part, self).__init__(**kwargs)
        if 'maintenance_frequency' in kwargs and 'last_maintenance' in kwargs:
            self.update_next_maintenance()
    def update_next_maintenance(self):t_maintenance - now).days
        """Update next maintenance date and reset notification status"""
        self.next_maintenance = self.last_maintenance + timedelta(days=self.maintenance_frequency)
        self.notification_sent = False  # Reset notification status when maintenance is done
    @staticmethod   due_soon_parts.append(part)
    def convert_to_days(value, unit):
        """Convert a value from specified unit to days"""
        value = int(value)
        if unit == 'day':erdue_parts,
            return valuedue_soon_parts,
        elif unit == 'week':
            return value * 7
        elif unit == 'month':
            return value * 30
        elif unit == 'year':r, primary_key=True)
            return value * 365(100), nullable=False)
        else:b.Column(db.String(100))
            return value  # Default to daysignKey('site.id'), nullable=False)
    def get_frequency_display(self):backref='machine', lazy=True, cascade="all, delete-orphan")
        """Return a human-readable frequency with appropriate unit"""ine number
        days = self.maintenance_frequency00))  # New column for serial number
        if days % 365 == 0 and days >= 365:ntenanceLog', backref='machine', lazy=True, cascade="all, delete-orphan")
            return f"{days // 365} {'year' if days // 365 == 1 else 'years'}"
        elif days % 30 == 0 and days >= 30:
            return f"{days // 30} {'month' if days // 30 == 1 else 'months'}"
        elif days % 7 == 0 and days >= 7:able=False)
            return f"{days // 7} {'week' if days // 7 == 1 else 'weeks'}"
        else:d = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)
            return f"{days} {'day' if days == 1 else 'days'}" # in days
    maintenance_unit = db.Column(db.String(10), default='day')  # 'day', 'week', 'month', or 'year'
class MaintenanceLog(db.Model):n(db.DateTime, default=datetime.utcnow)
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)on has been sent
    part_id = db.Column(db.Integer, db.ForeignKey('part.id'), nullable=False)rmed maintenance
    performed_by = db.Column(db.String(100), nullable=False)or invoice tracking
    invoice_number = db.Column(db.String(50))
    maintenance_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)('maintenance_frequency', 7)
    # Reference to the part to track which part was maintained
    part = db.relationship('Part', backref='maintenance_logs')
        if 'maintenance_frequency' in kwargs and 'maintenance_unit' in kwargs:
# AFTER all models are defined, THEN create tables.convert_to_days(frequency, unit)
if os.environ.get('RENDER', False):**kwargs)
    with app.app_context():quency' in kwargs and 'last_maintenance' in kwargs:
        try:self.update_next_maintenance()
            db.create_all()ance(self):
            print("Database tables created/verified")ification status"""
            .next_maintenance = self.last_maintenance + timedelta(days=self.maintenance_frequency)
            # Check if any users exist, if not create an admin user when maintenance is done
            user_count = db.session.query(db.func.count(User.id)).scalar()
            print(f"Found {user_count} users in database")
            onvert a value from specified unit to days"""
            if user_count == 0:
                print("No users found - creating default admin account")
                rn value
                # Create admin role first
                admin_role = Role(
                    name='Administrator', 
                    description='Full system access',
                    permissions=','.join([
                        Permissions.ADMIN_FULL,
                        Permissions.SITES_VIEW, 
                        Permissions.SITES_CREATE,
                        Permissions.SITES_EDIT,
                        Permissions.SITES_DELETE, appropriate unit"""
                        Permissions.MACHINES_VIEW,
                        Permissions.MACHINES_CREATE,
                        Permissions.MACHINES_EDIT, // 365 == 1 else 'years'}"
                        Permissions.MACHINES_DELETE,
                        Permissions.PARTS_VIEW,ays // 30 == 1 else 'months'}"
                        Permissions.PARTS_CREATE,
                        Permissions.PARTS_EDIT,s // 7 == 1 else 'weeks'}"
                        Permissions.PARTS_DELETE,
                        Permissions.MAINTENANCE_VIEW,'days'}"
                        Permissions.MAINTENANCE_SCHEDULE,
                        Permissions.MAINTENANCE_RECORD
                    ])Integer, primary_key=True)
                )db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)
                db.session.add(admin_role)eignKey('part.id'), nullable=False)
                db.session.commit()ing(100), nullable=False)
                er = db.Column(db.String(50))
                # Generate a secure password, default=datetime.utcnow)
                import secrets
                admin_password = secrets.token_urlsafe(8)  # 8 char secure random password
                lationship('Part', backref='maintenance_logs')
                # Create admin user
                admin = User(d, THEN create tables
                    username='admin',
                    full_name='Administrator',
                    email='admin@example.com',
                    is_admin=True,
                    role_id=admin_role.idd/verified")
                )
                admin.set_password(admin_password)ate an admin user
                db.session.add(admin)uery(db.func.count(User.id)).scalar()
                db.session.commit()nt} users in database")
                
                # Print credentials to console
                print("\n" + "="*50)d - creating default admin account")
                print("DEFAULT ADMIN ACCOUNT CREATED")
                print("="*50)n role first
                print(f"Username: admin")
                print(f"Password: {admin_password}")
                print("="*50)on='Full system access',
                print("IMPORTANT: Please change this password after logging in!")
                print("="*50 + "\n")ADMIN_FULL,
                        Permissions.SITES_VIEW, 
        except Exception as e:sions.SITES_CREATE,
            print(f"Error during database initialization: {str(e)}")
            print(traceback.format_exc())  # Print full traceback for debugging
                        Permissions.MACHINES_VIEW,
@login_manager.user_loaderrmissions.MACHINES_CREATE,
def load_user(user_id): Permissions.MACHINES_EDIT,
    return User.query.get(int(user_id))HINES_DELETE,
                        Permissions.PARTS_VIEW,
@app.route('/')         Permissions.PARTS_CREATE,
def index():            Permissions.PARTS_EDIT,
    if current_user.is_authenticated:ARTS_DELETE,
        return redirect(url_for('dashboard'))CE_VIEW,
    return redirect(url_for('login'))AINTENANCE_SCHEDULE,
                        Permissions.MAINTENANCE_RECORD
@app.route('/login', methods=['GET', 'POST'])
def login():    )
    if current_user.is_authenticated:role)
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first() char secure random password
        if user and user.check_password(password):
            login_user(user)in user
            # Get the next parameter or default to dashboard
            next_page = request.args.get('next', 'dashboard')
            return redirect(url_for(next_page))
        flash('Invalid username or password'),
    return render_template('login.html')
                    role_id=admin_role.id
@app.route('/logout')
@login_required admin.set_password(admin_password)
def logout():   db.session.add(admin)
    logout_user()b.session.commit()
    return redirect(url_for('login'))
                # Print credentials to console
@app.route('/dashboard')n" + "="*50)
@login_required print("DEFAULT ADMIN ACCOUNT CREATED")
def dashboard():print("="*50)
    # Filter sites based on user access and permissions
    if current_user.is_admin:ord: {admin_password}")
        # Admins see all sites
        sites = Site.query.all(): Please change this password after logging in!")
    elif current_user.has_permission(Permissions.SITES_VIEW):
        sites = Site.query.all()
    elif current_user.has_permission(Permissions.SITES_VIEW_ASSIGNED):
        sites = current_user.siteseeded()
    else:   
        sites = []eption as e:
    now = datetime.utcnow()uring database initialization: {str(e)}")
    machines = Machine.query.all()_exc())  # Print full traceback for debugging
    return render_template(
        'dashboard.html',r
        sites=sites,d):
        machines=machines,int(user_id))
        now=now,
        is_admin=current_user.is_admin,
        current_user=current_user,
    )f current_user.is_authenticated:
        return redirect(url_for('dashboard'))
@app.route('/sites', methods=['GET', 'POST'])
@login_required
def manage_sites():, methods=['GET', 'POST'])
    """Display and manage all sites"""
    # Check permissionsauthenticated:
    if not current_user.has_permission(Permissions.SITES_VIEW) and not current_user.is_admin:
        if current_user.has_permission(Permissions.SITES_VIEW_ASSIGNED):
            # User can only view their assigned sites
            sites = current_user.sitesassword')
        else:= User.query.filter_by(username=username).first()
            flash("You don't have permission to view sites", "error")
            return redirect(url_for('dashboard'))
    else:   # Get the next parameter or default to dashboard
        # Admin or users with view permission can see all sites
        sites = Site.query.all()for(next_page))
        flash('Invalid username or password')
    # Handle form submission for adding a new site
    if request.method == 'POST':
        if not current_user.has_permission(Permissions.SITES_CREATE) and not current_user.is_admin:
            flash("You don't have permission to create sites", "error")
            return redirect(url_for('manage_sites'))
        ut_user()
        name = request.form.get('name')
        location = request.form.get('location')
        contact_email = request.form.get('contact_email')
        notification_threshold = request.form.get('notification_threshold', 30)
        enable_notifications = 'enable_notifications' in request.form
        lter sites based on user access and permissions
        if not name:is_admin:
            flash("Site name is required", "error")
        else: = Site.query.all()
            # Create new sitemission(Permissions.SITES_VIEW):
            new_site = Site(ll()
                name=name,permission(Permissions.SITES_VIEW_ASSIGNED):
                location=location,
                contact_email=contact_email,
                notification_threshold=notification_threshold,
                enable_notifications=enable_notifications
            )= Machine.query.all()
            db.session.add(new_site)
            hboard.html',
            # Assign users if provided
            user_ids = request.form.getlist('user_ids')
            if user_ids:
                for user_id in user_ids:
                    user = User.query.get(user_id)
                    if user:
                        new_site.users.append(user)
            /sites', methods=['GET', 'POST'])
            db.session.commit()
            flash(f"Site '{name}' has been added successfully", "success")
            return redirect(url_for('manage_sites'))
    # Check permissions
    # Get users for site assignmention(Permissions.SITES_VIEW) and not current_user.is_admin:
    users = User.query.all() if current_user.is_admin else []_ASSIGNED):
            # User can only view their assigned sites
    return render_template('sites.html', 
                          sites=sites, 
                          users=users,ission to view sites", "error")
                          now=datetime.utcnow(),)
                          is_admin=current_user.is_admin,
                          can_create=current_user.has_permission(Permissions.SITES_CREATE) or current_user.is_admin,
                          can_edit=current_user.has_permission(Permissions.SITES_EDIT) or current_user.is_admin,
                          can_delete=current_user.has_permission(Permissions.SITES_DELETE) or current_user.is_admin)
    # Handle form submission for adding a new site
@app.route('/sites/<int:site_id>/delete', methods=['POST'])
@login_requiredcurrent_user.has_permission(Permissions.SITES_CREATE) and not current_user.is_admin:
def delete_site(site_id):n't have permission to create sites", "error")
    """Delete a site"""rect(url_for('manage_sites'))
    if not current_user.has_permission(Permissions.SITES_DELETE) and not current_user.is_admin:
        flash("You don't have permission to delete sites", "error")
        return redirect(url_for('manage_sites'))
        contact_email = request.form.get('contact_email')
    site = Site.query.get_or_404(site_id)form.get('notification_threshold', 30)
    site_name = site.nameons = 'enable_notifications' in request.form
        
    # Delete the site and all related data due to cascade
    db.session.delete(site)e is required", "error")
    db.session.commit()
            # Create new site
    flash(f"Site '{site_name}' has been deleted", "success")
    return redirect(url_for('manage_sites'))
                location=location,
@app.route('/sites/<int:site_id>/edit', methods=['GET', 'POST'])
@login_required notification_threshold=notification_threshold,
def edit_site(site_id):notifications=enable_notifications
    """Edit an existing site"""
    site = Site.query.get_or_404(site_id)
            
    # Check permissionsers if provided
    if not current_user.has_permission(Permissions.SITES_EDIT) and not current_user.is_admin:
        flash("You don't have permission to edit sites", "error")
        return redirect(url_for('manage_sites'))
                    user = User.query.get(user_id)
    if request.method == 'POST':
        site.name = request.form.get('name')d(user)
        site.location = request.form.get('location')
        site.contact_email = request.form.get('contact_email')
        site.notification_threshold = request.form.get('notification_threshold', 30)
        site.enable_notifications = 'enable_notifications' in request.form
        
        # Update assigned users if admin
        if current_user.is_admin:urrent_user.is_admin else []
            site.users = []  # Clear existing associations
            user_ids = request.form.getlist('user_ids')
            for user_id in user_ids:s, 
                user = User.query.get(user_id)
                if user:  now=datetime.utcnow(),
                    site.users.append(user)user.is_admin,
                          can_create=current_user.has_permission(Permissions.SITES_CREATE) or current_user.is_admin,
        db.session.commit()an_edit=current_user.has_permission(Permissions.SITES_EDIT) or current_user.is_admin,
        flash(f"Site '{site.name}' has been updated", "success")(Permissions.SITES_DELETE) or current_user.is_admin)
        return redirect(url_for('manage_sites'))
    .route('/sites/<int:site_id>/delete', methods=['POST'])
    users = User.query.all() if current_user.is_admin else []
    return render_template('edit_site.html', site=site, users=users, is_admin=current_user.is_admin)
    """Delete a site"""
@app.route('/machines', methods=['GET', 'POST'])ns.SITES_DELETE) and not current_user.is_admin:
@login_requiredYou don't have permission to delete sites", "error")
def manage_machines():t(url_for('manage_sites'))
    """Display and manage all machines"""
    # Check permissionset_or_404(site_id)
    if not current_user.has_permission(Permissions.MACHINES_VIEW) and not current_user.is_admin:
        flash("You don't have permission to view machines", "error")
        return redirect(url_for('dashboard'))e to cascade
        ession.delete(site)
    # Get all machines, optionally filtered by site
    site_id = request.args.get('site_id', type=int)
    if site_id:e '{site_name}' has been deleted", "success")
        machines = Machine.query.filter_by(site_id=site_id).all()
        site = Site.query.get_or_404(site_id)
        title = f"Machines at {site.name}"thods=['GET', 'POST'])
    else:quired
        machines = Machine.query.all()
        title = "All Machines""
    site = Site.query.get_or_404(site_id)
    # Handle form submission for adding a new machine
    if request.method == 'POST':
        if not current_user.has_permission(Permissions.MACHINES_CREATE) and not current_user.is_admin:
            flash("You don't have permission to create machines", "error")
            return redirect(url_for('manage_machines'))
        
        name = request.form.get('name')
        model = request.form.get('model')e')
        machine_number = request.form.get('machine_number')
        serial_number = request.form.get('serial_number')ail')
        site_id = request.form.get('site_id').form.get('notification_threshold', 30)
        site.enable_notifications = 'enable_notifications' in request.form
        if not name or not site_id:
            flash("Machine name and site are required", "error")
        else:rrent_user.is_admin:
            # Create new machinelear existing associations
            new_machine = Machine(m.getlist('user_ids')
                name=name, user_ids:
                model=model,query.get(user_id)
                machine_number=machine_number,
                serial_number=serial_number,
                site_id=site_id
            )ssion.commit()
            db.session.add(new_machine)been updated", "success")
            db.session.commit()('manage_sites'))
            
            flash(f"Machine '{name}' has been added successfully", "success")
            return redirect(url_for('manage_machines', site_id=site_id))admin=current_user.is_admin)
    
    # Get all sites for dropdown menus, 'POST'])
    sites = Site.query.all()
    manage_machines():
    return render_template('machines.html', 
                          machines=machines,
                          sites=sites,(Permissions.MACHINES_VIEW) and not current_user.is_admin:
                          title=title,on to view machines", "error")
                          site_id=site_id if site_id else None,
                          is_admin=current_user.is_admin,
                          can_create=current_user.has_permission(Permissions.MACHINES_CREATE) or current_user.is_admin,
                          can_edit=current_user.has_permission(Permissions.MACHINES_EDIT) or current_user.is_admin,
                          can_delete=current_user.has_permission(Permissions.MACHINES_DELETE) or current_user.is_admin)
        machines = Machine.query.filter_by(site_id=site_id).all()
@app.route('/machines/<int:machine_id>/edit', methods=['GET', 'POST'])
@login_required f"Machines at {site.name}"
def edit_machine(machine_id):
    """Edit an existing machine"""ll()
    machine = Machine.query.get_or_404(machine_id)
    
    # Check permissionsssion for adding a new machine
    if not current_user.has_permission(Permissions.MACHINES_EDIT) and not current_user.is_admin:
        flash("You don't have permission to edit machines", "error")TE) and not current_user.is_admin:
        return redirect(url_for('manage_machines'))ate machines", "error")
            return redirect(url_for('manage_machines'))
    if request.method == 'POST':
        machine.name = request.form.get('name')
        machine.model = request.form.get('model')
        machine.machine_number = request.form.get('machine_number')
        machine.serial_number = request.form.get('serial_number')
        machine.site_id = request.form.get('site_id')
        
        db.session.commit()site_id:
        flash(f"Machine '{machine.name}' has been updated", "success")
        return redirect(url_for('manage_machines', site_id=machine.site_id))
            # Create new machine
    sites = Site.query.all()chine(
    return render_template('edit_machine.html', machine=machine, sites=sites, is_admin=current_user.is_admin)
                model=model,
@app.route('/machines/<int:machine_id>/delete', methods=['POST'])
@login_required serial_number=serial_number,
def delete_machine(machine_id):
    """Delete a machine"""
    if not current_user.has_permission(Permissions.MACHINES_DELETE) and not current_user.is_admin:
        flash("You don't have permission to delete machines", "error")
        return redirect(url_for('manage_machines'))
            flash(f"Machine '{name}' has been added successfully", "success")
    machine = Machine.query.get_or_404(machine_id)es', site_id=site_id))
    site_id = machine.site_id
    machine_name = machine.namen menus
    sites = Site.query.all()
    db.session.delete(machine)
    db.session.commit()ate('machines.html', 
                          machines=machines,
    flash(f"Machine '{machine_name}' has been deleted", "success")
    return redirect(url_for('manage_machines', site_id=site_id))
                          site_id=site_id if site_id else None,
@app.route('/machines/<int:machine_id>/history')is_admin,
@login_required           can_create=current_user.has_permission(Permissions.MACHINES_CREATE) or current_user.is_admin,
def machine_history(machine_id):it=current_user.has_permission(Permissions.MACHINES_EDIT) or current_user.is_admin,
    """View maintenance history for a specific machine"""mission(Permissions.MACHINES_DELETE) or current_user.is_admin)
    machine = Machine.query.get_or_404(machine_id)
    .route('/machines/<int:machine_id>/edit', methods=['GET', 'POST'])
    # Check permissions - only show if user has access to the site
    if not current_user.is_admin and not machine.site in current_user.sites:
        flash('You do not have permission to view this machine', 'error')
        return redirect(url_for('dashboard'))e_id)
        
    # Get all maintenance logs for parts in this machine
    maintenance_logs = MaintenanceLog.query.join(Part).filter(IT) and not current_user.is_admin:
        Part.machine_id == machine_idion to edit machines", "error")
    ).order_by(MaintenanceLog.maintenance_date.desc()).all()
    
    return render_template('machine_history.html', 
                          machine=machine,ame')
                          maintenance_logs=maintenance_logs, 
                          now=datetime.utcnow())t('machine_number')
        machine.serial_number = request.form.get('serial_number')
@app.route('/parts', methods=['GET', 'POST'])ite_id')
@login_required
def manage_parts():commit()
    """Display and manage all parts"""}' has been updated", "success")
    # Check permissions(url_for('manage_machines', site_id=machine.site_id))
    if not current_user.has_permission(Permissions.PARTS_VIEW) and not current_user.is_admin:
        flash("You don't have permission to view parts", "error")
        return redirect(url_for('dashboard'))', machine=machine, sites=sites, is_admin=current_user.is_admin)
        
    # Get all parts, optionally filtered by machinehods=['POST'])
    machine_id = request.args.get('machine_id', type=int)
    if machine_id:(machine_id):
        parts = Part.query.filter_by(machine_id=machine_id).all()
        machine = Machine.query.get_or_404(machine_id)HINES_DELETE) and not current_user.is_admin:
        title = f"Parts for {machine.name}" delete machines", "error")
    else:eturn redirect(url_for('manage_machines'))
        parts = Part.query.all()
        title = "All Parts".get_or_404(machine_id)
    site_id = machine.site_id
    # Handle form submission for adding a new part
    if request.method == 'POST':
        if not current_user.has_permission(Permissions.PARTS_CREATE) and not current_user.is_admin:
            flash("You don't have permission to create parts", "error")
            return redirect(url_for('manage_parts'))
        h(f"Machine '{machine_name}' has been deleted", "success")
        name = request.form.get('name')hines', site_id=site_id))
        description = request.form.get('description')
        machine_id = request.form.get('machine_id')
        maintenance_frequency = request.form.get('maintenance_frequency')
        maintenance_unit = request.form.get('maintenance_unit')
        iew maintenance history for a specific machine"""
        if not name or not machine_id:(machine_id)
            flash("Part name and machine are required", "error")
        else:ermissions - only show if user has access to the site
            # Create new partmin and not machine.site in current_user.sites:
            new_part = Part(ve permission to view this machine', 'error')
                name=name,l_for('dashboard'))
                description=description,
                machine_id=machine_id,ts in this machine
                maintenance_frequency=maintenance_frequency,r(
                maintenance_unit=maintenance_unit,
                last_maintenance=datetime.utcnow()c()).all()
            )
            db.session.add(new_part)history.html', 
            db.session.commit()ne=machine,
                          maintenance_logs=maintenance_logs, 
            flash(f"Part '{name}' has been added successfully", "success")
            return redirect(url_for('manage_parts', machine_id=machine_id))
    .route('/parts', methods=['GET', 'POST'])
    # Get all machines for dropdown menus
    machines = Machine.query.all()
    """Display and manage all parts"""
    return render_template('parts.html', 
                          parts=parts,(Permissions.PARTS_VIEW) and not current_user.is_admin:
                          machines=machines,view parts", "error")
                          title=title,oard'))
                          now=datetime.utcnow(),
                          machine_id=machine_id if machine_id else None,
                          is_admin=current_user.is_admin,
                          can_create=current_user.has_permission(Permissions.PARTS_CREATE) or current_user.is_admin,
                          can_edit=current_user.has_permission(Permissions.PARTS_EDIT) or current_user.is_admin,
                          can_delete=current_user.has_permission(Permissions.PARTS_DELETE) or current_user.is_admin)
        title = f"Parts for {machine.name}"
@app.route('/parts/<int:part_id>/edit', methods=['GET', 'POST'])
@login_required Part.query.all()
def edit_part(part_id):rts"
    """Edit an existing part"""
    part = Part.query.get_or_404(part_id) new part
    if request.method == 'POST':
    # Check permissionsuser.has_permission(Permissions.PARTS_CREATE) and not current_user.is_admin:
    if not current_user.has_permission(Permissions.PARTS_EDIT) and not current_user.is_admin:
        flash("You don't have permission to edit parts", "error")
        return redirect(url_for('manage_parts'))
        name = request.form.get('name')
    if request.method == 'POST':rm.get('description')
        part.name = request.form.get('name')ne_id')
        part.description = request.form.get('description')nce_frequency')
        part.machine_id = request.form.get('machine_id')_unit')
        
        # Update maintenance frequency if changed
        new_frequency = request.form.get('maintenance_frequency')
        new_unit = request.form.get('maintenance_unit')
        if new_frequency and new_unit:
            days = Part.convert_to_days(new_frequency, new_unit)
            part.maintenance_frequency = days
            part.update_next_maintenance()
                machine_id=machine_id,
        db.session.commit()_frequency=maintenance_frequency,
        flash(f"Part '{part.name}' has been updated", "success")
        return redirect(url_for('manage_parts', machine_id=part.machine_id))
            )
    machines = Machine.query.all()t)
    return render_template('edit_part.html', part=part, machines=machines, is_admin=current_user.is_admin)
            
@app.route('/parts/<int:part_id>/delete', methods=['POST'])ly", "success")
@login_requiredurn redirect(url_for('manage_parts', machine_id=machine_id))
def delete_part(part_id):
    """Delete a part"""for dropdown menus
    if not current_user.has_permission(Permissions.PARTS_DELETE) and not current_user.is_admin:
        flash("You don't have permission to delete parts", "error")
        return redirect(url_for('manage_parts'))
                          parts=parts,
    part = Part.query.get_or_404(part_id)es,
    machine_id = part.machine_idtitle,
    part_name = part.name now=datetime.utcnow(),
                          machine_id=machine_id if machine_id else None,
    db.session.delete(part)s_admin=current_user.is_admin,
    db.session.commit()   can_create=current_user.has_permission(Permissions.PARTS_CREATE) or current_user.is_admin,
                          can_edit=current_user.has_permission(Permissions.PARTS_EDIT) or current_user.is_admin,
    flash(f"Part '{part_name}' has been deleted", "success")sion(Permissions.PARTS_DELETE) or current_user.is_admin)
    return redirect(url_for('manage_parts', machine_id=machine_id))
@app.route('/parts/<int:part_id>/edit', methods=['GET', 'POST'])
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password()::
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        # Find user by emailpermission(Permissions.PARTS_EDIT) and not current_user.is_admin:
        user = User.query.filter_by(email=email).first() "error")
        if user:edirect(url_for('manage_parts'))
            # Generate reset token
            token = user.generate_reset_token()
            # Build reset URLorm.get('name')
            reset_url = url_for('reset_password', user_id=user.id, token=token, _external=True)
            # Create emailrequest.form.get('machine_id')
            subject = "Password Reset Request"
            html_body = f""" frequency if changed
            <h1>Password Reset Request</h1>aintenance_frequency')
            <p>Hello {user.full_name or user.username},</p>
            <p>You requested to reset your password. Please click the link below to reset your password:</p>
            <p><a href="{reset_url}">{reset_url}</a></p>ew_unit)
            <p>This link is only valid for 1 hour.</p>
            <p>If you did not request a password reset, please ignore this email.</p>
            """
            try:on.commit()
                # Send emailname}' has been updated", "success")
                msg = Message(r('manage_parts', machine_id=part.machine_id))
                    subject=subject,
                    recipients=[email],
                    html=html_bodyart.html', part=part, machines=machines, is_admin=current_user.is_admin)
                )
                mail.send(msg)d>/delete', methods=['POST'])
                flash("Password reset link has been sent to your email", "success")
            except Exception as e:
                app.logger.error(f"Failed to send password reset email: {str(e)}")
                flash("Failed to send password reset email. Please try again later.", "error"):
        else:("You don't have permission to delete parts", "error")
            # Still show success message even if email not found
            # This prevents user enumeration attacks
            flash("If that email is in our system, a password reset link has been sent", "success")
        return redirect(url_for('login'))
    return render_template('forgot_password.html')
    
@app.route('/reset-password/<int:user_id>/<token>', methods=['GET', 'POST'])
def reset_password(user_id, token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))ed", "success")
    # Find userrect(url_for('manage_parts', machine_id=machine_id))
    user = User.query.get(user_id)
    # Verify user and tokend', methods=['GET', 'POST'])
    if not user or not user.verify_reset_token(token):
        flash("The password reset link is invalid or has expired.", "error")
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
    if request.method == 'POST':('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        # Validate password
        if not password or len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return render_template('reset_password.html', user_id=user_id, token=token)
            reset_url = url_for('reset_password', user_id=user.id, token=token, _external=True)
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template('reset_password.html', user_id=user_id, token=token)
            <h1>Password Reset Request</h1>
        # Update passwordr.full_name or user.username},</p>
        user.set_password(password)et your password. Please click the link below to reset your password:</p>
        # Clear reset tokenset_url}">{reset_url}</a></p>
        user.clear_reset_token() valid for 1 hour.</p>
            <p>If you did not request a password reset, please ignore this email.</p>
        flash("Your password has been successfully reset. You can now log in with your new password.", "success")
        return redirect(url_for('login'))
                # Send email
    return render_template('reset_password.html', user_id=user_id, token=token)
                    subject=subject,
@app.route('/profile')cipients=[email],
@login_required     html=html_body
def user_profile():
    """User profile page"""sg)
    return render_template('profile.html', has been sent to your email", "success")
                          user=current_user)
                app.logger.error(f"Failed to send password reset email: {str(e)}")
@app.route('/admin')h("Failed to send password reset email. Please try again later.", "error")
@login_required
@admin_requiredtill show success message even if email not found
def admin():# This prevents user enumeration attacks
    """Admin dashboard page"""il is in our system, a password reset link has been sent", "success")
    # Get counts for admin dashboardin'))
    user_count = User.query.count()password.html')
    site_count = Site.query.count()
    machine_count = Machine.query.count()/<token>', methods=['GET', 'POST'])
    part_count = Part.query.count()
    users = User.query.all() if current_user.is_admin else []
    return render_template('admin.html', d'))
                          user_count=user_count,
                          site_count=site_count,
                          machine_count=machine_count,
                          part_count=part_count)oken):
        flash("The password reset link is invalid or has expired.", "error")
@app.route('/admin/users')l_for('forgot_password'))
@login_required
@admin_requiredmethod == 'POST':
def manage_users():request.form.get('password')
    """User management page for admins"""et('confirm_password')
    users = User.query.all()
    roles = Role.query.all()en(password) < 8:
    sites = Site.query.all()must be at least 8 characters long.", "error")
    return render_template('admin_users.html', users=users, roles=roles, sites=sites)n)
        
@app.route('/admin/users/add', methods=['POST'])
@login_requiredsh("Passwords do not match.", "error")
@admin_requiredurn render_template('reset_password.html', user_id=user_id, token=token)
def add_user():
    """Add a new user"""d
    username = request.form.get('username')
    email = request.form.get('email')
    full_name = request.form.get('full_name')
    role_id = request.form.get('role_id')
    is_admin = 'is_admin' in request.formcessfully reset. You can now log in with your new password.", "success")
    password = secrets.token_urlsafe(8)  # Generate random initial password
    # Validate input
    if User.query.filter_by(username=username).first():id=user_id, token=token)
        flash(f"Username '{username}' already exists", "error")
        return redirect(url_for('manage_users'))
    if not username or not email:
        flash("Username and email are required", "error")
        return redirect(url_for('manage_users'))
    # Create new userplate('profile.html', 
    user = User(          user=current_user)
        username=username,
        email=email,
        full_name=full_name,
        role_id=role_id,
        is_admin=is_admin,
    )""Admin dashboard page"""
    user.set_password(password)board
    # Add user to selected sitest()
    site_ids = request.form.getlist('site_ids')
    for site_id in site_ids:query.count()
        site = Site.query.get(site_id)
        if site:.query.all() if current_user.is_admin else []
            user.sites.append(site)tml', 
    db.session.add(user)  user_count=user_count,
    db.session.commit()   site_count=site_count,
    flash(f"User '{username}' has been created with temporary password: {password}", "success")
    return redirect(url_for('manage_users'))unt)

@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit a user"""t page for admins"""
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email') users=users, roles=roles, sites=sites)
        user.full_name = request.form.get('full_name')
        user.role_id = request.form.get('role_id')
        user.is_admin = 'is_admin' in request.form
        equired
        # Reset password if requested
        if 'reset_password' in request.form:
            new_password = secrets.token_urlsafe(8)
            user.set_password(new_password)
            flash(f"Password has been reset to: {new_password}", "success")
        _id = request.form.get('role_id')
        # Update site assignmentsest.form
        user.sites = []  # Clear existing associationsndom initial password
        site_ids = request.form.getlist('site_ids')
        for site_id in site_ids:name=username).first():
            site = Site.query.get(site_id)ady exists", "error")
            if site:ect(url_for('manage_users'))
                user.sites.append(site)
        db.session.commit() email are required", "error")
        flash(f"User '{user.username}' has been updated", "success")
        return redirect(url_for('manage_users'))
    roles = Role.query.all()
    sites = Site.query.all()
    return render_template('edit_user.html', user=user, roles=roles, sites=sites)
        full_name=full_name,
@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_requiredn=is_admin,
@admin_required
def delete_user(user_id):sword)
    """Delete a user"""ted sites
    user = User.query.get_or_404(user_id)_ids')
    for site_id in site_ids:
    # Prevent deleting selfet(site_id)
    if user.id == current_user.id:
        flash("You cannot delete your own account", "error")
        return redirect(url_for('manage_users'))
    db.session.commit()
    username = user.username' has been created with temporary password: {password}", "success")
    db.session.delete(user)('manage_users'))
    db.session.commit()
    .route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
    flash(f"User '{username}' has been deleted", "success")
    return redirect(url_for('manage_users'))
def edit_user(user_id):
@app.route('/admin/roles')
@login_required.query.get_or_404(user_id)
@admin_requiredmethod == 'POST':
def manage_roles():me = request.form.get('username')
    """Role management page for admins"""ail')
    roles = Role.query.all()uest.form.get('full_name')
    all_permissions = Permissions.get_all_permissions()
    return render_template('admin_roles.html', roles=roles, all_permissions=all_permissions)
        
@app.route('/admin/roles/add', methods=['POST'])
@login_requiredet_password' in request.form:
@admin_required_password = secrets.token_urlsafe(8)
def add_role():r.set_password(new_password)
    """Add a new role"""word has been reset to: {new_password}", "success")
    name = request.form.get('name')
    description = request.form.get('description')
    permissions = ','.join(request.form.getlist('permissions'))
        site_ids = request.form.getlist('site_ids')
    # Validate inputin site_ids:
    if Role.query.filter_by(name=name).first():
        flash(f"Role '{name}' already exists", "error")
        return redirect(url_for('manage_roles'))
        db.session.commit()
    if not name:User '{user.username}' has been updated", "success")
        flash("Role name is required", "error"))
        return redirect(url_for('manage_roles'))
    sites = Site.query.all()
    # Create new roleplate('edit_user.html', user=user, roles=roles, sites=sites)
    role = Role(
        name=name,/users/<int:user_id>/delete', methods=['POST'])
        description=description,
        permissions=permissions
    )elete_user(user_id):
    """Delete a user"""
    db.session.add(role)t_or_404(user_id)
    db.session.commit()
    flash(f"Role '{name}' has been created", "success")
    return redirect(url_for('manage_roles'))
        flash("You cannot delete your own account", "error")
@app.route('/admin/roles/<int:role_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_requireduser.username
def edit_role(role_id):ser)
    """Edit a role"""()
    role = Role.query.get_or_404(role_id)
    flash(f"User '{username}' has been deleted", "success")
    if request.method == 'POST':age_users'))
        role.name = request.form.get('name')
        role.description = request.form.get('description')
        role.permissions = ','.join(request.form.getlist('permissions'))
        equired
        db.session.commit()
        flash(f"Role '{role.name}' has been updated", "success")
        return redirect(url_for('manage_roles'))
    all_permissions = Permissions.get_all_permissions()
    all_permissions = Permissions.get_all_permissions()les, all_permissions=all_permissions)
    role_permissions = role.get_permissions_list()
    return render_template('edit_role.html', role=role, all_permissions=all_permissions, role_permissions=role_permissions)
@login_required
@app.route('/admin/roles/<int:role_id>/delete', methods=['POST'])
@login_required
@admin_requiredw role"""
def delete_role(role_id):et('name')
    """Delete a role"""st.form.get('description')
    role = Role.query.get_or_404(role_id)etlist('permissions'))
    
    # Check if role is in use
    if User.query.filter_by(role_id=role.id).first():
        flash(f"Cannot delete role '{role.name}' because it is assigned to users", "error")
        return redirect(url_for('manage_roles'))
    
    role_name = role.name
    db.session.delete(role) required", "error")
    db.session.commit()(url_for('manage_roles'))
    
    flash(f"Role '{role_name}' has been deleted", "success")
    return redirect(url_for('manage_roles'))
        name=name,
@app.route('/admin/backup')tion,
@login_requiredions=permissions
@admin_required
def manage_backups():
    # Import backup utilities
    from backup_utils import list_backupsn.commit()
    n created", "success")
    # Get list of available backupsreturn redirect(url_for('manage_roles'))
    backups = list_backups()
    ods=['GET', 'POST'])
    return render_template('admin_backups.html', backups=backups)in_required

@app.route('/admin/backup/create', methods=['POST'])
@login_required
@admin_requiredrole = Role.query.get_or_404(role_id)
def create_backup():
    from backup_utils import create_backup as create_db_backupethod == 'POST':
    et('name')
    success, message = create_db_backup()scription')
    '))
    if success:
        flash(f'Backup created successfully: {message}', 'success')
    else:
        flash(f'Backup creation failed: {message}', 'error')'manage_roles'))
    
    return redirect(url_for('manage_backups'))missions()
list()
@app.route('/admin/backup/<filename>/restore', methods=['POST'])template('edit_role.html', role=role, all_permissions=all_permissions, role_permissions=role_permissions)
@login_required
@admin_requiredethods=['POST'])
def restore_backup(filename):
    from backup_utils import restore_backup as restore_db_backupin_required
    
    success, message = restore_db_backup(filename)    """Delete a role"""
    
    if success:
        flash('Database restored successfully. You may need to log in again.', 'success')role is in use
    else:lter_by(role_id=role.id).first():
        flash(f'Restore failed: {message}', 'error') '{role.name}' because it is assigned to users", "error")
    n redirect(url_for('manage_roles'))
    return redirect(url_for('manage_backups'))

@app.route('/admin/backup/<filename>/delete', methods=['POST'])db.session.delete(role)
@login_required)
@admin_required
def delete_backup(filename):n deleted", "success")
    try:
        from backup_utils import get_backup_dir
        import osup')
        
        backup_path = os.path.join(get_backup_dir(), filename)
        info_path = f"{backup_path}.info"
        dmins"""
        # Delete backup file and info file if they exist
        if os.path.exists(backup_path):
            os.remove(backup_path)
        ps are stored
        if os.path.exists(info_path):
            os.remove(info_path)
        
        flash('Backup deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting backup: {str(e)}', 'error')
    st existing backups
    return redirect(url_for('manage_backups'))        # Extract database path from URI
        db_path = app.config['SQLALCHEMY_DATABASE_URI'][10:]
        if db_path.startswith('/'):
            database_path = db_path
        else:
            database_path = os.path.join(BASE_DIR, db_path)
        
        try:
            # Close database connection
            db.session.close()
            # Backup current database before restoring
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            current_backup = os.path.join(backup_dir, f"pre_restore_{timestamp}.db")
            shutil.copy2(database_path, current_backup)
            # Restore from backup
            shutil.copy2(backup_path, database_path)
            flash(f"Database restored successfully from: {filename}", "success")
        except Exception as e:
            flash(f"Restore failed: {str(e)}", "error")
    else:
        flash("Restores are only supported for SQLite databases", "error")
    
    return redirect(url_for('manage_backups'))

@app.route('/admin/backup/<filename>/delete', methods=['POST'])
@login_required
@admin_required
def delete_backup(filename):
    """Delete a backup file"""
    import os
    
    # Validate filename to prevent path traversal
    if '../' in filename or '/' in filename:
        flash("Invalid backup filename", "error")
        return redirect(url_for('manage_backups'))
    
    backup_path = os.path.join(BASE_DIR, 'backups', filename)
    
    if os.path.exists(backup_path):
        try:
            os.remove(backup_path)
            flash(f"Backup deleted: {filename}", "success")
        except Exception as e:
            flash(f"Failed to delete backup: {str(e)}", "error")
    else:
        flash(f"Backup file not found: {filename}", "error")
    
    return redirect(url_for('manage_backups'))