"""
REST API v1 endpoints for React frontend
Performance optimized with caching and query optimization
"""
from flask import Blueprint, jsonify, request, session
from flask_login import login_user, logout_user, current_user, login_required
from functools import wraps, lru_cache
from models import User, db
from werkzeug.security import check_password_hash
import logging
from datetime import datetime, timedelta

# Create API blueprint
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# Setup logging
logger = logging.getLogger(__name__)

# Simple in-memory cache for dashboard stats (cache for 5 minutes)
_dashboard_cache = {'data': None, 'timestamp': None}
CACHE_DURATION = 300  # 5 minutes in seconds

def api_response(data=None, message=None, error=None, status=200):
    """Standard API response format"""
    response = {}
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    if error:
        response['error'] = error
        status = status if status >= 400 else 400
    
    return jsonify(response), status

def api_login_required(f):
    """Decorator for API endpoints that require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return api_response(error='Authentication required', status=401)
        return f(*args, **kwargs)
    return decorated_function

# ==================== AUTH ENDPOINTS ====================

@api_v1.route('/auth/login', methods=['POST'])
def api_login():
    """Login endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        remember_me = data.get('remember_me', False)
        
        if not username or not password:
            return api_response(
                error='Username and password are required',
                status=400
            )
        
        # Find user
        user = User.query.filter_by(username=username).first()
        
        if not user:
            logger.warning(f'Login attempt for non-existent user: {username}')
            return api_response(
                error='Invalid username or password',
                status=401
            )
        
        # Check password
        if not check_password_hash(user.password_hash, password):
            logger.warning(f'Failed login attempt for user: {username}')
            return api_response(
                error='Invalid username or password',
                status=401
            )
        
        # Check if account is active
        if not user.is_active:
            logger.warning(f'Login attempt for inactive account: {username}')
            return api_response(
                error='Account locked - contact administrator',
                status=403
            )
        
        # Login user
        login_user(user, remember=remember_me)
        logger.info(f'User logged in successfully: {username}')
        
        # Return user data
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role.name if user.role else 'user',
            'permissions': [perm.name for perm in user.role.permissions] if user.role else [],
        }
        
        return api_response(
            data={'user': user_data},
            message='Login successful'
        )
        
    except Exception as e:
        logger.error(f'Login error: {str(e)}')
        return api_response(
            error='Server connection failed',
            status=500
        )

@api_v1.route('/auth/logout', methods=['POST'])
@api_login_required
def api_logout():
    """Logout endpoint"""
    try:
        username = current_user.username
        logout_user()
        logger.info(f'User logged out: {username}')
        return api_response(message='Logout successful')
    except Exception as e:
        logger.error(f'Logout error: {str(e)}')
        return api_response(error='Logout failed', status=500)

@api_v1.route('/auth/me', methods=['GET'])
@api_login_required
def api_current_user():
    """Get current user information"""
    try:
        user_data = {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'role': current_user.role.name if current_user.role else 'user',
            'permissions': [perm.name for perm in current_user.role.permissions] if current_user.role else [],
        }
        return api_response(data=user_data)
    except Exception as e:
        logger.error(f'Get current user error: {str(e)}')
        return api_response(error='Failed to get user information', status=500)

# ==================== DASHBOARD ENDPOINTS ====================

@api_v1.route('/dashboard', methods=['GET'])
@api_login_required
def api_dashboard():
    """Get dashboard statistics with caching"""
    global _dashboard_cache
    
    try:
        # Check cache
        now = datetime.now()
        if (_dashboard_cache['data'] is not None and 
            _dashboard_cache['timestamp'] is not None and
            (now - _dashboard_cache['timestamp']).total_seconds() < CACHE_DURATION):
            logger.debug('Returning cached dashboard data')
            return api_response(data=_dashboard_cache['data'])
        
        # Cache miss or expired - fetch fresh data
        from models import Machine, MaintenanceRecord
        from sqlalchemy import func
        
        # Optimized queries using single database calls
        today = datetime.now().date()
        due_soon_date = today + timedelta(days=7)
        first_day_of_month = today.replace(day=1)
        
        # Single query for machine count
        total_machines = db.session.query(func.count(Machine.id)).filter_by(
            is_decommissioned=False
        ).scalar()
        
        # Single query for maintenance statistics
        maintenance_stats = db.session.query(
            func.sum((MaintenanceRecord.next_maintenance_date < today) & 
                    (MaintenanceRecord.completed == False)).label('overdue'),
            func.sum((MaintenanceRecord.next_maintenance_date >= today) & 
                    (MaintenanceRecord.next_maintenance_date <= due_soon_date) &
                    (MaintenanceRecord.completed == False)).label('due_soon'),
            func.sum((MaintenanceRecord.completed == True) &
                    (MaintenanceRecord.completed_date >= first_day_of_month)).label('completed')
        ).first()
        
        stats = {
            'total_machines': total_machines or 0,
            'overdue': int(maintenance_stats.overdue or 0),
            'due_soon': int(maintenance_stats.due_soon or 0),
            'completed': int(maintenance_stats.completed or 0),
        }
        
        # Update cache
        _dashboard_cache['data'] = stats
        _dashboard_cache['timestamp'] = now
        logger.debug('Dashboard cache updated')
        
        return api_response(data=stats)
        
    except Exception as e:
        logger.error(f'Dashboard error: {str(e)}')
        return api_response(error='Failed to load dashboard data', status=500)

# ==================== MACHINES ENDPOINTS ====================

@api_v1.route('/machines', methods=['GET'])
@api_login_required
def api_get_machines():
    """Get list of machines with optimized queries"""
    try:
        from models import Machine
        from sqlalchemy.orm import joinedload
        
        # Optimize with eager loading to avoid N+1 queries
        machines = Machine.query.options(
            joinedload(Machine.site)
        ).filter_by(is_decommissioned=False).all()
        
        machines_data = []
        for machine in machines:
            machines_data.append({
                'id': machine.id,
                'name': machine.name,
                'serial': machine.serial_number if hasattr(machine, 'serial_number') else '',
                'model': machine.model if hasattr(machine, 'model') else '',
                'site': machine.site.name if machine.site else '',
                'status': 'active',  # Add status logic as needed
                'lastMaintenance': machine.last_maintenance.strftime('%Y-%m-%d') if hasattr(machine, 'last_maintenance') and machine.last_maintenance else None,
                'nextMaintenance': machine.next_maintenance.strftime('%Y-%m-%d') if hasattr(machine, 'next_maintenance') and machine.next_maintenance else None,
            })
        
        return api_response(data=machines_data)
        
    except Exception as e:
        logger.error(f'Get machines error: {str(e)}')
        return api_response(error='Failed to load machines', status=500)

# ==================== MAINTENANCE ENDPOINTS ====================

@api_v1.route('/maintenance', methods=['GET'])
@api_login_required
def api_get_maintenance():
    """Get list of maintenance tasks with optimized queries"""
    try:
        from models import MaintenanceRecord
        from sqlalchemy.orm import joinedload
        
        # Optimize with eager loading to avoid N+1 queries
        tasks = MaintenanceRecord.query.options(
            joinedload(MaintenanceRecord.machine).joinedload('site')
        ).filter_by(completed=False).all()
        
        today = datetime.now().date()
        due_soon_date = today + timedelta(days=7)
        
        tasks_data = []
        for task in tasks:
            # Determine status
            status = 'pending'
            if task.next_maintenance_date:
                if task.next_maintenance_date < today:
                    status = 'overdue'
                elif task.next_maintenance_date <= due_soon_date:
                    status = 'due-soon'
            
            tasks_data.append({
                'id': task.id,
                'machine': task.machine.name if task.machine else '',
                'task': task.task_description if hasattr(task, 'task_description') else 'Maintenance',
                'dueDate': task.next_maintenance_date.strftime('%Y-%m-%d') if task.next_maintenance_date else None,
                'status': status,
                'assignedTo': task.assigned_to if hasattr(task, 'assigned_to') else '',
                'site': task.machine.site.name if task.machine and task.machine.site else '',
                'priority': 'medium',  # Add priority logic as needed
            })
        
        return api_response(data=tasks_data)
        
    except Exception as e:
        logger.error(f'Get maintenance error: {str(e)}')
        return api_response(error='Failed to load maintenance tasks', status=500)

# ==================== SITES ENDPOINTS ====================

@api_v1.route('/sites', methods=['GET'])
@api_login_required
def api_get_sites():
    """Get list of sites"""
    try:
        from models import Site
        sites = Site.query.all()
        
        sites_data = []
        for site in sites:
            sites_data.append({
                'id': site.id,
                'name': site.name,
                'location': site.location if hasattr(site, 'location') else '',
                'machineCount': len(site.machines) if hasattr(site, 'machines') else 0,
                'activeCount': len([m for m in site.machines if not m.is_decommissioned]) if hasattr(site, 'machines') else 0,
                'maintenanceThreshold': site.maintenance_threshold if hasattr(site, 'maintenance_threshold') else 7,
                'contactPerson': site.contact_person if hasattr(site, 'contact_person') else '',
                'phone': site.phone if hasattr(site, 'phone') else '',
                'status': 'active',
            })
        
        return api_response(data=sites_data)
        
    except Exception as e:
        logger.error(f'Get sites error: {str(e)}')
        return api_response(error='Failed to load sites', status=500)

# ==================== ERROR HANDLERS ====================

@api_v1.errorhandler(404)
def api_not_found(error):
    return api_response(error='Endpoint not found', status=404)

@api_v1.errorhandler(500)
def api_server_error(error):
    return api_response(error='Internal server error', status=500)
