from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import click  # Add the missing click import
from datetime import datetime, timedelta
import logging
from functools import wraps
from flask_mail import Mail, Message
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maintenance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.example.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', 'yes', '1')
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'user@example.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'password')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'maintenance@example.com')

# Initialize Flask-Mail
mail = Mail(app)

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
    enable_notifications = db.Column(db.Boolean, default=False)
    contact_email = db.Column(db.String(100))  # Contact email for notifications
    notification_threshold = db.Column(db.Integer, default=7)  # Days before due date to notify

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
            'ok': ok_parts
        }

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
    notification_sent = db.Column(db.Boolean, default=False)  # Track if notification has been sent

    def __init__(self, **kwargs):
        super(Part, self).__init__(**kwargs)
        if 'maintenance_frequency' in kwargs and 'last_maintenance' in kwargs:
            self.update_next_maintenance()

    def update_next_maintenance(self):
        """Update next maintenance date and reset notification status"""
        self.next_maintenance = self.last_maintenance + timedelta(days=self.maintenance_frequency)
        self.notification_sent = False  # Reset notification status when maintenance is done

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
        contact_email = request.form.get('contact_email')
        enable_notifications = True if request.form.get('enable_notifications') else False
        notification_threshold = int(request.form.get('notification_threshold', 7))
        new_site = Site(name=name, location=location, contact_email=contact_email,
                        enable_notifications=enable_notifications, notification_threshold=notification_threshold)
        db.session.add(new_site)
        db.session.commit()
        flash('Site added successfully')
    sites = Site.query.all()
    return render_template('admin_sites.html', sites=sites)

@app.route('/admin/sites/edit/<int:site_id>', methods=['GET', 'POST'])
@login_required
def edit_site(site_id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    site = Site.query.get_or_404(site_id)
    if request.method == 'POST':
        site.name = request.form.get('name')
        site.location = request.form.get('location')
        site.contact_email = request.form.get('contact_email')
        site.enable_notifications = True if request.form.get('enable_notifications') else False
        site.notification_threshold = int(request.form.get('notification_threshold', 7))
        db.session.commit()
        flash(f'Site "{site.name}" updated successfully')
        return redirect(url_for('manage_sites'))
    return render_template('admin_edit_site.html', site=site)

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

@app.route('/admin/machines/edit/<int:machine_id>', methods=['GET', 'POST'])
@login_required
def edit_machine(machine_id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    machine = Machine.query.get_or_404(machine_id)
    if request.method == 'POST':
        machine.name = request.form.get('name')
        machine.model = request.form.get('model')
        machine.site_id = request.form.get('site_id')
        db.session.commit()
        flash(f'Machine "{machine.name}" updated successfully')
        return redirect(url_for('manage_machines'))
    sites = Site.query.all()
    return render_template('admin_edit_machine.html', machine=machine, sites=sites)

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
        new_part = Part(name=name, description=description, machine_id=machine_id,
                        maintenance_frequency=maintenance_frequency, last_maintenance=datetime.utcnow())
        db.session.add(new_part)
        db.session.commit()
        flash('Part added successfully')
    parts = Part.query.all()
    machines = Machine.query.all()
    return render_template('admin_parts.html', parts=parts, machines=machines)

@app.route('/admin/parts/edit/<int:part_id>', methods=['GET', 'POST'])
@login_required
def edit_part(part_id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    part = Part.query.get_or_404(part_id)
    if request.method == 'POST':
        part.name = request.form.get('name')
        part.description = request.form.get('description')
        part.machine_id = request.form.get('machine_id')
        part.maintenance_frequency = int(request.form.get('maintenance_frequency'))
        part.last_maintenance = datetime.utcnow()
        part.update_next_maintenance()
        db.session.commit()
        flash(f'Part "{part.name}" updated successfully')
        return redirect(url_for('manage_parts'))
    machines = Machine.query.all()
    return render_template('admin_edit_part.html', part=part, machines=machines)

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
        permissions = request.form.getlist('permissions')
        new_role = Role(name=name, description=description, permissions=','.join(permissions))
        db.session.add(new_role)
        db.session.commit()
        flash(f'Role "{name}" added successfully')
        return redirect(url_for('admin'))
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
        role.name = request.form.get('name')
        role.description = request.form.get('description')
        permissions = request.form.getlist('permissions')
        role.permissions = ','.join(permissions)
        db.session.commit()
        flash(f'Role "{role.name}" updated successfully')
        return redirect(url_for('manage_roles'))
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
    
    role_name = role.name
    db.session.delete(role)
    db.session.commit()
    flash(f'Role "{role_name}" deleted successfully')
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
        site_ids = request.form.getlist('site_ids')
        if User.query.filter_by(username=username).first():
            flash(f'Username "{username}" already exists')
            roles = Role.query.all()
            users = User.query.all()
            sites = Site.query.all()
            return render_template('admin_users.html', roles=roles, users=users, sites=sites, current_user=current_user)
        new_user = User(username=username, full_name=full_name, email=email,
                        role_id=role_id if role_id else None, is_admin=is_admin)
        new_user.set_password(password)
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

# Function to check for parts needing notification and send emails
def check_for_due_soon_parts():
    """Check for parts that have newly entered the 'due soon' threshold and send notifications"""
    now = datetime.utcnow()
    # Find sites that have notifications enabled
    sites_with_notifications = []
    for site in Site.query.filter_by(enable_notifications=True).all():
        if not site.contact_email:
            app.logger.info(f"Site {site.name} has notifications enabled but no contact email")
            continue
        overdue_parts = []
        due_soon_parts = []
        parts_to_mark = []  # Parts to mark as notified
        
        for machine in site.machines:
            for part in machine.parts:
                # Skip parts that have already had notifications sent
                if part.notification_sent:
                    continue
                    
                days_until = (part.next_maintenance - now).days
                
                if days_until < 0:
                    overdue_parts.append({
                        'machine': machine.name,
                        'part': part.name,
                        'days': abs(days_until),
                        'due_date': part.next_maintenance.strftime('%Y-%m-%d'),
                        'part_id': part.id
                    })
                    parts_to_mark.append(part)
                elif days_until <= site.notification_threshold:
                    due_soon_parts.append({
                        'machine': machine.name,
                        'part': part.name,
                        'days': days_until,
                        'due_date': part.next_maintenance.strftime('%Y-%m-%d'),
                        'part_id': part.id
                    })
                    parts_to_mark.append(part)
        
        if overdue_parts or due_soon_parts:
            sites_with_notifications.append({
                'site': site,
                'overdue_parts': overdue_parts,
                'due_soon_parts': due_soon_parts,
                'parts_to_mark': parts_to_mark
            })
    
    # Send emails for each site
    sent_count = 0
    for site_info in sites_with_notifications:
        site = site_info['site']
        overdue_parts = site_info['overdue_parts']
        due_soon_parts = site_info['due_soon_parts']
        parts_to_mark = site_info['parts_to_mark']
        
        # Create email content
        subject = f"Maintenance Alert: {site.name}"
        
        # Render email template
        html_body = render_template(
            'email/maintenance_alert.html',
            site=site,
            overdue_parts=overdue_parts,
            due_soon_parts=due_soon_parts,
            threshold=site.notification_threshold
        )
        
        # Create and send the email
        try:
            msg = Message(
                subject=subject,
                recipients=[site.contact_email],
                html=html_body
            )
            mail.send(msg)
            app.logger.info(f"Maintenance notification sent to {site.contact_email} for site {site.name}")
            sent_count += 1
            
            # Mark parts as notified
            for part in parts_to_mark:
                part.notification_sent = True
            
            db.session.commit()
        except Exception as e:
            app.logger.error(f"Failed to send notification email: {str(e)}")
    
    return sent_count

# Add the missing route for checking notifications
@app.route('/admin/check-notifications', methods=['GET'])
@login_required
def check_notifications():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    count = check_for_due_soon_parts()
    if count > 0:
        flash(f'Sent notifications for {count} sites with parts due soon or overdue.')
    else:
        flash('No new notifications to send.')
    return redirect(url_for('admin'))

# CLI commands
@app.cli.command("init-db")
def init_db():
    """Initialize the database with sample data."""
    db.create_all()
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        # Create roles first with detailed permissions
        admin_role = Role(name='Administrator', description='Full system access',
                          permissions=','.join([
                              Permissions.ADMIN_ACCESS, Permissions.ADMIN_FULL,
                              Permissions.USERS_VIEW, Permissions.USERS_CREATE, Permissions.USERS_EDIT, Permissions.USERS_DELETE,
                              Permissions.ROLES_VIEW, Permissions.ROLES_CREATE, Permissions.ROLES_EDIT, Permissions.ROLES_DELETE,
                              Permissions.SITES_VIEW, Permissions.SITES_CREATE, Permissions.SITES_EDIT, Permissions.SITES_DELETE, Permissions.SITES_VIEW_ASSIGNED,
                              Permissions.MACHINES_VIEW, Permissions.MACHINES_CREATE, Permissions.MACHINES_EDIT, Permissions.MACHINES_DELETE,
                              Permissions.PARTS_VIEW, Permissions.PARTS_CREATE, Permissions.PARTS_EDIT, Permissions.PARTS_DELETE,
                              Permissions.MAINTENANCE_VIEW, Permissions.MAINTENANCE_SCHEDULE, Permissions.MAINTENANCE_RECORD
                          ]))
        manager_role = Role(name='Manager', description='Can manage sites and view all data',
                            permissions=','.join([
                                Permissions.SITES_VIEW, Permissions.SITES_CREATE, Permissions.SITES_EDIT, Permissions.SITES_DELETE,
                                Permissions.MACHINES_VIEW, Permissions.MACHINES_CREATE, Permissions.MACHINES_EDIT, Permissions.MACHINES_DELETE,
                                Permissions.PARTS_VIEW, Permissions.PARTS_CREATE, Permissions.PARTS_EDIT, Permissions.PARTS_DELETE,
                                Permissions.MAINTENANCE_VIEW, Permissions.MAINTENANCE_RECORD
                            ]))
        technician_role = Role(name='Technician', description='Can update maintenance records for assigned sites',
                               permissions=','.join([
                                   Permissions.SITES_VIEW_ASSIGNED,
                                   Permissions.MACHINES_VIEW, Permissions.PARTS_VIEW,
                                   Permissions.MAINTENANCE_VIEW, Permissions.MAINTENANCE_RECORD
                               ]))
        db.session.add_all([admin_role, manager_role, technician_role])
        db.session.commit()

        # Create admin user
        admin = User(username='admin', full_name='Administrator', email='admin@example.com', is_admin=True, role_id=admin_role.id)
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()

        # Create test sites
        site1 = Site(name='Main Factory', location='123 Industrial Ave')
        site2 = Site(name='Assembly Plant', location='456 Production Blvd', enable_notifications=True,
                     contact_email='factory.manager@example.com', notification_threshold=7)
        db.session.add_all([site1, site2])
        db.session.commit()

        # Create test machines
        machine1 = Machine(name='CNC Mill', model='XYZ-1000', site_id=site1.id)
        machine2 = Machine(name='Lathe', model='LT-500', site_id=site1.id)
        machine3 = Machine(name='Drill Press', model='DP-750', site_id=site2.id)
        machine4 = Machine(name='Assembly Robot', model='AR-200', site_id=site2.id)
        db.session.add_all([machine1, machine2, machine3, machine4])
        db.session.commit()

        # Current date for reference
        now = datetime.utcnow()

        # Create test parts with varying maintenance frequencies and past maintenance dates
        parts = [
            # Overdue parts (past maintenance date)
            Part(name='Spindle', description='Main cutting spindle', machine_id=machine1.id,
                 maintenance_frequency=7, last_maintenance=now - timedelta(days=10)),  # 3 days overdue
            Part(name='Coolant System', description='Cutting fluid circulation', machine_id=machine1.id,
                 maintenance_frequency=14, last_maintenance=now - timedelta(days=20)),  # 6 days overdue
            Part(name='Tool Changer', description='Automatic tool changer', machine_id=machine1.id,
                 maintenance_frequency=30, last_maintenance=now - timedelta(days=20)),  # Due in 10 days
            Part(name='Chuck', description='Workholding device', machine_id=machine2.id,
                 maintenance_frequency=21, last_maintenance=now - timedelta(days=15)),  # Due in 6 days
            Part(name='Tailstock', description='Supports workpiece end', machine_id=machine2.id,
                 maintenance_frequency=30, last_maintenance=now - timedelta(days=22)),  # Due in 8 days
            # OK parts (maintenance due beyond 14 days)
            Part(name='Drill Bit', description='Cutting tool', machine_id=machine3.id,
                 maintenance_frequency=45, last_maintenance=now - timedelta(days=20)),  # Due in 25 days
            Part(name='Table', description='Work surface', machine_id=machine3.id,
                 maintenance_frequency=60, last_maintenance=now - timedelta(days=15)),  # Due in 45 days
            Part(name='Servo Motor A', description='Axis 1 movement', machine_id=machine4.id,
                 maintenance_frequency=60, last_maintenance=now - timedelta(days=20)),  # Due in 40 days
            Part(name='Servo Motor B', description='Axis 2 movement', machine_id=machine4.id,
                 maintenance_frequency=90, last_maintenance=now - timedelta(days=30)),  # Due in 60 days
            Part(name='Servo Motor C', description='Axis 3 movement', machine_id=machine4.id,
                 maintenance_frequency=90, last_maintenance=now - timedelta(days=30)),  # Due in 60 days
            Part(name='Controller', description='Robot brain', machine_id=machine4.id,
                 maintenance_frequency=180, last_maintenance=now - timedelta(days=30)),  # Due in 150 days
            Part(name='Power Supply', description='Electrical power unit', machine_id=machine4.id,
                 maintenance_frequency=365, last_maintenance=now - timedelta(days=90)),  # Due in 275 days
            Part(name='Gripper', description='End effector', machine_id=machine4.id,
                 maintenance_frequency=120, last_maintenance=now - timedelta(days=20))  # Due in 100 days
        ]
        db.session.add_all(parts)
        db.session.commit()

        # Update next_maintenance for all parts
        for part in parts:
            part.update_next_maintenance()
        db.session.commit()
        print("Database initialized with test data.")
    else:
        print("Database already contains data. Skipping initialization.")

@app.cli.command("send-notifications")
def send_all_notifications():
    """Send maintenance notifications for all sites that have them enabled."""
    sent_count = check_for_due_soon_parts()
    print(f"Sent {sent_count} notification emails.")

@app.cli.command("reset-db")
def reset_db():
    """Drop and recreate all database tables."""
    db.drop_all()
    db.create_all()
    print("Database has been reset. Run 'flask init-db' to initialize with sample data.")

@app.cli.command("check-db")
def check_db():
    """Check if the database schema needs to be updated."""
    with app.app_context():
        inspector = db.inspect(db.engine)
        tables_exist = inspector.has_table("part")
        if tables_exist:
            columns = [col['name'] for col in inspector.get_columns('part')]
            if 'notification_sent' not in columns:
                print("Database schema needs updating - 'notification_sent' column is missing.")
                print("Please run 'flask --app app reset-db' to update the database schema.")
            else:
                print("Database schema is up to date.")
        else:
            print("Database tables don't exist. Run 'flask --app app init-db' to initialize.")

@app.cli.command("check-notification-settings")
def check_notification_settings():
    """Display notification settings for all sites."""
    sites = Site.query.all()
    if not sites:
        print("No sites found in database.")
        return
                
    print("\nNotification Settings for Sites:")
    print("--------------------------------------")
    for site in sites:
        print(f"\nSite: {site.name}")
        print(f"  Notifications Enabled: {site.enable_notifications}")
        print(f"  Contact Email: {site.contact_email or 'NOT SET'}")
        print(f"  Notification Threshold: {site.notification_threshold} days")
        now = datetime.utcnow()
        parts_notified = 0
        parts_overdue = 0
        parts_due_soon = 0
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
        print(f"    - Overdue: {parts_overdue}")
        print(f"    - Due soon: {parts_due_soon}")
        print(f"    - Already notified: {parts_notified}")

@app.cli.command("create-excel-template")
@click.argument("output_file", default="maintenance_import_template.xlsx")
def create_excel_template_cmd(output_file):
    """Create a template Excel file for importing maintenance data."""
    from create_excel_template import create_template
    create_template(output_file)
    print(f"Template created: {output_file}")

@app.cli.command("import-excel")
@click.argument("file_path")
def import_excel_cmd(file_path):
    """Import maintenance data from an Excel file.
    
    FILE_PATH is the path to the Excel file to import.
    
    The Excel file should contain the following sheets:
    - Sites: with columns for name, location, contact_email, enable_notifications, notification_threshold
    - Machines: with columns for name, model, site_name
    - Parts: with columns for name, description, machine_name, site_name, maintenance_frequency, last_maintenance
    """
    try:
        stats = import_excel(file_path)
        print("Import completed successfully!")
        print(f"Sites: {stats['sites_added']} added, {stats['sites_skipped']} skipped")
        print(f"Machines: {stats['machines_added']} added, {stats['machines_skipped']} skipped")
        print(f"Parts: {stats['parts_added']} added, {stats['parts_skipped']} skipped")
        print(f"Errors: {stats['errors']}")
    except Exception as e:
        print(f"Import failed: {str(e)}")

@app.route('/admin/test-email', methods=['GET', 'POST'])
@login_required
def test_email():
    """Send a test email to verify email configuration."""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        recipient = request.form.get('email')
        subject = request.form.get('subject', 'Maintenance Tracker - Test Email')
        message = request.form.get('message', 'This is a test email from the Maintenance Tracker system.')
        site_name = request.form.get('site_name', 'Test Site')
        site_location = request.form.get('site_location', 'Test Location')
        notification_threshold = int(request.form.get('notification_threshold', 7))
        include_samples = 'include_samples' in request.form
        
        # Sample data for overdue and due-soon items
        sample_data = {}
        if include_samples:
            now = datetime.utcnow()
            threshold = notification_threshold
            
            # Sample overdue parts
            sample_data['overdue_parts'] = [
                {
                    'machine': 'CNC Mill',
                    'part': 'Spindle',
                    'days': 3,
                    'due_date': (now - timedelta(days=3)).strftime('%Y-%m-%d'),
                    'part_id': 1
                },
                {
                    'machine': 'Lathe',
                    'part': 'Chuck',
                    'days': 5,
                    'due_date': (now - timedelta(days=5)).strftime('%Y-%m-%d'),
                    'part_id': 2
                }
            ]
            
            # Sample due-soon parts
            sample_data['due_soon_parts'] = [
                {
                    'machine': 'Assembly Robot',
                    'part': 'Servo Motor',
                    'days': 2,
                    'due_date': (now + timedelta(days=2)).strftime('%Y-%m-%d'),
                    'part_id': 3
                },
                {
                    'machine': 'CNC Mill',
                    'part': 'Coolant System',
                    'days': threshold - 1,
                    'due_date': (now + timedelta(days=threshold - 1)).strftime('%Y-%m-%d'),
                    'part_id': 4
                }
            ]
            
            # Sample site info
            sample_data['site'] = {
                'name': site_name,
                'location': site_location
            }
            
            sample_data['threshold'] = threshold
        
        try:
            msg = Message(
                subject=subject,
                recipients=[recipient],
                html=render_template('email/test_email.html', 
                                    message=message,
                                    now=datetime.utcnow(),
                                    **sample_data)
            )
            mail.send(msg)
            flash(f'Test email sent to {recipient} successfully!')
        except Exception as e:
            flash(f'Failed to send test email: {str(e)}')
        
        return redirect(url_for('test_email'))
    
    # Get current email configuration
    email_config = {
        'MAIL_SERVER': app.config['MAIL_SERVER'],
        'MAIL_PORT': app.config['MAIL_PORT'],
        'MAIL_USE_TLS': app.config['MAIL_USE_TLS'],
        'MAIL_USERNAME': app.config['MAIL_USERNAME'],
        'MAIL_DEFAULT_SENDER': app.config['MAIL_DEFAULT_SENDER']
    }
    
    return render_template('admin_test_email.html', config=email_config)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)