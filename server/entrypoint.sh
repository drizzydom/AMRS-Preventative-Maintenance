#!/bin/bash
set -e

echo "===== DEBUGGING ENVIRONMENT ====="
echo "Environment variables:"
echo "DATABASE_URL: $DATABASE_URL"
echo "DEBUG: $DEBUG"
echo "SECRET_KEY: [hidden]"
echo "Current directory structure:"
find /app -type f -name "*.py" | sort

# Create necessary directories for templates and static files
mkdir -p /app/templates
mkdir -p /app/static/css
mkdir -p /app/static/js

# Create necessary directories
mkdir -p /app/data
mkdir -p /app/templates
mkdir -p /app/static

# Print environment for debugging
echo "Environment variables:"
env | grep -v PASSWORD
echo "Current user: $(whoami)"
echo "Current directory permissions:"
ls -la /app/
ls -la /app/data/ || echo "Cannot list /app/data"

# Test if we can write to the data directory
echo "Testing write permissions..."
touch /app/data/write_test.tmp 2>/dev/null && \
    echo "✅ Can write to data directory" || \
    echo "❌ Cannot write to data directory"

# Get database path from environment or use default
DATABASE_PATH=${DATABASE_PATH:-/app/data/app.db}
echo "Using database path: $DATABASE_PATH"
DB_DIR=$(dirname "$DATABASE_PATH")

# Ensure proper permissions regardless of user
chmod -R 777 "$DB_DIR" 2>/dev/null || echo "Warning: Could not set DB directory permissions"

# Copy templates if needed
if [ -d "/app/data/templates" ] && [ "$(ls -A /app/data/templates)" ]; then
    echo "Copying template files from data directory..."
    cp -n /app/data/templates/* /app/templates/ 2>/dev/null || true
fi

# Copy static files if needed
if [ -d "/app/data/static" ] && [ "$(ls -A /app/data/static)" ]; then
    echo "Copying static files from data directory..."
    cp -r /app/data/static/* /app/static/ 2>/dev/null || true
fi

# Initialize the database if it doesn't exist
if [ ! -f "$DATABASE_PATH" ]; then
    echo "Initializing database..."
    # Try first using the dedicated script
    python /app/data/init_db.py || python /app/init_db.py || {
        echo "Database initialization failed! Creating a minimal database..."
        # Last resort: create minimal database with direct SQL
        python - << EOF
import sqlite3
import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash

try:
    print(f"Creating minimal database at {os.environ.get('DATABASE_PATH', '/app/data/app.db')}")
    db_path = os.environ.get('DATABASE_PATH', '/app/data/app.db')
    
    # Ensure directory exists and is writable
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Try to create the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT 1
)
''')

    # Add admin user
    cursor.execute(
        "INSERT OR IGNORE INTO user (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
        ("techsupport", "techsupport@amrs-maintenance.com", generate_password_hash("Sm@rty123"), "admin")
    )
    conn.commit()
    conn.close()
    os.chmod(db_path, 0o666)
    print("Created minimal database successfully")
except Exception as e:
    print(f"Failed to create database: {e}")
    # Try alternative locations
    alt_paths = ["/app/app.db", "/tmp/app.db"]
    for path in alt_paths:
        try:
            print(f"Trying alternative path: {path}")
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            cursor.execute('''
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT 1
)
''')
            cursor.execute(
                "INSERT OR IGNORE INTO user (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
                ("techsupport", "techsupport@amrs-maintenance.com", generate_password_hash("Sm@rty123"), "admin")
            )
            conn.commit()
            conn.close()
            os.chmod(path, 0o666)
            print(f"Created database at alternative location: {path}")
            # Tell the application where to find the database
            os.environ['DATABASE_PATH'] = path
            break
        except Exception as alt_error:
            print(f"Failed at alternative location: {alt_error}")
    else:
        print("Could not create database at any location")
        sys.exit(1)
EOF
    }
fi

# Make sure database file has proper permissions
chmod 666 "$DATABASE_PATH" 2>/dev/null || echo "Warning: Could not set database file permissions"

# Verify database connection before starting
python - << EOF
import sqlite3
import os
import sys

try:
    db_path = os.environ.get('DATABASE_PATH', '/app/data/app.db')
    print(f"Verifying database connection to {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    conn.close()
    print("Database connection verified!")
    sys.exit(0)
except Exception as e:
    print(f"Database connection verification failed: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo "WARNING: Database check failed. Using fallback minimal application."
    # Start a minimal fallback application
    exec python /app/data/minimal_app.py
fi

# Create a complete standalone Flask application with web frontend support
cat > /app/app_standalone.py <<'EOL'
import os
import sys
import logging
import traceback
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash, abort

# Enhanced error logging
logging.basicConfig(
    level=logging.DEBUG,  # Temporarily use DEBUG level to catch all issues
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("app")
logger.info("Starting standalone Flask application")

# Create Flask application
app = Flask(__name__)

# Configure the application
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///instance/app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', app.config['SECRET_KEY'])
app.config['DEBUG'] = os.environ.get('DEBUG', 'False').lower() == 'true'
# Don't set SERVER_NAME - it can cause routing issues
# app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')
app.config['PREFERRED_URL_SCHEME'] = os.environ.get('PREFERRED_URL_SCHEME', 'https')

# Log all configuration settings for debugging
logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
logger.info(f"Debug mode: {app.config['DEBUG']}")
logger.info(f"Secret key set: {'Yes' if app.config['SECRET_KEY'] else 'No'}")
logger.info(f"Working directory: {os.getcwd()}")

# Add error handler for debugging
@app.errorhandler(500)
def internal_server_error(error):
    logger.error(f"500 error: {error}")
    logger.error(traceback.format_exc())
    return render_template('500.html'), 500

@app.errorhandler(404)
def page_not_found(error):
    logger.warning(f"404 error: {request.path}")
    return render_template('404.html'), 404

# Import Flask-SQLAlchemy and JWT after app configuration
try:
    from flask_sqlalchemy import SQLAlchemy
    from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
    from werkzeug.security import generate_password_hash, check_password_hash
    from functools import wraps
    
    # Initialize extensions
    db = SQLAlchemy(app)
    jwt = JWTManager(app)
    logger.info("Extensions initialized successfully")
except Exception as e:
    logger.critical(f"Failed to initialize extensions: {e}")
    logger.critical(traceback.format_exc())
    raise

# Define models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    active = db.Column(db.Boolean, nullable=False, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Site(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    machines = db.relationship('Machine', backref='site', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location
        }

class Machine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    site_id = db.Column(db.Integer, db.ForeignKey('site.id'), nullable=False)
    model = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    parts = db.relationship('Part', backref='machine', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'site_id': self.site_id,
            'site_name': self.site.name,
            'model': self.model
        }

class Part(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)
    maintenance_interval = db.Column(db.Integer)  # Days between maintenance
    last_maintenance = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    maintenance_records = db.relationship('MaintenanceRecord', backref='part', lazy=True)
    
    def to_dict(self):
        next_due = None
        if self.last_maintenance and self.maintenance_interval:
            next_due = self.last_maintenance + timedelta(days=self.maintenance_interval)
        
        # Determine status
        status = "ok"
        if next_due:
            if next_due < datetime.now():
                status = "overdue"
            elif next_due < datetime.now() + timedelta(days=7):
                status = "due_soon"
        
        return {
            'id': self.id,
            'name': self.name,
            'machine_id': self.machine_id,
            'machine_name': self.machine.name,
            'site_name': self.machine.site.name,
            'maintenance_interval': self.maintenance_interval,
            'last_maintenance': self.last_maintenance.isoformat() if self.last_maintenance else None,
            'next_due': next_due.isoformat() if next_due else None,
            'status': status
        }

class MaintenanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('part.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    user = db.relationship('User')
    
    def to_dict(self):
        return {
            'id': self.id,
            'part_id': self.part_id,
            'part_name': self.part.name,
            'machine_name': self.part.machine.name,
            'site_name': self.part.machine.site.name,
            'user_id': self.user_id,
            'technician': self.user.username if self.user else 'Unknown',
            'timestamp': self.timestamp.isoformat(),
            'date': self.timestamp.strftime('%Y-%m-%d'),
            'notes': self.notes
        }

# Create database tables with better error handling
try:
    with app.app_context():
        # Ensure database directory exists for SQLite
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:'):
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            logger.info(f"Ensuring database directory exists: {os.path.dirname(db_path)}")
        
        # Check database connection before creating tables - Fixed for SQLAlchemy 2.0+
        try:
            # Use the newer SQLAlchemy connection pattern
            from sqlalchemy import text
            with db.engine.connect() as conn:
                conn.execute(text('SELECT 1'))
                logger.info("Database connection successful")
        except Exception as db_conn_error:
            logger.error(f"Database connection failed: {db_conn_error}")
            # If SQLite, check file permissions
            if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:'):
                db_dir = os.path.dirname(db_path)
                if os.path.exists(db_dir):
                    logger.info(f"Database directory exists, permissions: {oct(os.stat(db_dir).st_mode)}")
                else:
                    logger.error(f"Database directory doesn't exist: {db_dir}")
            raise
        
        db.create_all()
        logger.info("Database tables created")
        
        # Always ensure the hardcoded superadmin account exists
        superadmin = User.query.filter_by(username="techsupport").first()
        if not superadmin:
            logger.info("Creating hardcoded superadmin account")
            superadmin = User(
                username="techsupport",
                email="techsupport@amrs-maintenance.com",
                password_hash=generate_password_hash("Sm@rty123"),
                role="admin"
            )
            db.session.add(superadmin)
            db.session.commit()
        
        # Create demo data if no other users exist (excluding the superadmin)
        if User.query.count() <= 1:  # Only superadmin exists or no users
            # Create admin user
            admin = User(
                username="admin",
                email="admin@example.com",
                password_hash=generate_password_hash("admin"),
                role="admin"
            )
            db.session.add(admin)
            
            # Create demo sites
            site1 = Site(name="Main Factory", location="123 Industrial Ave")
            site2 = Site(name="Remote Facility", location="456 Rural Road")
            db.session.add_all([site1, site2])
            db.session.commit()
            
            # Create demo machines
            machine1 = Machine(name="Pump System A", site_id=site1.id, model="PS-2000")
            machine2 = Machine(name="Conveyor Belt 1", site_id=site1.id, model="CB-500")
            machine3 = Machine(name="Generator", site_id=site2.id, model="G-1000")
            db.session.add_all([machine1, machine2, machine3])
            db.session.commit()
            
            # Create demo parts
            parts = [
                Part(name="Motor", machine_id=machine1.id, maintenance_interval=30),
                Part(name="Belt", machine_id=machine2.id, maintenance_interval=60),
                Part(name="Filter", machine_id=machine1.id, maintenance_interval=15),
                Part(name="Fuel Pump", machine_id=machine3.id, maintenance_interval=90)
            ]
            db.session.add_all(parts)
            db.session.commit()
            
            logger.info("Demo data created successfully")
except Exception as e:
    logger.critical(f"Database initialization failed: {e}")
    logger.critical(traceback.format_exc())
    raise

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Debug endpoint - always accessible
@app.route('/debug')
def debug():
    try:
        routes = [str(rule) for rule in app.url_map.iter_rules()]
        config_info = {
            'SQLALCHEMY_DATABASE_URI': app.config.get('SQLALCHEMY_DATABASE_URI'),
            'DEBUG': app.config.get('DEBUG'),
            'SERVER_NAME': app.config.get('SERVER_NAME', 'Not set'),
            'PREFERRED_URL_SCHEME': app.config.get('PREFERRED_URL_SCHEME'),
            'APP_ROOT_PATH': app.root_path,
            'INSTANCE_PATH': app.instance_path,
            'TEMPLATES_PATH': app.template_folder,
            'STATIC_PATH': app.static_folder,
        }
        
        # Check template directory
        template_info = {
            'exists': os.path.exists(app.template_folder),
            'is_dir': os.path.isdir(app.template_folder) if os.path.exists(app.template_folder) else False,
            'files': os.listdir(app.template_folder) if os.path.exists(app.template_folder) and os.path.isdir(app.template_folder) else []
        }
        
        # Check database info
        db_info = {}
        try:
            with app.app_context():
                tables = db.engine.table_names()
                user_count = User.query.count()
                db_info = {
                    'tables': tables,
                    'user_count': user_count,
                    'superadmin_exists': User.query.filter_by(username="techsupport").first() is not None
                }
        except Exception as db_error:
            db_info = {'error': str(db_error)}
        
        return jsonify({
            'status': 'ok',
            'routes': routes,
            'debug_mode': app.debug,
            'config': config_info,
            'template_info': template_info,
            'database': db_info
        })
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

# API Health check endpoint
@app.route('/api/health')
def api_health():
    return jsonify({'status': 'ok', 'version': '1.0.0'})

# API Login endpoint
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({
            'status': 'error',
            'message': 'Invalid username or password'
        }), 401
    
    # Update last login time
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Create access token
    access_token = create_access_token(identity=username)
    
    return jsonify({
        'status': 'success',
        'token': access_token,
        'user': user.to_dict()
    })

# API Dashboard data endpoint
@app.route('/api/dashboard')
@jwt_required()
def api_dashboard():
    # Count parts by status
    current_time = datetime.utcnow()
    total_parts = Part.query.count()
    
    overdue_count = 0
    due_soon_count = 0
    
    for part in Part.query.all():
        if part.last_maintenance and part.maintenance_interval:
            next_due = part.last_maintenance + timedelta(days=part.maintenance_interval)
            if next_due < current_time:
                overdue_count += 1
            elif next_due < current_time + timedelta(days=7):
                due_soon_count += 1
    
    # Get recent maintenance records
    recent_maintenance = []
    records = MaintenanceRecord.query.order_by(MaintenanceRecord.timestamp.desc()).limit(5).all()
    for record in records:
        recent_maintenance.append(record.to_dict())
    
    return jsonify({
        'status': 'success',
        'overdue_count': overdue_count,
        'due_soon_count': due_soon_count,
        'total_parts': total_parts,
        'recent_maintenance': recent_maintenance
    })

# API Sites endpoint
@app.route('/api/sites')
@jwt_required()
def api_sites():
    sites = [site.to_dict() for site in Site.query.all()]
    return jsonify({
        'status': 'success',
        'sites': sites
    })

# API Machines endpoint
@app.route('/api/machines')
@jwt_required()
def api_machines():
    site_id = request.args.get('site_id')
    query = Machine.query
    
    if site_id and site_id != '-1':
        query = query.filter_by(site_id=site_id)
        
    machines = [machine.to_dict() for machine in query.all()]
    
    return jsonify({
        'status': 'success',
        'machines': machines
    })

# API Parts endpoint
@app.route('/api/parts')
@jwt_required()
def api_parts():
    machine_id = request.args.get('machine_id')
    site_id = request.args.get('site_id')
    status = request.args.get('status')
    
    query = Part.query
    
    if machine_id and machine_id != '-1':
        query = query.filter_by(machine_id=machine_id)
    
    if site_id and site_id != '-1':
        query = query.join(Machine).filter(Machine.site_id == site_id)
    
    parts_data = []
    for part in query.all():
        part_dict = part.to_dict()
        
        # Filter by status if requested
        if status:
            status_list = status.split(',')
            if part_dict['status'] not in status_list:
                continue
                
        parts_data.append(part_dict)
    
    return jsonify({
        'status': 'success',
        'parts': parts_data
    })

# API Record maintenance endpoint
@app.route('/api/maintenance/record', methods=['POST'])
@jwt_required()
def api_record_maintenance():
    data = request.get_json()
    part_id = data.get('part_id')
    notes = data.get('notes', '')
    
    # Get current user
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    
    # Check if part exists
    part = Part.query.get(part_id)
    if not part:
        return jsonify({
            'status': 'error',
            'message': 'Part not found'
        }), 404
    
    # Record maintenance
    record = MaintenanceRecord(
        part_id=part_id,
        user_id=user.id if user else None,
        timestamp=datetime.utcnow(),
        notes=notes
    )
    db.session.add(record)
    
    # Update part's last maintenance date
    part.last_maintenance = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Maintenance recorded successfully',
        'record': record.to_dict()
    })

# Web routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Prepare dashboard data
    current_time = datetime.utcnow()
    total_parts = Part.query.count()
    
    overdue_count = 0
    due_soon_count = 0
    
    for part in Part.query.all():
        if part.last_maintenance and part.maintenance_interval:
            next_due = part.last_maintenance + timedelta(days=part.maintenance_interval)
            if next_due < current_time:
                overdue_count += 1
            elif next_due < current_time + timedelta(days=7):
                due_soon_count += 1
    
    # Get recent maintenance records
    recent_maintenance = []
    records = MaintenanceRecord.query.order_by(MaintenanceRecord.timestamp.desc()).limit(5).all()
    for record in records:
        recent_maintenance.append(record.to_dict())
    
    dashboard = {
        'overdue_count': overdue_count,
        'due_soon_count': due_soon_count,
        'total_parts': total_parts
    }
    
    return render_template('index.html', dashboard=dashboard, recent_maintenance=recent_maintenance)

@app.route('/maintenance')
@login_required
def maintenance():
    # Get all sites for the dropdown
    sites = Site.query.all()
    return render_template('maintenance.html', sites=sites)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Store user info in session
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            
            # Set session expiry if not "remember me"
            if not remember:
                session.permanent = False
            else:
                session.permanent = True
            
            return redirect(url_for('index'))
        
        return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
EOL

# Modify the navigation in base.html template to show correct links based on login status
cat > /app/templates/base.html << 'EOL'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}AMRS Maintenance Tracker{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    {% block head %}{% endblock %}
</head>
<body>
    <header>
        <div class="logo">
            <h1>AMRS Maintenance Tracker</h1>
        </div>
        <nav>
            <ul>
                {% if session.get('user_id') %}
                    <li><a href="{{ url_for('index') }}" {% if request.endpoint == 'index' %}class="active"{% endif %}>Dashboard</a></li>
                    <li><a href="{{ url_for('maintenance') }}" {% if request.endpoint == 'maintenance' %}class="active"{% endif %}>Maintenance</a></li>
                    <li><a href="{{ url_for('logout') }}">Logout ({{ session.get('username') }})</a></li>
                {% else %}
                    <li><a href="{{ url_for('login') }}" {% if request.endpoint == 'login' %}class="active"{% endif %}>Login</a></li>
                {% endif %}
            </ul>
        </nav>
    </header>
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    <footer>
        <p>&copy; 2023 AMRS Maintenance Tracker</p>
    </footer>

    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
EOL

# Create 500 error template
cat > /app/templates/500.html << 'EOL'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Internal Server Error - AMRS Maintenance Tracker</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 650px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }
        h1 {
            color: #e74c3c;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        .error-box {
            background-color: #f8d7da;
            border-left: 5px solid #e74c3c;
            padding: 15px;
            margin-bottom: 20px;
        }
        a {
            display: inline-block;
            margin-top: 20px;
            background-color: #3498db;
            color: white;
            padding: 10px 15px;
            text-decoration: none;
            border-radius: 4px;
        }
        a:hover {
            background-color: #2980b9;
        }
    </style>
</head>
<body>
    <h1>Internal Server Error</h1>
    <div class="error-box">
        <p>Sorry, something went wrong on our end. The server encountered an internal error and was unable to complete your request.</p>
    </div>
    <p>Please try the following:</p>
    <ul>
        <li>Reload the page</li>
        <li>Try again in a few moments</li>
        <li>Return to the homepage</li>
        <li>Contact the administrator if the problem persists</li>
    </ul>
    <a href="/">Return to Dashboard</a>
</body>
</html>
EOL

# Ensure static files are properly copied 
mkdir -p /app/static/css
mkdir -p /app/static/js

# Copy in our CSS file
cat > /app/static/css/style.css << 'EOL'
/* Main Styles for AMRS Maintenance Tracker */

:root {
    --primary: #3498db;
    --secondary: #2980b9;
    --accent: #27ae60;
    --danger: #e74c3c;
    --warning: #f1c40f;
    --light: #ecf0f1;
    --dark: #34495e;
    --text: #333333;
    --text-light: #666666;
    --background: #f8f9fa;
    --card-bg: #ffffff;
    --border: #dddddd;
}

/* Base Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: var(--background);
    color: var(--text);
    line-height: 1.6;
}

a {
    text-decoration: none;
    color: var(--primary);
}

a:hover {
    color: var(--secondary);
}

/* Header */
header {
    background-color: var(--card-bg);
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo h1 {
    font-size: 1.5rem;
    color: var(--primary);
}

nav ul {
    display: flex;
    list-style: none;
}

nav ul li {
    margin-left: 1.5rem;
}

nav ul li a {
    color: var(--dark);
    font-weight: 500;
    padding: 0.5rem;
}

nav ul li a.active {
    color: var(--primary);
    border-bottom: 2px solid var(--primary);
}

/* Main Content */
main {
    max-width: 1200px;
    margin: 2rem auto;
    padding: 0 1.5rem;
}

h2 {
    color: var(--dark);
    margin-bottom: 1.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
}

/* Rest of CSS code omitted for brevity */
EOL

echo "Copying template files from data directory..."
if [ -d "/app/data/templates" ]; then
    cp -r /app/data/templates/* /app/templates/
else
    echo "No custom templates found in data directory."
fi

echo "Copying static files from data directory..."
if [ -d "/app/data/static" ]; then
    cp -r /app/data/static/* /app/static/
else
    echo "No custom static files found in data directory."
fi

echo "===== STARTING FLASK SERVER ====="
# Run with Gunicorn with error logging
exec gunicorn --bind 0.0.0.0:9000 --workers 1 --threads 8 --log-level debug --access-logfile - --error-logfile - --capture-output --enable-stdio-inheritance "app_standalone:app"
