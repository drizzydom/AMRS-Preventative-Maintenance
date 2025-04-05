from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
from flask_mail import Mail, Message
from dotenv import load_dotenv
from sqlalchemy import text, inspect
from sqlalchemy.orm.attributes import flag_modified
import os
import sys
import logging
import secrets

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Get the directory of this file
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Define dotenv_path before using it
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)

# Ensure .env file exists
def ensure_env_file():
    if not os.path.exists(dotenv_path):
        print(f"[APP] .env file not found at {dotenv_path}. Using environment variables.")

# Ensure email template directories exist
def ensure_email_templates():
    templates_dir = os.path.join(BASE_DIR, 'templates')
    email_dir = os.path.join(templates_dir, 'email')
    # Create templates directory if it doesn't exist
    if not os.path.exists(templates_dir):
        print(f"[APP] Creating templates directory: {templates_dir}")
        os.makedirs(templates_dir, exist_ok=True)
    
    # Create email directory if it doesn't exist
    if not os.path.exists(email_dir):
        print(f"[APP] Creating email templates directory: {email_dir}")
        os.makedirs(email_dir, exist_ok=True)
    
    # Check if template files exist
    print("[APP] Checking email templates...")
    # ... rest of your email templates code ...

# Call these setup functions
ensure_env_file()
ensure_email_templates()

# Print debug info about environment
print(f"[APP] Running in environment: {'RENDER' if os.environ.get('RENDER') else 'LOCAL'}")
print(f"[APP] Working directory: {os.getcwd()}")
print(f"[APP] Base directory: {BASE_DIR}")

try:
    # Import cache configuration
    from cache_config import configure_caching
except ImportError:
    print("[APP] Warning: cache_config module not found")
    configure_caching = None

try:
    # Import database configuration
    from db_config import configure_database
except ImportError as e:
    print(f"[APP] Error importing db_config: {str(e)}")
    # Define a simple fallback if import fails
    def configure_database(app):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maintenance.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        return app

# Initialize Flask app with better error handling
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')
app.config['APPLICATION_ROOT'] = os.environ.get('APPLICATION_ROOT', '/')
app.config['PREFERRED_URL_SCHEME'] = os.environ.get('PREFERRED_URL_SCHEME', 'https')

# Ensure URLs work with and without trailing slashes
app.url_map.strict_slashes = False

# Configure the database
try:
    print("[APP] Configuring database...")
    configure_database(app)
except Exception as e:
    print(f"[APP] Error configuring database: {str(e)}")
    # Set a fallback configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maintenance.db'

# Initialize database
print("[APP] Initializing SQLAlchemy...")
db = SQLAlchemy(app)

# Define User model - MUST BE DEFINED BEFORE any references to User
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100))
    full_name = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def __repr__(self):
        return f'<User {self.username}>'

# Define Role model
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    permissions = db.Column(db.String(500), default="view")
    users = db.relationship('User', backref='role', lazy=True)
    
    def get_permissions_list(self):
        if self.permissions:
            return self.permissions.split(',')
        return []
        
    def __repr__(self):
        return f'<Role {self.name}>'

# Initialize Flask-Login - CRITICAL: This must be done after User model is defined
print("[APP] Initializing Flask-Login...")
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Specify the login view endpoint for @login_required
login_manager.login_message_category = 'info'  # Flash message category for login messages

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    # This must return None or a User object
    return User.query.get(int(user_id)) if user_id else None

# Add error handlers with fallbacks
@app.errorhandler(404)
def page_not_found(e):
    try:
        return render_template('errors/404.html'), 404
    except:
        # Fallback to simple HTML response if template is missing
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>Page Not Found</title></head>
        <body style="font-family:Arial; text-align:center; padding:50px;">
            <h1 style="color:#FE7900;">Page Not Found</h1>
            <p>The requested page was not found. Please check the URL or go back to the <a href="/" style="color:#FE7900;">home page</a>.</p>
        </body>
        </html>
        ''', 404

@app.errorhandler(500)
def server_error(e):
    try:
        return render_template('errors/500.html'), 500
    except:
        # Fallback to simple HTML response if template is missing
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>Server Error</title></head>
        <body style="font-family:Arial; text-align:center; padding:50px;">
            <h1 style="color:#FE7900;">Server Error</h1>
            <p>Sorry, something went wrong on our end. Please try again later or go back to the <a href="/" style="color:#FE7900;">home page</a>.</p>
        </body>
        </html>
        ''', 500

# Make sure your login route is defined
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    # If user is already authenticated, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # Handle login form submission
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Find the user
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists and password is correct
        if user and user.check_password(password):
            # Log the user in
            login_user(user)
            flash('Login successful', 'success')
            
            # Redirect to the requested page or dashboard
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    # Render login template for GET requests
    return render_template('login.html', now=datetime.now())

# Make sure you have a logout route
@app.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# Add a dashboard route if it doesn't exist
@app.route('/dashboard')
@login_required
def dashboard():
    """Show the main dashboard"""
    # Add your dashboard logic here
    return render_template('dashboard.html')

# Root route handler
@app.route('/')
def index():
    """Root route that redirects to the dashboard or login page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

# Add debug route to check application
@app.route('/debug-info')
def debug_info():
    """Debug route to check application status"""
    output = {
        "status": "running",
        "time": datetime.now().isoformat(),
        "routes": [str(rule) for rule in app.url_map.iter_rules()],
        "flask_login_initialized": hasattr(app, 'login_manager'),
        "current_user": str(current_user) if 'current_user' in globals() else "Not available",
        "is_authenticated": current_user.is_authenticated if 'current_user' in globals() else False
    }
    return jsonify(output)

# Add health check route for diagnostics
@app.route('/health')
def health_check():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "environment": os.environ.get('FLASK_ENV', 'production'),
        "render": os.environ.get('RENDER', 'false')
    })

# Add password reset functionality
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password requests"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate a secure token for this user
            reset_token = jwt.encode(
                {
                    'user_id': user.id,
                    'exp': datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
                },
                app.config['SECRET_KEY'],
                algorithm='HS256'
            )
            
            # Create reset link
            reset_url = url_for('reset_password', user_id=user.id, token=reset_token, _external=True)
            
            # For now, just print the reset URL to the console for testing
            print(f"Password reset link for {user.username}: {reset_url}")
            
            # TODO: Send email with reset link
            # In a production environment, you would send an email with the reset link
            
            flash('If an account exists with that email, a password reset link has been sent.', 'info')
            return redirect(url_for('login'))
        else:
            # Don't reveal that the user doesn't exist
            flash('If an account exists with that email, a password reset link has been sent.', 'info')
            return redirect(url_for('login'))
    
    return render_template('forgot_password.html', now=datetime.now())

@app.route('/reset-password/<int:user_id>/<token>', methods=['GET', 'POST'])
def reset_password(user_id, token):
    """Handle password reset with token"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    user = User.query.get(user_id)
    if not user:
        flash('Invalid or expired reset link.', 'error')
        return redirect(url_for('login'))
        
    try:
        # Verify the token
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        if payload['user_id'] != user_id:
            raise Exception("Token doesn't match user")
    except:
        flash('Invalid or expired reset link.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('reset_password.html', user_id=user_id, token=token)
            
        if len(password) < 8:
            flash('Password must be at least 8 characters', 'error')
            return render_template('reset_password.html', user_id=user_id, token=token)
        
        # Update user's password
        user.set_password(password)
        db.session.commit()
        
        flash('Your password has been updated. Please log in with your new password.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', user_id=user_id, token=token)

# Create admin function
def create_default_admin():
    """Create a default admin account if no users exist"""
    try:
        print("[APP] Checking for existing users...")
        
        # Check if users table exists
        inspector = inspect(db.engine)
        if 'user' not in inspector.get_table_names():
            print("[APP] Users table doesn't exist yet, creating all tables...")
            db.create_all()
        
        # Check for existing users
        user_count = User.query.count()
        
        if user_count == 0:
            print("[APP] No users found. Creating default admin user...")
            
            # Check if Roles table exists and has Administrator role
            admin_role = None
            if 'role' in inspector.get_table_names():
                admin_role = Role.query.filter_by(name="Administrator").first()
                
            # Create admin role if needed
            if not admin_role:
                print("[APP] Creating Administrator role...")
                
                # Handle case where get_all_permissions may not exist
                try:
                    permissions = Permissions.get_all_permissions() if hasattr(Permissions, 'get_all_permissions') else "admin"
                    permissions_string = ",".join(permissions)
                except:
                    permissions_string = "admin.full"
                
                admin_role = Role(
                    name="Administrator",
                    description="Full system access",
                    permissions=permissions_string
                )
                db.session.add(admin_role)
                db.session.commit()
            
            # Create admin user with username "admin" and password "admin"
            admin_user = User(
                username="admin",
                email="admin@example.com",
                full_name="System Administrator", 
                is_admin=True,
                role_id=admin_role.id if admin_role else None
            )
            
            # Set password - handle different implementations
            if hasattr(admin_user, 'set_password'):
                admin_user.set_password("admin")
            else:
                admin_user.password_hash = generate_password_hash("admin")
            
            db.session.add(admin_user)
            db.session.commit()
            
            print("[APP] Created default admin user 'admin' with password 'admin'")
            print("[APP] WARNING: This is intended for testing only.")
            print("[APP] IMPORTANT: Change this password when deploying to production!")
            
            return True
        else:
            print(f"[APP] {user_count} users already exist, not creating default admin")
            return False
            
    except Exception as e:
        print(f"[APP] Error creating default admin: {str(e)}")
        return False

# Add default user if none exist - ensures at least one admin exists after fresh deployments
def add_default_admin_if_needed():
    """Add a default admin user if no users exist in the database"""
    try:
        print("[APP] Checking for default admin user...")
        
        # First make sure tables exist
        with app.app_context():
            inspector = inspect(db.engine)
            if 'user' not in inspector.get_table_names():
                print("[APP] User table doesn't exist yet. Will create tables first.")
                db.create_all()
                print("[APP] Tables created.")
            
            # Check if any users exist
            user_count = User.query.count()
            
            if user_count == 0:
                print("[APP] No users found in database. Creating default admin user.")
                
                # Create default admin role if needed
                admin_role = Role.query.filter_by(name="Administrator").first()
                if not admin_role:
                    print("[APP] Creating Administrator role with full permissions.")
                    admin_role = Role(
                        name="Administrator",
                        description="Full system access",
                        permissions="admin.full"  # Full administrator access
                    )
                    db.session.add(admin_role)
                    db.session.commit()
                
                # Create default admin user with simple password for testing
                admin_user = User(
                    username="admin",
                    email="admin@example.com",
                    full_name="System Administrator",
                    is_admin=True,
                    role_id=admin_role.id if admin_role else None
                )
                admin_user.set_password("admin")  # Simple password for testing
                
                db.session.add(admin_user)
                db.session.commit()
                
                print("[APP] Created default admin user 'admin' with password 'admin'")
                print("[APP] WARNING: This is intended for testing only.")
                print("[APP] IMPORTANT: Please change this password immediately after login.")
                
                return admin_user
            else:
                print(f"[APP] Found {user_count} existing users in database - no default admin needed.")
                return None
    except Exception as e:
        print(f"[APP] Error creating default admin: {str(e)}")
        return None

# Call this function when app initializes
with app.app_context():
    try:
        create_default_admin()
    except Exception as e:
        print(f"[APP] Error during startup initialization: {str(e)}")

# AFTER all models are defined, THEN create tables
if os.environ.get('RENDER', False):
    print("[APP] Running on Render, creating database tables...")
    with app.app_context():
        try:
            db.create_all()
            print("[APP] Database tables created successfully.")
            # Add default admin user if needed
            add_default_admin_if_needed()
        except Exception as e:
            print(f"[APP] Error creating database tables: {str(e)}", file=sys.stderr)

# Routes for main navigation items
@app.route('/sites')
@login_required
def manage_sites():
    """Handle site management page"""
    sites = []  # In a full implementation, you'd fetch sites from the database
    return render_template('sites.html', 
                          sites=sites,
                          now=datetime.now(),
                          can_create=True,
                          can_edit=True,
                          can_delete=True)

@app.route('/machines')
@login_required
def manage_machines():
    """Handle machine management page"""
    machines = []  # In a full implementation, you'd fetch machines from the database
    sites = []     # Sites for dropdown selection
    site_id = request.args.get('site_id')
    title = "Machines"
    return render_template('machines.html', 
                          machines=machines,
                          sites=sites,
                          site_id=site_id,
                          title=title,
                          now=datetime.now(),
                          can_create=True,
                          can_edit=True,
                          can_delete=True)

@app.route('/parts')
@login_required
def manage_parts():
    """Handle parts management page"""
    parts = []     # In a full implementation, you'd fetch parts from the database
    machines = []  # Machines for dropdown selection
    machine_id = request.args.get('machine_id')
    title = "Parts"
    return render_template('parts.html', 
                          parts=parts,
                          machines=machines,
                          machine_id=machine_id,
                          title=title,
                          now=datetime.now(),
                          can_create=True,
                          can_edit=True,
                          can_delete=True)

@app.route('/profile')
@login_required
def user_profile():
    """Handle user profile page"""
    return render_template('profile.html', user=current_user)

@app.route('/admin')
@login_required
def admin():
    """Admin dashboard - only accessible to admin users"""
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area.', 'error')
        return redirect(url_for('dashboard'))
    
    # Placeholder counts - in a real app, you'd query the database
    user_count = 1
    site_count = 0
    machine_count = 0
    part_count = 0
    
    return render_template('admin.html',
                          user_count=user_count,
                          site_count=site_count,
                          machine_count=machine_count,
                          part_count=part_count)

# Admin sub-pages
@app.route('/admin/users')
@login_required
def manage_users():
    """User management page"""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('dashboard'))
    
    users = [current_user]  # In a real app, you'd query all users
    roles = []
    sites = []
    
    return render_template('admin_users.html', users=users, roles=roles, sites=sites)

@app.route('/admin/roles')
@login_required
def manage_roles():
    """Role management page"""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('dashboard'))
    
    roles = []
    all_permissions = {"view": "View Content", "edit": "Edit Content"}  # Example permissions
    
    return render_template('admin_roles.html', roles=roles, all_permissions=all_permissions)

@app.route('/admin/backups')
@login_required
def manage_backups():
    """Database backup management page"""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('dashboard'))
    
    backups = []
    
    return render_template('admin_backups.html', backups=backups)

# Placeholder routes for CRUD operations (these would be implemented with actual logic)
@app.route('/sites/add', methods=['POST'])
@login_required
def add_site():
    flash('Site creation not implemented yet', 'warning')
    return redirect(url_for('manage_sites'))

@app.route('/sites/edit/<int:site_id>', methods=['GET', 'POST'])
@login_required
def edit_site(site_id):
    site = {"id": site_id, "name": "Example Site", "location": "Example Location"}
    return render_template('edit_site.html', site=site, users=[])

@app.route('/sites/delete/<int:site_id>', methods=['POST'])
@login_required
def delete_site(site_id):
    """Delete a site and all its machines and parts"""
    try:
        site = Site.query.get_or_404(site_id)
        
        # Check permissions (optional - implement based on your authentication system)
        # if not current_user.is_admin and not current_user.has_permission('delete_site'):
        #     flash('You do not have permission to delete sites.', 'error')
        #     return redirect(url_for('manage_sites'))
        
        site_name = site.name
        
        # Delete all parts associated with this site's machines
        parts_count = 0
        # Get all machines for this site
        machines = Machine.query.filter_by(site_id=site_id).all()
        for machine in machines:
            # Delete parts for each machine
            parts = Part.query.filter_by(machine_id=machine.id).all()
            parts_count += len(parts)
            for part in parts:
                db.session.delete(part)
        
        # Delete all machines for this site
        machines_count = Machine.query.filter_by(site_id=site_id).count()
        Machine.query.filter_by(site_id=site_id).delete()
        
        # Delete the site
        db.session.delete(site)
        db.session.commit()
        
        flash(f'Site "{site_name}" with {machines_count} machines and {parts_count} parts has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting site: {str(e)}', 'error')
    
    return redirect(url_for('manage_sites'))

# Part Management Routes
@app.route('/parts/delete/<int:part_id>', methods=['POST'])
@login_required
def delete_part(part_id):
    """Delete a part from the system"""
    try:
        part = Part.query.get_or_404(part_id)
        
        # Check permissions (optional - implement based on your authentication system)
        # if not current_user.is_admin and not current_user.has_permission('delete_part'):
        #     flash('You do not have permission to delete parts.', 'error')
        #     return redirect(url_for('manage_parts'))
        
        # Store information for flash message
        part_name = part.name
        machine_id = part.machine_id
        
        # Delete part
        db.session.delete(part)
        db.session.commit()
        
        flash(f'Part "{part_name}" has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting part: {str(e)}', 'error')
    
    # Redirect back to the machine's parts page if we know the machine_id
    if 'machine_id' in locals():
        return redirect(url_for('manage_parts', machine_id=machine_id))
    else:
        return redirect(url_for('manage_parts'))

# Machine Management Routes
@app.route('/machines/delete/<int:machine_id>', methods=['POST'])
@login_required
def delete_machine(machine_id):
    """Delete a machine and all its parts"""
    try:
        machine = Machine.query.get_or_404(machine_id)
        
        # Check permissions (optional - implement based on your authentication system)
        # if not current_user.is_admin and not current_user.has_permission('delete_machine'):
        #     flash('You do not have permission to delete machines.', 'error')
        #     return redirect(url_for('manage_machines'))
        
        # Store information for flash message and redirect
        machine_name = machine.name
        site_id = machine.site_id
        
        # Delete all parts associated with this machine
        parts_count = Part.query.filter_by(machine_id=machine_id).count()
        Part.query.filter_by(machine_id=machine_id).delete()
        
        # Delete the machine
        db.session.delete(machine)
        db.session.commit()
        
        flash(f'Machine "{machine_name}" and its {parts_count} parts have been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting machine: {str(e)}', 'error')
    
    # Redirect back to the site's machines page if we know the site_id
    if 'site_id' in locals():
        return redirect(url_for('manage_machines', site_id=site_id))
    else:
        return redirect(url_for('manage_machines'))

# User Management Routes
@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Edit an existing user"""
    # Ensure user has admin privileges
    if not current_user.is_admin:
        flash('You do not have permission to edit users.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    roles = Role.query.all()
    sites = Site.query.all()
    
    if request.method == 'POST':
        try:
            # Update user details
            user.username = request.form['username']
            user.email = request.form['email']
            user.full_name = request.form['full_name']
            
            # Handle role assignment
            role_id = request.form.get('role_id')
            user.role_id = int(role_id) if role_id and role_id != '' else None
            
            # Handle admin status
            user.is_admin = 'is_admin' in request.form
            
            # Handle site assignments - get list of site IDs from form
            site_ids = request.form.getlist('site_ids')
            
            # Clear current site assignments and add new ones
            user.sites = []
            if site_ids:
                for site_id in site_ids:
                    site = Site.query.get(int(site_id))
                    if site:
                        user.sites.append(site)
            
            # Handle password reset if requested
            if 'reset_password' in request.form:
                import secrets
                import string
                
                # Generate a secure random password
                alphabet = string.ascii_letters + string.digits
                password = ''.join(secrets.choice(alphabet) for _ in range(12))
                
                user.set_password(password)
                password_message = f" Password has been reset to '{password}'."
            else:
                password_message = ""
            
            db.session.commit()
            flash(f'User {user.username} has been updated.{password_message}', 'success')
            return redirect(url_for('manage_users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'error')
    
    return render_template(
        'edit_user.html',
        user=user,
        roles=roles,
        sites=sites
    )

# Role Management Routes
@app.route('/admin/roles/delete/<int:role_id>', methods=['POST'])
@login_required
def delete_role(role_id):
    """Delete a role if it has no users assigned"""
    # Ensure user has admin privileges
    if not current_user.is_admin:
        flash('You do not have permission to delete roles.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        role = Role.query.get_or_404(role_id)
        
        # Check if any users have this role
        if role.users and len(role.users) > 0:
            flash(f'Cannot delete role "{role.name}" because it is assigned to {len(role.users)} users.', 'error')
            return redirect(url_for('manage_roles'))
        
        role_name = role.name
        db.session.delete(role)
        db.session.commit()
        
        flash(f'Role "{role_name}" has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting role: {str(e)}', 'error')
    
    return redirect(url_for('manage_roles'))

@app.route('/admin/roles/add', methods=['POST'])
@login_required
def add_role():
    """Add a new role"""
    # Ensure user has admin privileges
    if not current_user.is_admin:
        flash('You do not have permission to add roles.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Get form data
        name = request.form['name']
        description = request.form.get('description', '')
        
        # Get selected permissions
        permissions = request.form.getlist('permissions')
        permissions_str = ','.join(permissions) if permissions else ''
        
        # Create new role
        new_role = Role(
            name=name,
            description=description,
            permissions=permissions_str
        )
        
        # Add role to database
        db.session.add(new_role)
        db.session.commit()
        
        flash(f'Role "{name}" created successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding role: {str(e)}', 'error')
    
    return redirect(url_for('manage_roles'))

@app.route('/admin/roles/edit/<int:role_id>', methods=['GET', 'POST'])
@login_required
def edit_role(role_id):
    """Edit an existing role"""
    # Ensure user has admin privileges
    if not current_user.is_admin:
        flash('You do not have permission to edit roles.', 'error')
        return redirect(url_for('dashboard'))
    
    role = Role.query.get_or_404(role_id)
    
    if request.method == 'POST':
        try:
            # Update role details
            role.name = request.form['name']
            role.description = request.form.get('description', '')
            
            # Update permissions
            permissions = request.form.getlist('permissions')
            role.permissions = ','.join(permissions) if permissions else ''
            
            db.session.commit()
            flash(f'Role "{role.name}" has been updated.', 'success')
            return redirect(url_for('manage_roles'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating role: {str(e)}', 'error')
    
    # For GET request, render the edit form
    role_permissions = role.permissions.split(',') if role.permissions else []
    all_permissions = get_all_permissions()
    
    return render_template(
        'edit_role.html',
        role=role,
        role_permissions=role_permissions,
        all_permissions=all_permissions
    )

# Add helper function to get all available permissions
def get_all_permissions():
    """Return a dictionary of all available permissions"""
    # Sample permissions - replace with your actual permissions system
    return {
        "view_sites": "View Sites",
        "edit_sites": "Edit Sites", 
        "delete_sites": "Delete Sites",
        "view_machines": "View Machines",
        "edit_machines": "Edit Machines",
        "delete_machines": "Delete Machines",
        "view_parts": "View Parts",
        "edit_parts": "Edit Parts",
        "delete_parts": "Delete Parts",
        "view_reports": "View Reports",
        "admin.users": "Manage Users",
        "admin.roles": "Manage Roles",
        "admin.backups": "Manage Backups"
    }

# Add routes for backup management if they don't exist
@app.route('/admin/backups/create', methods=['POST'])
@login_required
def create_backup():
    """Create a new database backup"""
    # Ensure user has admin privileges
    if not current_user.is_admin:
        flash('You do not have permission to create backups.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        from backup_utils import create_backup as create_db_backup
        success, message = create_db_backup()
        
        if success:
            flash(f'Backup created successfully: {message}', 'success')
        else:
            flash(f'Backup failed: {message}', 'error')
    except Exception as e:
        flash(f'Error creating backup: {str(e)}', 'error')
    
    return redirect(url_for('manage_backups'))

@app.route('/admin/backups/delete/<filename>', methods=['POST'])
@login_required
def delete_backup(filename):
    """Delete a database backup file"""
    # Ensure user has admin privileges
    if not current_user.is_admin:
        flash('You do not have permission to delete backups.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        from backup_utils import get_backup_dir
        import os
        
        backup_path = os.path.join(get_backup_dir(), filename)
        if os.path.exists(backup_path):
            os.remove(backup_path)
            # Also remove info file if it exists
            info_path = f"{backup_path}.info"
            if os.path.exists(info_path):
                os.remove(info_path)
            flash(f'Backup "{filename}" has been deleted.', 'success')
        else:
            flash(f'Backup file not found.', 'error')
    except Exception as e:
        flash(f'Error deleting backup: {str(e)}', 'error')
    
    return redirect(url_for('manage_backups'))

@app.route('/admin/backups/restore/<filename>', methods=['POST'])
@login_required
def restore_backup(filename):
    """Restore database from a backup file"""
    # Ensure user has admin privileges
    if not current_user.is_admin:
        flash('You do not have permission to restore backups.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        from backup_utils import restore_backup as restore_db_backup
        success, message = restore_db_backup(filename)
        
        if success:
            flash(f'Database restored successfully: {message}', 'success')
        else:
            flash(f'Restore failed: {message}', 'error')
    except Exception as e:
        flash(f'Error restoring backup: {str(e)}', 'error')
    
    return redirect(url_for('manage_backups'))

@app.route('/admin/users/add', methods=['POST'])
@login_required
def add_user():
    """Add a new user"""
    if not current_user.is_admin:
        flash('You do not have permission to add users.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Get form data
        username = request.form['username']
        email = request.form['email']
        full_name = request.form.get('full_name', '')
        role_id = request.form.get('role_id')
        is_admin = 'is_admin' in request.form
        site_ids = request.form.getlist('site_ids')
        
        # Generate a random password
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for i in range(12))
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            is_admin=is_admin,
            role_id=int(role_id) if role_id and role_id != '' else None
        )
        new_user.set_password(password)
        
        # Add user to database
        db.session.add(new_user)
        db.session.commit()
        
        # Assign sites if any were selected
        if site_ids:
            for site_id in site_ids:
                site = Site.query.get(int(site_id))
                if site:
                    new_user.sites.append(site)
            db.session.commit()
        
        flash(f'User {username} created successfully with password: {password}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding user: {str(e)}', 'error')
    
    return redirect(url_for('manage_users'))

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete a user"""
    if not current_user.is_admin:
        flash('You do not have permission to delete users.', 'error')
        return redirect(url_for('dashboard'))
    
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('manage_users'))
    
    try:
        user = User.query.get_or_404(user_id)
        username = user.username
        
        # Remove user from any sites
        user.sites = []
        
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        
        flash(f'User "{username}" has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('manage_users'))

# Make sure we can run the app directly for both development and production
if __name__ == '__main__':
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Add default admin account if no users exist
        add_default_admin_if_needed()
    
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 10000))
    print(f"[APP] Starting Flask server on port {port}")
    
    # Use host 0.0.0.0 to bind to all interfaces
    app.run(host='0.0.0.0', port=port)