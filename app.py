from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
import logging
from functools import wraps

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maintenance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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
    db.Column('site_id', db.Integer, db.ForeignKey('site.id'), primary_key=True)
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

class Site(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    machines = db.relationship('Machine', backref='site', lazy=True, cascade="all, delete-orphan")

class Machine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100))
    site_id = db.Column(db.Integer, db.ForeignKey('site.id'), nullable=False)
    parts = db.relationship('Part', backref='machine', lazy=True, cascade="all, delete-orphan")

class Part(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)
    maintenance_frequency = db.Column(db.Integer, default=7)  # in days
    last_maintenance = db.Column(db.DateTime, default=datetime.utcnow)
    next_maintenance = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(Part, self).__init__(**kwargs)
        if 'maintenance_frequency' in kwargs and 'last_maintenance' in kwargs:
            self.update_next_maintenance()
            
    def update_next_maintenance(self):
        self.next_maintenance = self.last_maintenance + timedelta(days=self.maintenance_frequency)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
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
            return redirect(url_for('dashboard'))
        else:
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
        # Users with sites.view permission see all sites
        sites = Site.query.all()
    elif current_user.has_permission(Permissions.SITES_VIEW_ASSIGNED):
        # Users with sites.view.assigned permission see only their assigned sites
        sites = current_user.sites
    else:
        # Users with no site permissions see only their assigned sites
        sites = current_user.sites
        
    now = datetime.utcnow()
    return render_template('dashboard.html', 
                          sites=sites, 
                          machines=Machine.query.all(),
                          now=now,
                          is_admin=current_user.is_admin,
                          current_user=current_user)

# Admin routes
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    return render_template('admin.html')

# CRUD routes for Sites
@app.route('/admin/sites', methods=['GET', 'POST'])
@login_required
def manage_sites():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        
        new_site = Site(name=name, location=location)
        db.session.add(new_site)
        db.session.commit()
        flash('Site added successfully')
        
    sites = Site.query.all()
    return render_template('admin_sites.html', sites=sites)

# CRUD routes for Machines
@app.route('/admin/machines', methods=['GET', 'POST'])
@login_required
def manage_machines():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        model = request.form.get('model')
        site_id = request.form.get('site_id')
        
        new_machine = Machine(name=name, model=model, site_id=site_id)
        db.session.add(new_machine)
        db.session.commit()
        flash('Machine added successfully')
        
    machines = Machine.query.all()
    sites = Site.query.all()
    return render_template('admin_machines.html', machines=machines, sites=sites)

# CRUD routes for Parts
@app.route('/admin/parts', methods=['GET', 'POST'])
@login_required
def manage_parts():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        machine_id = request.form.get('machine_id')
        maintenance_frequency = int(request.form.get('maintenance_frequency'))
        
        new_part = Part(
            name=name, 
            description=description, 
            machine_id=machine_id, 
            maintenance_frequency=maintenance_frequency,
            last_maintenance=datetime.utcnow()
        )
        db.session.add(new_part)
        db.session.commit()
        flash('Part added successfully')
        
    parts = Part.query.all()
    machines = Machine.query.all()
    return render_template('admin_parts.html', parts=parts, machines=machines)

# Delete routes
@app.route('/admin/sites/delete/<int:site_id>', methods=['POST'])
@login_required
def delete_site(site_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    site = Site.query.get_or_404(site_id)
    db.session.delete(site)
    db.session.commit()
    flash(f'Site "{site.name}" and all associated machines and parts have been deleted')
    return redirect(url_for('manage_sites'))

@app.route('/admin/machines/delete/<int:machine_id>', methods=['POST'])
@login_required
def delete_machine(machine_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    machine = Machine.query.get_or_404(machine_id)
    db.session.delete(machine)
    db.session.commit()
    flash(f'Machine "{machine.name}" and all associated parts have been deleted')
    return redirect(url_for('manage_machines'))

@app.route('/admin/parts/delete/<int:part_id>', methods=['POST'])
@login_required
def delete_part(part_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    part = Part.query.get_or_404(part_id)
    db.session.delete(part)
    db.session.commit()
    flash(f'Part "{part.name}" has been deleted')
    return redirect(url_for('manage_parts'))

@app.route('/admin/parts/update-maintenance/<int:part_id>', methods=['POST'])
@login_required
def update_maintenance(part_id):
    if not current_user.is_admin and not current_user.has_permission(Permissions.MAINTENANCE_RECORD):
        flash('Access denied. You need permission to record maintenance.')
        return redirect(url_for('dashboard'))
    
    part = Part.query.get_or_404(part_id)
    part.last_maintenance = datetime.utcnow()
    part.update_next_maintenance()
    db.session.commit()
    flash(f'Maintenance for "{part.name}" has been updated')
    return redirect(url_for('manage_parts'))

# New routes for Role management
@app.route('/admin/roles', methods=['GET', 'POST'])
@login_required
def manage_roles():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        # Get permissions from multi-select (checkbox group)
        permissions = request.form.getlist('permissions')
        
        new_role = Role(
            name=name, 
            description=description,
            permissions=','.join(permissions)
        )
        db.session.add(new_role)
        db.session.commit()
        flash(f'Role "{name}" added successfully')
    
    roles = Role.query.all()
    return render_template('admin_roles.html', roles=roles, all_permissions=Permissions.get_all_permissions())

# Add a new route for editing a specific role
@app.route('/admin/roles/edit/<int:role_id>', methods=['GET', 'POST'])
@login_required
def edit_role(role_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    role = Role.query.get_or_404(role_id)
    
    if request.method == 'POST':
        # Update role details
        role.name = request.form.get('name')
        role.description = request.form.get('description')
        
        # Update permissions
        permissions = request.form.getlist('permissions')
        role.permissions = ','.join(permissions)
        
        db.session.commit()
        flash(f'Role "{role.name}" updated successfully')
        return redirect(url_for('manage_roles'))
    
    # For GET request, just render the edit form
    role_permissions = role.get_permissions_list()
    return render_template('admin_edit_role.html', role=role, 
                           role_permissions=role_permissions,
                           all_permissions=Permissions.get_all_permissions())

# New route for deleting a specific role
@app.route('/admin/roles/delete/<int:role_id>', methods=['POST'])
@login_required
def delete_role(role_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    role = Role.query.get_or_404(role_id)
    if role.users:
        flash(f'Cannot delete role "{role.name}" because it has assigned users')
        return redirect(url_for('manage_roles'))
        
    db.session.delete(role)
    db.session.commit()
    flash(f'Role "{role.name}" deleted successfully')
    return redirect(url_for('manage_roles'))

# New routes for User management
@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        role_id = request.form.get('role_id')
        is_admin = True if request.form.get('is_admin') else False
        
        if User.query.filter_by(username=username).first():
            flash(f'Username "{username}" already exists')
            roles = Role.query.all()
            users = User.query.all()
            sites = Site.query.all()
            return render_template('admin_users.html', roles=roles, users=users, sites=sites, current_user=current_user)
        
        new_user = User(
            username=username,
            full_name=full_name,
            email=email,
            role_id=role_id if role_id else None,
            is_admin=is_admin
        )
        new_user.set_password(password)
        
        site_ids = request.form.getlist('site_ids')
        for site_id in site_ids:
            site = Site.query.get(site_id)
            if site:
                new_user.sites.append(site)
        
        db.session.add(new_user)
        db.session.commit()
        flash(f'User "{username}" added successfully')
    
    roles = Role.query.all()
    users = User.query.all()
    sites = Site.query.all()
    return render_template('admin_users.html', roles=roles, users=users, sites=sites, current_user=current_user)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    if user_id == current_user.id:
        flash('Cannot delete your own user account')
        return redirect(url_for('manage_users'))
        
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{user.username}" deleted successfully')
    return redirect(url_for('manage_users'))

# Setup database initialization
@app.cli.command("init-db")
def init_db():
    """Initialize the database with sample data."""
    db.create_all()
    
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        # Create roles first with detailed permissions
        admin_role = Role(
            name='Administrator', 
            description='Full system access',
            permissions=','.join([
                # Administrative permissions
                Permissions.ADMIN_ACCESS, Permissions.ADMIN_FULL,
                
                # User management
                Permissions.USERS_VIEW, Permissions.USERS_CREATE, 
                Permissions.USERS_EDIT, Permissions.USERS_DELETE,
                
                # Role management
                Permissions.ROLES_VIEW, Permissions.ROLES_CREATE, 
                Permissions.ROLES_EDIT, Permissions.ROLES_DELETE,
                
                # Site management
                Permissions.SITES_VIEW, Permissions.SITES_CREATE, 
                Permissions.SITES_EDIT, Permissions.SITES_DELETE,
                
                # Machine management
                Permissions.MACHINES_VIEW, Permissions.MACHINES_CREATE, 
                Permissions.MACHINES_EDIT, Permissions.MACHINES_DELETE,
                
                # Part management
                Permissions.PARTS_VIEW, Permissions.PARTS_CREATE, 
                Permissions.PARTS_EDIT, Permissions.PARTS_DELETE,
                
                # Maintenance management
                Permissions.MAINTENANCE_VIEW, Permissions.MAINTENANCE_SCHEDULE, 
                Permissions.MAINTENANCE_RECORD
            ])
        )
        
        manager_role = Role(
            name='Manager', 
            description='Can manage sites and view all data',
            permissions=','.join([
                # Site management
                Permissions.SITES_VIEW, Permissions.SITES_CREATE, Permissions.SITES_EDIT,
                
                # Machine management
                Permissions.MACHINES_VIEW, Permissions.MACHINES_CREATE, Permissions.MACHINES_EDIT,
                
                # Part management
                Permissions.PARTS_VIEW, Permissions.PARTS_CREATE, Permissions.PARTS_EDIT,
                
                # Maintenance management
                Permissions.MAINTENANCE_VIEW, Permissions.MAINTENANCE_SCHEDULE, Permissions.MAINTENANCE_RECORD,
                
                # User management (view only)
                Permissions.USERS_VIEW
            ])
        )
        
        technician_role = Role(
            name='Technician', 
            description='Can update maintenance records for assigned sites',
            permissions=','.join([
                # View permissions - only assigned sites
                Permissions.SITES_VIEW_ASSIGNED, 
                Permissions.MACHINES_VIEW, Permissions.PARTS_VIEW,
                
                # Maintenance permissions
                Permissions.MAINTENANCE_VIEW, Permissions.MAINTENANCE_RECORD
            ])
        )
        db.session.add_all([admin_role, manager_role, technician_role])
        db.session.commit()
        
        # Create admin user
        admin = User(username='admin', full_name='Administrator', email='admin@example.com', is_admin=True, role_id=admin_role.id)
        admin.set_password('admin')
        db.session.add(admin)
        
        # Create test sites
        site1 = Site(name='Main Factory', location='123 Industrial Ave')
        site2 = Site(name='Assembly Plant', location='456 Production Blvd')
        db.session.add_all([site1, site2])
        db.session.commit()
        
        # Create test machines
        machine1 = Machine(name='CNC Mill', model='XYZ-1000', site_id=site1.id)
        machine2 = Machine(name='Lathe', model='LT-500', site_id=site1.id)
        machine3 = Machine(name='Drill Press', model='DP-750', site_id=site2.id)
        machine4 = Machine(name='Assembly Robot', model='AR-200', site_id=site2.id)
        db.session.add_all([machine1, machine2, machine3, machine4])
        db.session.commit()
        
        # Create test parts with varying maintenance frequencies
        parts = [
            Part(name='Spindle', description='Main cutting spindle', machine_id=machine1.id, 
                 maintenance_frequency=3, last_maintenance=datetime.utcnow()),
            Part(name='Coolant System', description='Cutting fluid circulation', machine_id=machine1.id,
                 maintenance_frequency=6, last_maintenance=datetime.utcnow()),
            Part(name='Tool Changer', description='Automatic tool changer', machine_id=machine1.id,
                 maintenance_frequency=2, last_maintenance=datetime.utcnow()),
            Part(name='Chuck', description='Workholding device', machine_id=machine2.id,
                 maintenance_frequency=4, last_maintenance=datetime.utcnow()),
            Part(name='Tailstock', description='Supports workpiece end', machine_id=machine2.id,
                 maintenance_frequency=5, last_maintenance=datetime.utcnow()),
            Part(name='Drill Bit', description='Cutting tool', machine_id=machine3.id,
                 maintenance_frequency=1, last_maintenance=datetime.utcnow()),
            Part(name='Table', description='Work surface', machine_id=machine3.id,
                 maintenance_frequency=4, last_maintenance=datetime.utcnow()),
            Part(name='Servo Motor A', description='Axis 1 movement', machine_id=machine4.id,
                 maintenance_frequency=3, last_maintenance=datetime.utcnow()),
            Part(name='Servo Motor B', description='Axis 2 movement', machine_id=machine4.id,
                 maintenance_frequency=3, last_maintenance=datetime.utcnow()),
            Part(name='Servo Motor C', description='Axis 3 movement', machine_id=machine4.id,
                 maintenance_frequency=3, last_maintenance=datetime.utcnow()),
            Part(name='Gripper', description='End effector', machine_id=machine4.id,
                 maintenance_frequency=2, last_maintenance=datetime.utcnow()),
            Part(name='Controller', description='Robot brain', machine_id=machine4.id,
                 maintenance_frequency=6, last_maintenance=datetime.utcnow()),
            Part(name='Power Supply', description='Electrical power unit', machine_id=machine4.id,
                 maintenance_frequency=5, last_maintenance=datetime.utcnow()),
        ]
        
        # Update next_maintenance for all parts
        for part in parts:
            part.update_next_maintenance()
            
        db.session.add_all(parts)
        db.session.commit()
        print("Database initialized with test data.")
    else:
        print("Database already contains data. Skipping initialization.")

@app.cli.command("reset-db")
def reset_db():
    """Drop and recreate all database tables."""
    db.drop_all()
    db.create_all()
    print("Database has been reset. Run 'flask init-db' to initialize with sample data.")

# Create database tables if they don't exist
with app.app_context():
    # Check if User table exists but doesn't have the new columns
    inspector = db.inspect(db.engine)
    tables_exist = inspector.has_table("user")
    
    if tables_exist:
        columns = [col['name'] for col in inspector.get_columns('user')]
        needs_upgrade = 'role_id' not in columns or 'email' not in columns
        
        if needs_upgrade:
            print("Existing database schema found that needs updating.")
            print("Backing up and upgrading database...")
            
            # Option 1: For simplicity, we'll recreate tables
            backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs('backups', exist_ok=True)
            try:
                # Copy the existing database file to a backup
                import shutil
                shutil.copy2('instance/maintenance.db', f'backups/maintenance_{backup_time}.db')
                print(f"Database backed up to 'backups/maintenance_{backup_time}.db'")
                
                # Drop all tables and recreate them
                db.drop_all()
                print("Old schema dropped")
            except Exception as e:
                print(f"Error during backup: {e}")
    
    # Create all tables
    db.create_all()
    print("Database schema updated")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)