"""
API endpoints for the maintenance tracker application.
These enable the desktop client to interact with the system via HTTP requests.
"""
from flask import jsonify, request, Blueprint, abort
from functools import wraps
import jwt
import datetime
from flask_login import current_user, login_required
import os
from app import app, db
from app import User, Site, Machine, Part, MaintenanceLog

# Create blueprint for API routes
api_bp = Blueprint('api', __name__)

# Secret key for JWT tokens
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', app.config['SECRET_KEY'])

# Token expiration time (in minutes)
TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

def token_required(f):
    """Decorator for routes that require a valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in the headers
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Decode token
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'Invalid user'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

@api_bp.route('/login', methods=['POST'])
def login():
    """API endpoint for user authentication"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing username or password'}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    # Authenticate user
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Generate JWT token
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    }, JWT_SECRET_KEY)
    
    # Return token and user info
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'is_admin': user.is_admin,
            'email': user.email,
            'full_name': user.full_name
        }
    })

@api_bp.route('/dashboard', methods=['GET'])
@token_required
def get_dashboard(current_user):
    """API endpoint to get dashboard data"""
    now = datetime.datetime.utcnow()
    
    # Get all parts
    parts = Part.query.all()
    
    # Count parts by status
    overdue_count = 0
    due_soon_count = 0
    total_parts = len(parts)
    
    for part in parts:
        days_until = (part.next_maintenance - now).days
        if days_until < 0:
            overdue_count += 1
        elif days_until <= 30:  # Using 30 days as default threshold
            due_soon_count += 1
    
    return jsonify({
        'overdue_count': overdue_count,
        'due_soon_count': due_soon_count,
        'total_parts': total_parts
    })

@api_bp.route('/sites', methods=['GET'])
@token_required
def get_sites(current_user):
    """API endpoint to get sites list"""
    # Filter sites based on user permissions
    if current_user.is_admin:
        sites = Site.query.all()
    elif hasattr(current_user, 'sites'):
        sites = current_user.sites
    else:
        sites = []
    
    sites_data = []
    for site in sites:
        sites_data.append({
            'id': site.id,
            'name': site.name,
            'location': site.location
        })
    
    return jsonify(sites_data)

@api_bp.route('/sites/<int:site_id>', methods=['GET'])
@token_required
def get_site(current_user, site_id):
    """API endpoint to get site details"""
    site = db.session.get(Site, site_id)
    if not site:
        abort(404)
    
    # Check if user has access to this site
    if not current_user.is_admin and site not in current_user.sites:
        return jsonify({'error': 'Access denied'}), 403
    
    # Get all machines for this site
    machines = Machine.query.filter_by(site_id=site.id).all()
    machines_data = []
    
    for machine in machines:
        machines_data.append({
            'id': machine.id,
            'name': machine.name,
            'model': machine.model,
            'machine_number': machine.machine_number,
            'serial_number': machine.serial_number
        })
    
    return jsonify({
        'id': site.id,
        'name': site.name,
        'location': site.location,
        'machines': machines_data
    })

@api_bp.route('/machines', methods=['GET'])
@token_required
def get_machines(current_user):
    """API endpoint to get machines list"""
    site_id = request.args.get('site_id', type=int)
    
    # Filter machines by site if provided
    if site_id:
        machines = Machine.query.filter_by(site_id=site_id).all()
    else:
        # Filter based on user permissions
        if current_user.is_admin:
            machines = Machine.query.all()
        else:
            # Get machines from sites user has access to
            site_ids = [site.id for site in current_user.sites]
            machines = Machine.query.filter(Machine.site_id.in_(site_ids)).all()
    
    machines_data = []
    for machine in machines:
        # Get site name
        site = Site.query.get(machine.site_id)
        site_name = site.name if site else 'Unknown Site'
        
        machines_data.append({
            'id': machine.id,
            'name': machine.name,
            'model': machine.model,
            'site_id': machine.site_id,
            'site_name': site_name,
            'machine_number': machine.machine_number,
            'serial_number': machine.serial_number
        })
    
    return jsonify(machines_data)

@api_bp.route('/machines/<int:machine_id>', methods=['GET'])
@token_required
def get_machine(current_user, machine_id):
    """API endpoint to get machine details with parts"""
    machine = db.session.get(Machine, machine_id)
    if not machine:
        abort(404)
    site = Site.query.get(machine.site_id)
    
    # Check if user has access to this machine's site
    if not current_user.is_admin and site not in current_user.sites:
        return jsonify({'error': 'Access denied'}), 403
    
    # Get all parts for this machine
    parts = Part.query.filter_by(machine_id=machine.id).all()
    now = datetime.datetime.utcnow()
    parts_data = []
    
    for part in parts:
        days_until = (part.next_maintenance - now).days
        
        # Determine status
        if days_until < 0:
            status = 'overdue'
        elif days_until <= 30:  # Using 30 days as default threshold
            status = 'due_soon'
        else:
            status = 'ok'
            
        parts_data.append({
            'id': part.id,
            'name': part.name,
            'description': part.description,
            'last_maintenance': part.last_maintenance.isoformat(),
            'next_maintenance': part.next_maintenance.isoformat(),
            'days_until': days_until,
            'status': status,
            'maintenance_frequency': part.maintenance_frequency,
            'maintenance_unit': part.maintenance_unit,
            'last_maintained_by': part.last_maintained_by
        })
    
    return jsonify({
        'id': machine.id,
        'name': machine.name,
        'model': machine.model,
        'site_id': machine.site_id,
        'site_name': site.name if site else 'Unknown Site',
        'machine_number': machine.machine_number,
        'serial_number': machine.serial_number,
        'parts': parts_data
    })

@api_bp.route('/parts', methods=['GET'])
@token_required
def get_parts(current_user):
    """API endpoint to get parts list"""
    machine_id = request.args.get('machine_id', type=int)
    status_filter = request.args.get('status')
    
    # Start with base query
    query = Part.query
    
    # Filter by machine if provided
    if machine_id:
        query = query.filter_by(machine_id=machine_id)
    else:
        # Filter based on user permissions
        if not current_user.is_admin:
            # Get machines from sites user has access to
            site_ids = [site.id for site in current_user.sites]
            machine_ids = [m.id for m in Machine.query.filter(Machine.site_id.in_(site_ids)).all()]
            query = query.filter(Part.machine_id.in_(machine_ids))
    
    parts = query.all()
    now = datetime.datetime.utcnow()
    parts_data = []
    
    for part in parts:
        machine = Machine.query.get(part.machine_id)
        site = Site.query.get(machine.site_id) if machine else None
        
        days_until = (part.next_maintenance - now).days
        
        # Determine status
        if days_until < 0:
            status = 'overdue'
        elif site and days_until <= site.notification_threshold:
            status = 'due_soon'
        else:
            status = 'ok'
        
        # Apply status filter if provided
        if status_filter and status != status_filter:
            continue
            
        parts_data.append({
            'id': part.id,
            'name': part.name,
            'description': part.description,
            'machine_id': part.machine_id,
            'machine_name': machine.name if machine else 'Unknown Machine',
            'site_id': machine.site_id if machine else None,
            'site_name': site.name if site else 'Unknown Site',
            'last_maintenance': part.last_maintenance.isoformat(),
            'next_maintenance': part.next_maintenance.isoformat(),
            'days_until': days_until,
            'status': status,
            'maintenance_frequency': part.maintenance_frequency,
            'last_maintained_by': part.last_maintained_by if hasattr(part, 'last_maintained_by') else None
        })
    
    return jsonify(parts_data)

@api_bp.route('/maintenance/record', methods=['POST'])
@token_required
def record_maintenance(current_user):
    """API endpoint to record maintenance for a part"""
    data = request.get_json()
    
    if not data or 'part_id' not in data:
        return jsonify({'error': 'Missing part_id'}), 400
    
    part_id = data.get('part_id')
    notes = data.get('notes', '')
    
    part = db.session.get(Part, part_id)
    if not part:
        abort(404)
    machine = Machine.query.get(part.machine_id)
    
    # Check if user has access to this machine's site
    site = Site.query.get(machine.site_id)
    if not current_user.is_admin and site not in current_user.sites:
        return jsonify({'error': 'Access denied'}), 403
    
    # Update part maintenance information
    maintenance_date = datetime.datetime.utcnow()
    performed_by = current_user.full_name or current_user.username
    
    # Update part
    part.last_maintenance = maintenance_date
    part.last_maintained_by = performed_by
    part.update_next_maintenance()
    db.session.commit()
    
    # Create maintenance log entry
    log = MaintenanceLog(
        machine_id=machine.id,
        part_id=part.id,
        performed_by=performed_by,
        maintenance_date=maintenance_date,
        notes=notes
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Maintenance recorded for {part.name}',
        'part_id': part.id,
        'next_maintenance': part.next_maintenance.isoformat()
    })

# Add a health check endpoint
@api_bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint for the Electron app to verify server status"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

# Register blueprint with app
def register_api():
    app.register_blueprint(api_bp, url_prefix='/api')
