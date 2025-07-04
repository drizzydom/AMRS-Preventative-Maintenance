from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import JSON as PG_JSON
from sqlalchemy.types import JSON as SA_JSON
from sqlalchemy import Table, Column, Integer, ForeignKey, Date, Boolean
from cryptography.fernet import Fernet, InvalidToken
import base64
import os
import hashlib

# --- Application-level encryption utilities ---
# The encryption key MUST be set as an environment variable in production
FERNET_KEY = os.environ.get('USER_FIELD_ENCRYPTION_KEY')
if not FERNET_KEY:
    # Instead of generating a key, show an error message recommending proper setup
    print("[SECURITY ERROR] USER_FIELD_ENCRYPTION_KEY environment variable not set.")
    print("[SECURITY ERROR] Please set this variable to a valid Fernet key before starting the application.")
    print("[SECURITY ERROR] This key should be a URL-safe base64-encoded 32-byte key.")
    print("[SECURITY ERROR] Example command to generate: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'")
    # If application is starting up, we'll use a temporary key for testing only
    # This is not secure and should not be used in production!
    if os.environ.get('FLASK_ENV') == 'development' or os.environ.get('FLASK_DEBUG') == '1':
        print("[SECURITY WARNING] Development mode detected. Using a temporary key for encryption.")
        FERNET_KEY = base64.urlsafe_b64encode(os.urandom(32)).decode()
    else:
        # For production, we don't want to silently continue with an insecure setup
        raise ValueError("USER_FIELD_ENCRYPTION_KEY environment variable must be set in production.")

# Initialize Fernet cipher with the key
fernet = Fernet(FERNET_KEY)

def encrypt_value(value):
    if value is None:
        return None
    encrypted = fernet.encrypt(value.encode()).decode()
    print(f"[ENCRYPTION] encrypt_value('{value}') = {encrypted}")
    return encrypted

def decrypt_value(value):
    if value is None:
        return None
    try:
        return fernet.decrypt(value.encode()).decode()
    except (InvalidToken, AttributeError):
        return None

def hash_value(value):
    if value is None:
        return None
    return hashlib.sha256(value.lower().encode()).hexdigest()

db = SQLAlchemy()

# Define the association table for many-to-many relationship between User and Site
user_site = db.Table(
    'user_site',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('site_id', db.Integer, db.ForeignKey('sites.id'), primary_key=True)
)

# Association table for AuditTask <-> Machine
machine_audit_task = Table(
    'machine_audit_task', db.Model.metadata,
    Column('audit_task_id', Integer, ForeignKey('audit_tasks.id'), primary_key=True),
    Column('machine_id', Integer, ForeignKey('machines.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'  # Explicit table name for PostgreSQL conventions
    id = db.Column(db.Integer, primary_key=True)
    _username = db.Column('username', db.Text, unique=True, nullable=False, index=True)
    username_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    _email = db.Column('email', db.Text, unique=True, nullable=False)
    email_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(100))
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reset_token = db.Column(db.String(100), default=None)
    reset_token_expiration = db.Column(db.DateTime, default=None)
    notification_preferences = db.Column(
        PG_JSON().with_variant(SA_JSON(), 'sqlite'),
        nullable=True,
        default=None
    )
    
    # Define the relationship with Role
    role = db.relationship('Role', backref='users', lazy='joined')
    
    # Define the many-to-many relationship with Site
    sites = db.relationship('Site', secondary=user_site, lazy='subquery',
                          backref=db.backref('users', lazy=True))
    
    # Define the one-to-many relationship with MaintenanceRecord
    maintenance_records = db.relationship('MaintenanceRecord', backref='user', lazy=True)

    @property
    def username(self):
        return decrypt_value(self._username)

    @username.setter
    def username(self, value):
        self._username = encrypt_value(value)
        self.username_hash = hash_value(value)

    @property
    def email(self):
        return decrypt_value(self._email)

    @email.setter
    def email(self, value):
        self._email = encrypt_value(value)
        self.email_hash = hash_value(value)

    def set_password(self, password):
        """Set the password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check the password against the stored hash"""
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission):
        """Check if user has a specific permission"""
        # Admin users have all permissions
        if self.is_admin:
            return True
        
        # Users with no role have no permissions
        if not self.role:
            return False
        
        # Check if the user's role has the permission
        return self.role.has_permission(permission)
    
    def get_notification_preferences(self):
        default = {
            'enable_email': True,
            'notification_frequency': 'weekly',
            'email_format': 'html',
            'notification_types': ['overdue', 'due_soon']
        }
        if not self.notification_preferences:
            return default
        prefs = self.notification_preferences.copy()
        for k, v in default.items():
            if k not in prefs:
                prefs[k] = v
        return prefs

    def set_notification_preferences(self, prefs):
        self.notification_preferences = prefs
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.username}>'

class Role(db.Model):
    """Role model for user permissions"""
    __tablename__ = 'roles'  # Explicit table name for PostgreSQL conventions
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255))
    permissions = db.Column(db.Text)  # Comma-separated list of permissions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def has_permission(self, permission):
        """Check if this role has a specific permission"""
        if not self.permissions:
            return False
            
        # Special case for admin.full permission
        if 'admin.full' in self.permissions:
            return True
            
        permissions_list = self.permissions.split(',')
        return permission in permissions_list
    
    def get_permissions_list(self):
        """Get the list of permissions for this role"""
        if not self.permissions:
            return []
            
        return self.permissions.split(',')
    
    def __repr__(self):
        return f'<Role {self.name}>'

class Site(db.Model):
    """Site model representing physical locations"""
    __tablename__ = 'sites'  # Explicit table name for PostgreSQL conventions
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(255))
    contact_email = db.Column(db.String(120))
    enable_notifications = db.Column(db.Boolean, default=True)
    notification_threshold = db.Column(db.Integer, default=30)  # Days before maintenance to notify
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define the one-to-many relationship with Machine
    machines = db.relationship('Machine', backref='site', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Site {self.name}>'

class Machine(db.Model):
    """Machine model representing equipment at a site"""
    __tablename__ = 'machines'  # Explicit table name for PostgreSQL conventions
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100))
    machine_number = db.Column(db.String(50))
    serial_number = db.Column(db.String(50))
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'), nullable=False)
    decommissioned = db.Column(db.Boolean, default=False, nullable=False)  # Track if machine is decommissioned
    decommissioned_date = db.Column(db.DateTime, nullable=True)  # When it was decommissioned
    decommissioned_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Who decommissioned it
    decommissioned_reason = db.Column(db.Text, nullable=True)  # Why it was decommissioned
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define the one-to-many relationship with Part
    parts = db.relationship('Part', backref='machine', lazy=True, cascade="all, delete-orphan")
    
    # Relationship for decommissioned_by user
    decommissioned_by_user = db.relationship('User', foreign_keys=[decommissioned_by], backref='decommissioned_machines')
    
    @property
    def is_active(self):
        """Return True if machine is not decommissioned"""
        return not self.decommissioned
    
    def decommission(self, user, reason=None):
        """Mark machine as decommissioned"""
        from datetime import datetime
        self.decommissioned = True
        self.decommissioned_date = datetime.utcnow()
        self.decommissioned_by = user.id if user else None
        self.decommissioned_reason = reason
        self.updated_at = datetime.utcnow()
    
    def recommission(self):
        """Mark machine as active again"""
        from datetime import datetime
        self.decommissioned = False
        self.decommissioned_date = None
        self.decommissioned_by = None
        self.decommissioned_reason = None
        self.updated_at = datetime.utcnow()
    
    def __repr__(self):
        status = "Decommissioned" if self.decommissioned else "Active"
        return f'<Machine {self.name} ({status})>'
    
    @classmethod
    def safe_filter_active(cls, query):
        """
        Safely filter for active (non-decommissioned) machines.
        Falls back to all machines if decommissioned column doesn't exist yet.
        """
        try:
            # Try to filter by decommissioned field
            return query.filter(cls.decommissioned == False)
        except Exception as e:
            # If the column doesn't exist yet, return all machines
            # This handles the case during migration where columns don't exist
            import logging
            logging.getLogger(__name__).warning(f"decommissioned column not available yet: {e}")
            return query

class Part(db.Model):
    """Part model representing components of a machine that need maintenance"""
    __tablename__ = 'parts'  # Explicit table name for PostgreSQL conventions
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    machine_id = db.Column(db.Integer, db.ForeignKey('machines.id'), nullable=False)
    maintenance_frequency = db.Column(db.Integer, default=30)  # Numeric value for frequency
    maintenance_unit = db.Column(db.String(10), default='day')  # Units: day, week, month, year
    maintenance_days = db.Column(db.Integer, default=30)  # Calculated days for maintenance period
    last_maintenance = db.Column(db.DateTime, default=datetime.utcnow)
    next_maintenance = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define the one-to-many relationship with MaintenanceRecord
    maintenance_records = db.relationship('MaintenanceRecord', backref='part', lazy=True, cascade="all, delete-orphan")
    
    def get_frequency_display(self):
        unit = self.maintenance_unit or 'day'
        freq = self.maintenance_frequency or 1
        if unit == 'day':
            return f"Every {freq} day{'s' if freq != 1 else ''}"
        elif unit == 'week':
            return f"Every {freq} week{'s' if freq != 1 else ''}"
        elif unit == 'month':
            return f"Every {freq} month{'s' if freq != 1 else ''}"
        elif unit == 'year':
            return f"Every {freq} year{'s' if freq != 1 else ''}"
        return f"Every {freq} {unit}(s)"
    
    def __repr__(self):
        return f'<Part {self.name}>'

class MaintenanceRecord(db.Model):
    """Maintenance record model for tracking maintenance activities"""
    __tablename__ = 'maintenance_records'  # Explicit table name for PostgreSQL conventions
    
    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('parts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    machine_id = db.Column(db.Integer, db.ForeignKey('machines.id'), nullable=True)  # Add machine_id field
    date = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.Column(db.Text)
    maintenance_type = db.Column(db.String(50), nullable=True)  # Added for clarity and migration safety
    description = db.Column(db.Text, nullable=True)  # Add this field for maintenance description
    performed_by = db.Column(db.String(100), nullable=True)  # Add this field for the user who performed the maintenance
    status = db.Column(db.String(50), nullable=True)  # Add this field for maintenance status
    notes = db.Column(db.Text, nullable=True)  # Add this field for maintenance notes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Add client identifier for synchronization
    client_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()))
    
    # Add relationship to Machine
    machine = db.relationship('Machine', backref=db.backref('maintenance_records', lazy=True))
    
    def __repr__(self):
        return f'<MaintenanceRecord {self.id} for Part {self.part_id}>'

class AuditTask(db.Model):
    __tablename__ = 'audit_tasks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    interval = db.Column(db.String(20), default='daily')  # Options: daily, weekly, monthly, custom
    custom_interval_days = db.Column(db.Integer, nullable=True)  # Only used if interval == 'custom'
    color = db.Column(db.String(32), nullable=True)  # HSL or HEX color for per-site color wheel
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    machines = db.relationship('Machine', secondary=machine_audit_task, backref='audit_tasks')
    completions = db.relationship('AuditTaskCompletion', backref='audit_task', lazy=True, cascade="all, delete-orphan")

class AuditTaskCompletion(db.Model):
    __tablename__ = 'audit_task_completions'
    id = db.Column(db.Integer, primary_key=True)
    audit_task_id = db.Column(db.Integer, db.ForeignKey('audit_tasks.id'), nullable=False)
    machine_id = db.Column(db.Integer, db.ForeignKey('machines.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
