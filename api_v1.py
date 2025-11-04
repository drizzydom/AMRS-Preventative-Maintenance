"""
REST API v1 endpoints for React frontend
Performance optimized with caching and query optimization
"""
from flask import Blueprint, jsonify, request, session
from flask_login import login_user, logout_user, current_user, login_required
from functools import wraps, lru_cache
from models import User, db, hash_value
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
        
        # Find user using hashed username (for encrypted username support in offline mode)
        # Explicitly join the role relationship to ensure it's loaded
        from models import Role
        user = User.query.options(db.joinedload(User.role)).filter_by(username_hash=hash_value(username)).first()
        
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
        
        # Check if account is active (check 'active' column if it exists, otherwise use is_active property)
        is_user_active = getattr(user, 'active', True) if hasattr(user, 'active') else getattr(user, 'is_active', True)
        if not is_user_active:
            logger.warning(f'Login attempt for inactive account: {username}')
            return api_response(
                error='Account locked - contact administrator',
                status=403
            )
        
        # Login user
        login_user(user, remember=remember_me)
        logger.info(f'User logged in successfully: {username}')
        
        # Return user data - handle role safely
        role_name = 'user'
        permissions = []
        
        try:
            logger.info(f'Accessing role for user {username}: role_id={user.role_id}, role type={type(user.role)}, role value={repr(user.role)}')
            if user.role:
                # Check if role is an object with name attribute
                if hasattr(user.role, 'name'):
                    role_name = user.role.name
                    # Get permissions if available
                    if hasattr(user.role, 'permissions'):
                        permissions_str = user.role.permissions or ''
                        permissions = [p.strip() for p in permissions_str.split(',') if p.strip()]
                elif isinstance(user.role, str):
                    role_name = user.role
                    logger.warning(f'Role is a string: {user.role}')
        except Exception as role_error:
            logger.error(f'Error accessing role for user {username}: {role_error}', exc_info=True)
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': role_name,
            'permissions': permissions,
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
        # Handle role safely - it might be a string or None
        role_name = 'user'
        permissions = []
        
        if hasattr(current_user, 'role') and current_user.role:
            if isinstance(current_user.role, str):
                role_name = current_user.role
            elif hasattr(current_user.role, 'name'):
                role_name = current_user.role.name
                if hasattr(current_user.role, 'permissions'):
                    try:
                        permissions = [perm.name for perm in current_user.role.permissions]
                    except:
                        permissions = []
        
        user_data = {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'role': role_name,
            'permissions': permissions,
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
        from models import Machine, Part, MaintenanceRecord
        from sqlalchemy import func, and_
        
        # Optimized queries using single database calls
        today = datetime.now().date()
        due_soon_date = today + timedelta(days=7)
        first_day_of_month = today.replace(day=1)
        
        # Single query for machine count
        total_machines = db.session.query(func.count(Machine.id)).filter_by(
            decommissioned=False
        ).scalar()
        
        # Query parts for maintenance statistics (parts have next_maintenance dates)
        overdue_parts = db.session.query(func.count(Part.id)).filter(
            and_(Part.next_maintenance < today, Part.next_maintenance.isnot(None))
        ).scalar()
        
        due_soon_parts = db.session.query(func.count(Part.id)).filter(
            and_(
                Part.next_maintenance >= today,
                Part.next_maintenance <= due_soon_date,
                Part.next_maintenance.isnot(None)
            )
        ).scalar()
        
        # Count completed maintenance records this month
        completed_this_month = db.session.query(func.count(MaintenanceRecord.id)).filter(
            MaintenanceRecord.date >= first_day_of_month
        ).scalar()
        
        stats = {
            'total_machines': total_machines or 0,
            'overdue': int(overdue_parts or 0),
            'due_soon': int(due_soon_parts or 0),
            'completed': int(completed_this_month or 0),
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
        ).filter_by(decommissioned=False).all()
        
        machines_data = []
        for machine in machines:
            machines_data.append({
                'id': machine.id,
                'name': machine.name,
                'serial': machine.serial_number if hasattr(machine, 'serial_number') else '',
                'model': machine.model if hasattr(machine, 'model') else '',
                'machine_number': machine.machine_number if hasattr(machine, 'machine_number') else '',
                'site': machine.site.name if machine.site else '',
                'site_id': machine.site_id if hasattr(machine, 'site_id') else None,
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
    """Get list of maintenance tasks based on parts with due maintenance"""
    try:
        from models import Part, Machine
        from sqlalchemy.orm import joinedload
        from sqlalchemy import and_
        
        today = datetime.now().date()
        due_soon_date = today + timedelta(days=7)
        
        # Get all parts that have upcoming or overdue maintenance
        # Optimize with eager loading to avoid N+1 queries
        parts = Part.query.options(
            joinedload(Part.machine).joinedload(Machine.site)
        ).filter(
            Part.next_maintenance.isnot(None)
        ).all()
        
        tasks_data = []
        for part in parts:
            if not part.next_maintenance:
                continue
                
            # Determine status based on next_maintenance date
            status = 'pending'
            if part.next_maintenance < today:
                status = 'overdue'
            elif part.next_maintenance <= due_soon_date:
                status = 'due-soon'
            
            # Get machine and site info
            machine_name = part.machine.name if part.machine else 'Unknown'
            site_name = part.machine.site.name if part.machine and part.machine.site else ''
            
            tasks_data.append({
                'id': part.id,
                'machine': machine_name,
                'task': f"{part.name} - {part.description}" if part.description else part.name,
                'dueDate': part.next_maintenance.strftime('%Y-%m-%d'),
                'status': status,
                'assignedTo': '',  # Can be added from maintenance records if needed
                'site': site_name,
                'priority': 'high' if status == 'overdue' else 'medium' if status == 'due-soon' else 'low',
                'lastMaintenance': part.last_maintenance.strftime('%Y-%m-%d') if part.last_maintenance else None,
                'frequency': f"{part.maintenance_frequency} {part.maintenance_unit}" if part.maintenance_frequency else None,
            })
        
        # Sort by due date (overdue first, then upcoming)
        tasks_data.sort(key=lambda x: (x['status'] != 'overdue', x['dueDate']))
        
        return api_response(data=tasks_data)
        
    except Exception as e:
        logger.error(f'Get maintenance error: {str(e)}', exc_info=True)
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
                'activeCount': len([m for m in site.machines if not m.decommissioned]) if hasattr(site, 'machines') else 0,
                'maintenanceThreshold': site.maintenance_threshold if hasattr(site, 'maintenance_threshold') else 7,
                'contactPerson': site.contact_person if hasattr(site, 'contact_person') else '',
                'phone': site.phone if hasattr(site, 'phone') else '',
                'status': 'active',
            })
        
        return api_response(data=sites_data)
        
    except Exception as e:
        logger.error(f'Get sites error: {str(e)}')
        return api_response(error='Failed to load sites', status=500)

# ==================== AUDIT ENDPOINTS ====================

@api_v1.route('/audits', methods=['GET'])
@api_login_required
def api_get_audits():
    """Get list of audit tasks"""
    try:
        from models import AuditTask, AuditTaskCompletion
        from sqlalchemy.orm import joinedload
        
        # Get audit tasks based on user permissions
        if current_user.is_admin:
            audit_tasks = AuditTask.query.options(joinedload(AuditTask.machines)).all()
        else:
            user_site_ids = [site.id for site in current_user.sites] if hasattr(current_user, 'sites') else []
            audit_tasks = AuditTask.query.options(joinedload(AuditTask.machines)).filter(
                AuditTask.site_id.in_(user_site_ids)
            ).all() if user_site_ids else []
        
        audits_data = []
        for task in audit_tasks:
            # Get completion stats
            total_machines = len(task.machines) if hasattr(task, 'machines') else 0
            completed_today = AuditTaskCompletion.query.filter_by(
                audit_task_id=task.id,
                date=datetime.utcnow().date(),
                completed=True
            ).count()
            
            # Determine status
            if completed_today == total_machines and total_machines > 0:
                status = 'completed'
            elif completed_today > 0:
                status = 'in-progress'
            else:
                status = 'pending'
            
            site = task.site if hasattr(task, 'site') else None
            
            audits_data.append({
                'id': task.id,
                'name': task.name,
                'description': task.description if hasattr(task, 'description') else '',
                'site': site.name if site else '',
                'site_id': task.site_id,
                'interval': task.interval if hasattr(task, 'interval') else 'daily',
                'custom_interval_days': task.custom_interval_days if hasattr(task, 'custom_interval_days') else None,
                'color': task.color if hasattr(task, 'color') else None,
                'totalMachines': total_machines,
                'completedToday': completed_today,
                'status': status,
                'machines': [{'id': m.id, 'name': m.name} for m in task.machines] if hasattr(task, 'machines') else [],
                'created_at': task.created_at.isoformat() if hasattr(task, 'created_at') and task.created_at else None,
            })
        
        return api_response(data=audits_data)
        
    except Exception as e:
        logger.error(f'Get audits error: {str(e)}')
        return api_response(error='Failed to load audits', status=500)

# ==================== USERS ENDPOINTS ====================

@api_v1.route('/users', methods=['GET'])
@api_login_required
def api_get_users():
    """Get list of users (admin only)"""
    try:
        # Check admin permission
        if not current_user.is_admin:
            return api_response(error='Admin access required', status=403)
        
        users = User.query.all()
        
        users_data = []
        for user in users:
            role = user.role if hasattr(user, 'role') else None
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name if hasattr(user, 'full_name') else '',
                'role': role.name if role and hasattr(role, 'name') else (role if isinstance(role, str) else 'User'),
                'role_id': user.role_id if hasattr(user, 'role_id') else None,
                'is_admin': user.is_admin if hasattr(user, 'is_admin') else False,
                'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
            })
        
        return api_response(data=users_data)
        
    except Exception as e:
        logger.error(f'Get users error: {str(e)}')
        return api_response(error='Failed to load users', status=500)

@api_v1.route('/roles', methods=['GET'])
@api_login_required
def api_get_roles():
    """Get list of roles"""
    try:
        from models import Role
        roles = Role.query.all()
        
        roles_data = []
        for role in roles:
            roles_data.append({
                'id': role.id,
                'name': role.name,
                'description': role.description if hasattr(role, 'description') else '',
                'permissions': role.permissions.split(',') if hasattr(role, 'permissions') and role.permissions else [],
            })
        
        return api_response(data=roles_data)
        
    except Exception as e:
        logger.error(f'Get roles error: {str(e)}')
        return api_response(error='Failed to load roles', status=500)

# ==================== ERROR HANDLERS ====================

@api_v1.errorhandler(404)
def api_not_found(error):
    return api_response(error='Endpoint not found', status=404)

@api_v1.errorhandler(500)
def api_server_error(error):
    return api_response(error='Internal server error', status=500)
