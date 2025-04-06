from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

db = SQLAlchemy()

user_site = db.Table('user_site',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('site_id', db.Integer, db.ForeignKey('sites.id'), primary_key=True)
)

class Role(db.Model):
    """Role model for user permissions"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))
    permissions = db.Column(db.Text)  # Store comma-separated permissions
    
    # Define the relationship to User
    users = db.relationship('User', back_populates='role')
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    def get_permissions_list(self):
        """Returns permissions as a list"""
        if not self.permissions:
            return []
        return self.permissions.split(',')

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))  # Reference 'roles' not 'role'
    reset_token = db.Column(db.String(100))
    reset_token_expiry = db.Column(db.DateTime)
    notification_preferences = db.Column(db.JSON)

    # Define the many-to-many relationship with sites
    sites = db.relationship('Site', secondary=user_site, back_populates='users')
    
    # Define the relationship to Role
    role = db.relationship('Role', back_populates='users')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def __repr__(self):
        return f'<User {self.username}>'

class Site(db.Model):
    __tablename__ = 'sites'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    contact_email = db.Column(db.String(100))
    notification_threshold = db.Column(db.Integer, default=30)
    enable_notifications = db.Column(db.Boolean, default=True)
    
    # Relationships
    machines = db.relationship('Machine', backref='site', lazy=True)
    users = db.relationship('User', secondary=user_site, back_populates='sites')
    
    def __repr__(self):
        return f'<Site {self.name}>'
    
    def get_parts_status(self, current_date=None):
        """
        Get maintenance status of all parts at this site
        Returns dictionary with 'overdue' and 'due_soon' lists
        """
        if current_date is None:
            current_date = datetime.now()
        
        overdue = []
        due_soon = []
        threshold = self.notification_threshold or 30  # Default to 30 days if not set
        
        # Loop through all machines at this site
        for machine in self.machines:
            for part in machine.parts:
                days_until = (part.next_maintenance - current_date).days
                
                # Overdue parts
                if days_until < 0:
                    overdue.append(part)
                # Due soon parts within threshold
                elif days_until <= threshold:
                    due_soon.append(part)
        
        return {
            'overdue': overdue,
            'due_soon': due_soon
        }

class Machine(db.Model):
    __tablename__ = 'machines'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100))
    machine_number = db.Column(db.String(100))
    serial_number = db.Column(db.String(100))
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'), nullable=False)
    
    # Relationships
    parts = db.relationship('Part', backref='machine', lazy=True)
    
    def __repr__(self):
        return f'<Machine {self.name}>'

class Part(db.Model):
    __tablename__ = 'parts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    machine_id = db.Column(db.Integer, db.ForeignKey('machines.id'), nullable=False)
    maintenance_frequency = db.Column(db.Integer, default=30)
    maintenance_unit = db.Column(db.String(10), default='day')  # day, week, month, year
    maintenance_days = db.Column(db.Integer, default=30)
    last_maintenance = db.Column(db.DateTime, default=datetime.now)
    next_maintenance = db.Column(db.DateTime, 
                                default=lambda: datetime.now() + timedelta(days=30))
    
    def __repr__(self):
        return f'<Part {self.name}>'
        
    def get_frequency_display(self):
        """Returns a human-readable maintenance frequency"""
        suffix = 's' if self.maintenance_frequency != 1 else ''
        return f"{self.maintenance_frequency} {self.maintenance_unit}{suffix}"
