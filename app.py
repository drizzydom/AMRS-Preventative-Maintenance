from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
import logging

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

# Define database models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    sites = Site.query.all()
    machines = Machine.query.all()
    # Pass current date to template for maintenance calculations
    now = datetime.utcnow()
    return render_template('dashboard.html', 
                          sites=sites, 
                          machines=machines,
                          now=now,
                          is_admin=current_user.is_admin)

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
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    part = Part.query.get_or_404(part_id)
    part.last_maintenance = datetime.utcnow()
    part.update_next_maintenance()
    db.session.commit()
    flash(f'Maintenance for "{part.name}" has been updated')
    return redirect(url_for('manage_parts'))

# Setup database initialization
@app.cli.command("init-db")
def init_db():
    """Initialize the database with sample data."""
    db.create_all()
    
    # Check if admin user exists, create if not
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', is_admin=True)
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
            # Machine 1 parts
            Part(name='Spindle', description='Main cutting spindle', machine_id=machine1.id, 
                 maintenance_frequency=3, last_maintenance=datetime.utcnow()),
            Part(name='Coolant System', description='Cutting fluid circulation', machine_id=machine1.id,
                 maintenance_frequency=6, last_maintenance=datetime.utcnow()),
            Part(name='Tool Changer', description='Automatic tool changer', machine_id=machine1.id,
                 maintenance_frequency=2, last_maintenance=datetime.utcnow()),
                 
            # Machine 2 parts
            Part(name='Chuck', description='Workholding device', machine_id=machine2.id,
                 maintenance_frequency=4, last_maintenance=datetime.utcnow()),
            Part(name='Tailstock', description='Supports workpiece end', machine_id=machine2.id,
                 maintenance_frequency=5, last_maintenance=datetime.utcnow()),
            
            # Machine 3 parts
            Part(name='Drill Bit', description='Cutting tool', machine_id=machine3.id,
                 maintenance_frequency=1, last_maintenance=datetime.utcnow()),
            Part(name='Table', description='Work surface', machine_id=machine3.id,
                 maintenance_frequency=4, last_maintenance=datetime.utcnow()),
                 
            # Machine 4 parts
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

# Replace @app.before_first_request with this
with app.app_context():
    try:
        db.create_all()
        # Check if we need to initialize sample data
        if User.query.filter_by(username='admin').first() is None:
            admin = User(username='admin', is_admin=True)
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
                # Machine 1 parts
                Part(name='Spindle', description='Main cutting spindle', machine_id=machine1.id, 
                    maintenance_frequency=3, last_maintenance=datetime.utcnow()),
                Part(name='Coolant System', description='Cutting fluid circulation', machine_id=machine1.id,
                    maintenance_frequency=6, last_maintenance=datetime.utcnow()),
                Part(name='Tool Changer', description='Automatic tool changer', machine_id=machine1.id,
                    maintenance_frequency=2, last_maintenance=datetime.utcnow()),
                    
                # Machine 2 parts
                Part(name='Chuck', description='Workholding device', machine_id=machine2.id,
                    maintenance_frequency=4, last_maintenance=datetime.utcnow()),
                Part(name='Tailstock', description='Supports workpiece end', machine_id=machine2.id,
                    maintenance_frequency=5, last_maintenance=datetime.utcnow()),
                
                # Machine 3 parts
                Part(name='Drill Bit', description='Cutting tool', machine_id=machine3.id,
                    maintenance_frequency=1, last_maintenance=datetime.utcnow()),
                Part(name='Table', description='Work surface', machine_id=machine3.id,
                    maintenance_frequency=4, last_maintenance=datetime.utcnow()),
                    
                # Machine 4 parts
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
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
