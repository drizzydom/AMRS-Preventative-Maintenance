from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import JSON as PG_JSON
from sqlalchemy.types import JSON as SA_JSON
from sqlalchemy import Table, Column, Integer, ForeignKey, Date, Boolean

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
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define the one-to-many relationship with Part
    parts = db.relationship('Part', backref='machine', lazy=True, cascade="all, delete-orphan")
    
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
    
    # Define the one-to-many relationship with MaintenanceRecord
    maintenance_records = db.relationship('MaintenanceRecord', backref='part', lazy=True, cascade="all, delete-orphan")
    
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
