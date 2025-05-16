from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
import uuid
import base64
import os
import hashlib

# Fix SQLAlchemy imports to avoid the '__all__' attribute error
import sqlalchemy
import sqlalchemy.orm
from sqlalchemy import Table, Column, Integer, ForeignKey, Date, Boolean, Text, String, DateTime
from sqlalchemy.orm import relationship, backref

# Add necessary __all__ attributes to SQLAlchemy modules if missing
if not hasattr(sqlalchemy, '__all__'):
    sqlalchemy.__all__ = ['Column', 'Table', 'Integer', 'String', 'Text', 'ForeignKey']

if not hasattr(sqlalchemy.orm, '__all__'):
    sqlalchemy.orm.__all__ = ['relationship', 'backref', 'sessionmaker', 'session']

try:
    from sqlalchemy.dialects.postgresql import JSON as PG_JSON
    from sqlalchemy.types import JSON as SA_JSON
except ImportError:
    # Fallback if PostgreSQL dialect isn't available
    from sqlalchemy.types import JSON as SA_JSON
    PG_JSON = SA_JSON

# For encryption in Electron environment
try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:
    # Provide mock encryption if cryptography isn't available
    print("[WARNING] Cryptography module not available, using mock encryption")
    class MockFernet:
        def __init__(self, key): 
            self.key = key
        def encrypt(self, data):
            return f"MOCK_ENCRYPTED:{data}".encode()
        def decrypt(self, token):
            if token.startswith(b"MOCK_ENCRYPTED:"):
                return token[15:]
            return token
    
    class MockInvalidToken(Exception):
        pass
    
    Fernet = MockFernet
    InvalidToken = MockInvalidToken

# --- Application-level encryption utilities ---
# In Electron, we'll set this from the app's environment
FERNET_KEY = os.environ.get('USER_FIELD_ENCRYPTION_KEY')
if not FERNET_KEY:
    # For Electron app, generate a consistent key based on machine ID
    # This isn't secure for production but works for local app usage
    try:
        if os.environ.get('ELECTRON_MODE') == 'true':
            print("[INFO] Running in Electron mode, generating deterministic encryption key")
            # Generate a consistent key based on machine info
            import platform
            machine_id = platform.node()  # Get computer name
            key_seed = f"AMRS_APP_{machine_id}".encode()
            FERNET_KEY = base64.urlsafe_b64encode(hashlib.sha256(key_seed).digest())
        elif os.environ.get('FLASK_ENV') == 'development' or os.environ.get('FLASK_DEBUG') == '1':
            print("[SECURITY WARNING] Development mode detected. Using a temporary key for encryption.")
            FERNET_KEY = base64.urlsafe_b64encode(os.urandom(32))
        else:
            print("[SECURITY ERROR] USER_FIELD_ENCRYPTION_KEY environment variable not set.")
            print("[SECURITY ERROR] Please set this variable to a valid Fernet key before starting the application.")
            print("[SECURITY ERROR] This key should be a URL-safe base64-encoded 32-byte key.")
            print("[SECURITY ERROR] Example command to generate: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'")
            # For production, we need a proper key
            raise ValueError("USER_FIELD_ENCRYPTION_KEY environment variable must be set in production.")
    except Exception as e:
        # Last resort fallback
        print(f"[ERROR] Failed to generate encryption key: {str(e)}")
        print("[WARNING] Using temporary insecure key")
        FERNET_KEY = base64.urlsafe_b64encode(b"TEMPORARY_UNSECURE_KEY_DO_NOT_USE_IN_PRODUCTION!!")

# Initialize Fernet cipher with the key
try:
    fernet = Fernet(FERNET_KEY)
except Exception as e:
    print(f"[ERROR] Failed to initialize Fernet: {str(e)}")
    # Create a mock fernet that just passes through
    class PassthroughFernet:
        def encrypt(self, data):
            if isinstance(data, str):
                return data.encode()
            return data
        def decrypt(self, data):
            if isinstance(data, bytes):
                return data.decode()
            return data
    fernet = PassthroughFernet()

def encrypt_value(value):
    if value is None:
        return None
    try:
        encrypted = fernet.encrypt(value.encode()).decode()
        return encrypted
    except Exception as e:
        print(f"[ERROR] Encryption failed: {str(e)}")
        return value

def decrypt_value(value):
    if value is None:
        return None
    try:
        return fernet.decrypt(value.encode()).decode()
    except (InvalidToken, AttributeError, Exception) as e:
        print(f"[ERROR] Decryption failed: {str(e)}")
        return value

def hash_value(value):
    if value is None:
        return None
    return hashlib.sha256(value.lower().encode()).hexdigest()

# Initialize SQLAlchemy
db = SQLAlchemy()

# Create a direct reference to the SQLAlchemy classes
# This avoids using db.xxx which causes the __all__ attribute error
sa_Column = sqlalchemy.Column
sa_ForeignKey = sqlalchemy.ForeignKey
sa_Integer = sqlalchemy.Integer
sa_Table = sqlalchemy.Table
sa_relationship = sqlalchemy.orm.relationship
sa_backref = sqlalchemy.orm.backref

# Define the association table for many-to-many relationship between User and Site
user_site = sa_Table(
    'user_site',
    db.metadata,
    sa_Column('user_id', sa_Integer, sa_ForeignKey('users.id'), primary_key=True),
    sa_Column('site_id', sa_Integer, sa_ForeignKey('sites.id'), primary_key=True)
)

# Association table for AuditTask <-> Machine
machine_audit_task = sa_Table(
    'machine_audit_task', 
    db.metadata,
    sa_Column('audit_task_id', sa_Integer, sa_ForeignKey('audit_tasks.id'), primary_key=True),
    sa_Column('machine_id', sa_Integer, sa_ForeignKey('machines.id'), primary_key=True)
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
    
    # Use direct SQLAlchemy imports for relationships
    role = sa_relationship('Role', backref='users', lazy='joined')
    sites = sa_relationship('Site', secondary=user_site, lazy='subquery',
                         backref=sa_backref('users', lazy=True))
    maintenance_records = sa_relationship('MaintenanceRecord', backref='user', lazy=True)

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
    
    # Use direct SQLAlchemy imports for relationship
    machines = sa_relationship('Machine', backref='site', lazy=True, cascade="all, delete-orphan")
    
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Use direct SQLAlchemy imports for relationship
    parts = sa_relationship('Part', backref='machine', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Machine {self.name}>'

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
    
    # Use direct SQLAlchemy imports for relationship
    maintenance_records = sa_relationship('MaintenanceRecord', backref='part', lazy=True, cascade="all, delete-orphan")
    
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
    
    # Use direct SQLAlchemy imports for relationship
    machine = sa_relationship('Machine', backref=sa_backref('maintenance_records', lazy=True))
    
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
    machines = sa_relationship('Machine', secondary=machine_audit_task, backref='audit_tasks')
    completions = sa_relationship('AuditTaskCompletion', backref='audit_task', lazy=True, cascade="all, delete-orphan")

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
