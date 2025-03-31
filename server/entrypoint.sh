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

# Create a complete standalone Flask application with web frontend support
cat > /app/app_standalone.py <<'EOL'
import os
import sys
import logging
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
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
app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')  # For URL generation
app.config['PREFERRED_URL_SCHEME'] = os.environ.get('PREFERRED_URL_SCHEME', 'https')

# Log configuration details
logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
logger.info(f"Debug mode: {app.config['DEBUG']}")
logger.info(f"Server name: {app.config['SERVER_NAME']}")

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

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

# Create database tables
with app.app_context():
    # Ensure database directory exists for SQLite
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:'):
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    db.create_all()
    logger.info("Database tables created")
    
    # Create demo data if no users exist
    if User.query.first() is None:
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
            Part(name="Hydraulic Pump", machine_id=machine1.id, maintenance_interval=30),
            Part(name="Filter Assembly", machine_id=machine1.id, maintenance_interval=15),
            Part(name="Drive Belt", machine_id=machine2.id, maintenance_interval=60),
            Part(name="Roller Bearings", machine_id=machine2.id, maintenance_interval=90),
            Part(name="Fuel Filter", machine_id=machine3.id, maintenance_interval=45),
            Part(name="Air Filter", machine_id=machine3.id, maintenance_interval=30),
            Part(name="Oil Filter", machine_id=machine3.id, maintenance_interval=15)
        ]
        db.session.add_all(parts)
        db.session.commit()
        
        # Create some maintenance records
        now = datetime.utcnow()
        records = [
            MaintenanceRecord(part_id=1, user_id=1, timestamp=now - timedelta(days=10), notes="Replaced hydraulic fluid"),
            MaintenanceRecord(part_id=2, user_id=1, timestamp=now - timedelta(days=5), notes="Cleaned filter"),
            MaintenanceRecord(part_id=5, user_id=1, timestamp=now - timedelta(days=30), notes="Replaced filter"),
            MaintenanceRecord(part_id=6, user_id=1, timestamp=now - timedelta(days=20), notes="Cleaned and inspected")
        ]
        db.session.add_all(records)
        
        # Update last_maintenance dates based on records
        for record in records:
            part = Part.query.get(record.part_id)
            if part and (part.last_maintenance is None or part.last_maintenance < record.timestamp):
                part.last_maintenance = record.timestamp
        
        db.session.commit()
        logger.info("Created demo data")

# Authentication utilities
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to be logged in to view this page.')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Define helper functions
def get_dashboard_data():
    now = datetime.utcnow()
    
    # Count overdue parts
    overdue_count = Part.query.filter(
        Part.last_maintenance != None,
        Part.maintenance_interval != None,
        now > Part.last_maintenance + timedelta(days=Part.maintenance_interval)
    ).count()
    
    # Count parts due soon (within next 7 days)
    due_soon_count = Part.query.filter(
        Part.last_maintenance != None,
        Part.maintenance_interval != None,
        now <= Part.last_maintenance + timedelta(days=Part.maintenance_interval),
        now >= Part.last_maintenance + timedelta(days=Part.maintenance_interval - 7)
    ).count()
    
    # Count total parts
    total_parts = Part.query.count()
    
    # Get recent maintenance
    recent_maintenance = MaintenanceRecord.query.order_by(
        MaintenanceRecord.timestamp.desc()
    ).limit(10).all()
    
    return {
        'overdue_count': overdue_count,
        'due_soon_count': due_soon_count,
        'total_parts': total_parts,
        'recent_maintenance': [record.to_dict() for record in recent_maintenance]
    }

# API Routes
@app.route('/api/health')
def api_health_check():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password_hash, password):
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        token = create_access_token(identity=username)
        return jsonify({
            'token': token,
            'user': user.to_dict()
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/dashboard')
@jwt_required()
def api_dashboard():
    return jsonify(get_dashboard_data())

@app.route('/api/sites')
@jwt_required()
def api_sites():
    sites = Site.query.all()
    return jsonify({
        'sites': [site.to_dict() for site in sites]
    })

@app.route('/api/machines')
@jwt_required()
def api_machines():
    site_id = request.args.get('site_id', None)
    query = Machine.query
    
    if site_id and site_id != '-1':
        query = query.filter_by(site_id=site_id)
    
    machines = query.all()
    return jsonify({
        'machines': [machine.to_dict() for machine in machines]
    })

@app.route('/api/parts')
@jwt_required()
def api_parts():
    site_id = request.args.get('site_id')
    machine_id = request.args.get('machine_id')
    status_filter = request.args.get('status')
    
    # Start with all parts
    query = Part.query.join(Machine).join(Site)
    
    # Apply filters
    if site_id and site_id != '-1':
        query = query.filter(Site.id == site_id)
    if machine_id and machine_id != '-1':
        query = query.filter(Part.machine_id == machine_id)
    
    parts = query.all()
    
    # Convert to dicts and apply status filtering
    result = []
    for part in parts:
        part_dict = part.to_dict()
        if status_filter:
            statuses = status_filter.split(',')
            if part_dict['status'] in statuses:
                result.append(part_dict)
        else:
            result.append(part_dict)
    
    return jsonify({'parts': result})

@app.route('/api/maintenance/record', methods=['POST'])
@jwt_required()
def api_record_maintenance():
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    part_id = data.get('part_id')
    notes = data.get('notes', '')
    
    # Get current user
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    
    if not part_id:
        return jsonify({'error': 'Part ID is required'}), 400
    
    part = Part.query.get(part_id)
    if not part:
        return jsonify({'error': 'Part not found'}), 404
    
    # Create maintenance record
    record = MaintenanceRecord(
        part_id=part_id,
        user_id=user.id if user else None,
        notes=notes
    )
    db.session.add(record)
    
    # Update part's last maintenance date
    part.last_maintenance = record.timestamp
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Maintenance recorded successfully',
        'record': record.to_dict()
    })

# Web Interface Routes
@app.route('/')
def root():
    # If requesting via browser, show web interface, else return API info
    if 'text/html' in request.headers.get('Accept', ''):
        if 'user_id' in session:
            return redirect(url_for('index'))
        return redirect(url_for('login'))
    
    # API client access
    return jsonify({
        'name': 'AMRS Maintenance API',
        'status': 'ok',
        'version': '1.0.0'
    })

@app.route('/index')
@login_required
def index():
    dashboard = get_dashboard_data()
    recent_maintenance = dashboard['recent_maintenance']
    
    return render_template('index.html', 
                           dashboard=dashboard, 
                           recent_maintenance=recent_maintenance)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False) == 'on'
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Store user in session
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            if remember:
                session.permanent = True
                
            return redirect(url_for('index'))
        else:
            error = 'Invalid username or password'
    
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/maintenance')
@login_required
def maintenance():
    sites = Site.query.all()
    return render_template('maintenance.html', sites=sites)

# Add a context processor to pass current user to all templates
@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return {'current_user': user}

# For handling 404 errors
@app.errorhandler(404)
def page_not_found(e):
    # If JSON request or API endpoint, return JSON error
    if request.path.startswith('/api/') or request.headers.get('Accept') == 'application/json':
        return jsonify({'error': 'Not found'}), 404
    
    # Otherwise render 404 template
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 9000)))
EOL

# Create a simple 404 template
cat > /app/templates/404.html << 'EOF'
{% extends "base.html" %}

{% block title %}Page Not Found - AMRS Maintenance Tracker{% endblock %}

{% block content %}
<div class="error-page">
    <h2>404 - Page Not Found</h2>
    <p>The page you're looking for doesn't exist.</p>
    <p><a href="{{ url_for('index') }}">Return to Dashboard</a></p>
</div>
{% endblock %}
EOF

# Copy templates and static files from data directory if they exist
if [ -d "/app/data/templates" ]; then
    echo "Copying template files from data directory..."
    cp -r /app/data/templates/* /app/templates/
else
    echo "No custom templates found in data directory."
fi

if [ -d "/app/data/static" ]; then
    echo "Copying static files from data directory..."
    cp -r /app/data/static/* /app/static/
else
    echo "No custom static files found in data directory."
fi

echo "===== STARTING FLASK SERVER ====="
# Run with Gunicorn
exec gunicorn --bind 0.0.0.0:9000 --workers 1 --threads 8 --log-level info "app_standalone:app"
