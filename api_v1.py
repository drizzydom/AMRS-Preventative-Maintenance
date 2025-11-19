"""
REST API v1 endpoints for React frontend
Performance optimized with caching and query optimization
"""
import uuid
from flask import Blueprint, jsonify, request, session
from flask_login import login_user, logout_user, current_user, login_required
from functools import wraps, lru_cache
from models import User, db, hash_value
from remember_session_manager import (
    create_or_update_session,
    queue_cookie_refresh,
    queue_cookie_clear,
    sanitize_device_id,
    build_fingerprint,
    revoke_user_sessions,
    REMEMBER_DEVICE_COOKIE,
)
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


def _get_role_name(role):
    if isinstance(role, str):
        return role
    if hasattr(role, 'name') and role.name:
        return role.name
    return ''


def _get_role_permissions(role):
    permissions = []
    try:
        if isinstance(role, str):
            from models import Role

            db_role = Role.query.filter_by(name=role).first()
            if db_role and db_role.permissions:
                permissions = [p.strip() for p in db_role.permissions.split(',') if p.strip()]
        elif role and hasattr(role, 'permissions') and role.permissions:
            permissions = [p.strip() for p in role.permissions.split(',') if p.strip()]
    except Exception as exc:
        logger.debug(f'Permission lookup failed: {exc}')
    return permissions


def _current_permissions():
    if not current_user or not current_user.is_authenticated:
        return set()

    permissions = set()
    if getattr(current_user, 'is_admin', False):
        permissions.add('admin.full')

    permissions.update(_get_role_permissions(getattr(current_user, 'role', None)))
    return permissions


def _is_admin_user():
    if not current_user or not current_user.is_authenticated:
        return False
    if getattr(current_user, 'is_admin', False):
        return True
    role_name = _get_role_name(getattr(current_user, 'role', None))
    return role_name.lower() == 'admin'


def _has_permission(permission: str) -> bool:
    if not permission:
        return False
    if _is_admin_user():
        return True
    return permission in _current_permissions()


def _user_site_ids():
    try:
        return [site.id for site in getattr(current_user, 'sites', []) if getattr(site, 'id', None) is not None]
    except Exception:
        return []


def _request_ip():
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or ''


def _resolve_device_id(preferred: str | None = None):
    candidates = [preferred, request.headers.get('X-Device-Id'), request.cookies.get(REMEMBER_DEVICE_COOKIE)]
    for candidate in candidates:
        device_id = sanitize_device_id(candidate)
        if device_id:
            return device_id
    return str(uuid.uuid4())


def _request_fingerprint(device_id: str) -> str:
    return build_fingerprint(device_id or '', request.headers.get('User-Agent', ''), (_request_ip() or '')[:24])


def _can_view_all_sites():
    if _is_admin_user():
        return True
    return 'maintenance.record' in _current_permissions()


def _has_any_permission(*permissions):
    """Return True if user has at least one of the given permissions."""
    for permission in permissions:
        if permission and _has_permission(permission):
            return True
    return False


def _allowed_site_ids():
    """Return list of site IDs the current user can access or None for all."""
    if _can_view_all_sites():
        return None
    return _user_site_ids()


def _has_site_access(site_id):
    """Check whether the current user can access the provided site ID."""
    if site_id is None:
        return True
    allowed = _allowed_site_ids()
    if allowed is None:
        return True
    return site_id in allowed

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
        
        # Login user (custom remember handled below)
        login_user(user, remember=False)
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
            'is_admin': bool(getattr(user, 'is_admin', False) or role_name.lower() == 'admin'),
        }
        
        device_id = _resolve_device_id(data.get('device_id'))
        if remember_me:
            session_record, raw_token = create_or_update_session(
                user,
                device_id,
                user_agent=request.headers.get('User-Agent', ''),
                ip_address=_request_ip(),
                fingerprint=_request_fingerprint(device_id),
            )
            queue_cookie_refresh(session_record.id, raw_token, device_id)
        else:
            revoke_user_sessions(user.id, device_id=device_id)
            queue_cookie_clear()

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
        device_id = sanitize_device_id(request.cookies.get(REMEMBER_DEVICE_COOKIE))
        revoke_user_sessions(current_user.id, device_id=device_id)
        queue_cookie_clear()
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
        role_name = _get_role_name(getattr(current_user, 'role', None)) or 'user'
        permissions = list(_current_permissions())
        
        user_data = {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'role': role_name,
            'permissions': permissions,
            'is_admin': _is_admin_user(),
        }
        return api_response(data=user_data)
    except Exception as e:
        logger.error(f'Get current user error: {str(e)}')
        return api_response(error='Failed to get user information', status=500)

# ==================== DASHBOARD ENDPOINTS ====================

@api_v1.route('/dashboard', methods=['GET'])
@api_login_required
def api_get_dashboard():
    """Get dashboard statistics with 5-minute caching"""
    try:
        site_scope = None
        if not _can_view_all_sites():
            site_scope = _user_site_ids()
            if not site_scope:
                stats = {
                    'total_machines': 0,
                    'overdue': 0,
                    'due_soon': 0,
                    'completed': 0,
                }
                return api_response(data=stats)
        use_cache = site_scope is None

        # Check cache first
        now = datetime.now()
        if (use_cache and _dashboard_cache['data'] is not None and 
            _dashboard_cache['timestamp'] is not None and
            (now - _dashboard_cache['timestamp']).total_seconds() < CACHE_DURATION):
            logger.debug('Returning cached dashboard data')
            return api_response(data=_dashboard_cache['data'])
        
        logger.info('Fetching fresh dashboard data...')
        
        # Cache miss or expired - fetch fresh data
        from models import Machine, Part, MaintenanceRecord
        from sqlalchemy import func, and_
        
        # Use datetime for consistent comparisons (parts store datetime, not just date)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        due_soon_date = today + timedelta(days=7)
        first_day_of_month = today.replace(day=1)
        
        logger.debug(f'Dashboard date filters: today={today}, due_soon_date={due_soon_date}, first_day_of_month={first_day_of_month}')
        
        # Single query for machine count
        machine_query = db.session.query(func.count(Machine.id)).filter_by(decommissioned=False)
        if site_scope is not None:
            machine_query = machine_query.filter(Machine.site_id.in_(site_scope))
        total_machines = machine_query.scalar()
        logger.debug(f'Total machines (not decommissioned): {total_machines}')
        
        # Query parts for maintenance statistics (parts have next_maintenance dates)
        overdue_query = db.session.query(func.count(Part.id)).filter(
            and_(Part.next_maintenance < today, Part.next_maintenance.isnot(None))
        )
        due_soon_query = db.session.query(func.count(Part.id)).filter(
            and_(
                Part.next_maintenance >= today,
                Part.next_maintenance <= due_soon_date,
                Part.next_maintenance.isnot(None)
            )
        )

        if site_scope is not None:
            overdue_query = overdue_query.join(Machine, Part.machine_id == Machine.id).filter(Machine.site_id.in_(site_scope))
            due_soon_query = due_soon_query.join(Machine, Part.machine_id == Machine.id).filter(Machine.site_id.in_(site_scope))

        overdue_parts = overdue_query.scalar()
        logger.debug(f'Overdue parts: {overdue_parts}')
        
        due_soon_parts = due_soon_query.scalar()
        logger.debug(f'Due soon parts: {due_soon_parts}')
        
        # Count completed maintenance records this month
        completed_query = db.session.query(func.count(MaintenanceRecord.id)).filter(
            MaintenanceRecord.date >= first_day_of_month
        )

        if site_scope is not None:
            completed_query = completed_query.join(Machine, MaintenanceRecord.machine_id == Machine.id).filter(
                Machine.site_id.in_(site_scope)
            )

        completed_this_month = completed_query.scalar()
        logger.debug(f'Completed maintenance this month: {completed_this_month}')
        
        stats = {
            'total_machines': total_machines or 0,
            'overdue': int(overdue_parts or 0),
            'due_soon': int(due_soon_parts or 0),
            'completed': int(completed_this_month or 0),
        }
        
        # Update cache
        if use_cache:
            _dashboard_cache['data'] = stats
            _dashboard_cache['timestamp'] = now
            logger.info(f'Dashboard cache updated: {stats}')
        
        return api_response(data=stats)
        
    except Exception as e:
        logger.error(f'Dashboard error: {str(e)}', exc_info=True)
        return api_response(error='Failed to load dashboard data', status=500)

# ==================== MACHINES ENDPOINTS ====================

@api_v1.route('/machines', methods=['GET'])
@api_login_required
def api_get_machines():
    """Get list of machines with optimized queries"""
    try:
        if not (_has_permission('machines.view') or _has_permission('maintenance.record') or _is_admin_user()):
            return api_response(error='Insufficient permissions', status=403)

        from models import Machine
        from sqlalchemy.orm import joinedload
        
        # Optimize with eager loading to avoid N+1 queries
        query = Machine.query.options(joinedload(Machine.site)).filter_by(decommissioned=False)

        if not _can_view_all_sites():
            site_ids = _user_site_ids()
            if not site_ids:
                return api_response(data=[])
            query = query.filter(Machine.site_id.in_(site_ids))

        machines = query.all()
        
        machines_data = []
        for machine in machines:
            machines_data.append({
                'id': machine.id,
                'name': machine.name,
                'serial': machine.serial_number if hasattr(machine, 'serial_number') else '',
                'model': machine.model if hasattr(machine, 'model') else '',
                'machine_number': machine.machine_number if hasattr(machine, 'machine_number') else '',
                'site': machine.site.name if machine.site else '',
                'site_name': machine.site.name if machine.site else '',
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
    """Get list of maintenance tasks based on parts with due maintenance
    
    Query parameters:
    - status: Filter by status ('overdue', 'due_soon', 'pending')
    - site_id: Filter by site ID
    """
    try:
        if not (_has_permission('maintenance.view') or _has_permission('maintenance.record') or _is_admin_user()):
            return api_response(error='Insufficient permissions', status=403)

        from models import Part, Machine, Site
        from sqlalchemy.orm import joinedload
        from sqlalchemy import and_
        
        # Use datetime for consistent comparisons (parts store datetime, not just date)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        due_soon_date = today + timedelta(days=7)
        
        # Get query parameters
        status_filter = request.args.get('status', None)
        site_id_filter = request.args.get('site_id', None)
        
        # Get all parts that have upcoming or overdue maintenance
        # Optimize with eager loading to avoid N+1 queries
        query = Part.query.options(
            joinedload(Part.machine).joinedload(Machine.site)
        ).filter(Part.next_maintenance.isnot(None))
        joined_machine = False
        
        # Apply site filter if provided
        if site_id_filter and site_id_filter != 'all':
            try:
                site_id = int(site_id_filter)
                if not _can_view_all_sites():
                    allowed_site_ids = _user_site_ids()
                    if site_id not in allowed_site_ids:
                        return api_response(error='Site access denied', status=403)
                query = query.join(Part.machine).filter(Machine.site_id == site_id)
                joined_machine = True
            except (ValueError, TypeError):
                pass
        
        if not _can_view_all_sites():
            allowed_site_ids = _user_site_ids()
            if not allowed_site_ids:
                return api_response(data=[])
            if not joined_machine:
                query = query.join(Part.machine)
                joined_machine = True
            query = query.filter(Machine.site_id.in_(allowed_site_ids))

        parts = query.all()
        
        # Define patterns for import artifacts that should be excluded
        import_artifact_patterns = [
            'maintenance done',
            'maintenance type',
            'maintenance - ',
            'maint done',
            'maint type',
            'inspection done',
            'inspection type',
            'service done',
            'service type',
        ]
        
        tasks_data = []
        for part in parts:
            if not part.next_maintenance:
                continue
            
            # Filter out import artifacts - check both part name and description
            part_name_lower = part.name.lower() if part.name else ''
            part_desc_lower = part.description.lower() if part.description else ''
            
            is_artifact = False
            for pattern in import_artifact_patterns:
                if pattern in part_name_lower or pattern in part_desc_lower:
                    is_artifact = True
                    break
            
            if is_artifact:
                continue  # Skip this part as it's an import artifact
                
            # Determine status based on next_maintenance date
            status = 'pending'
            if part.next_maintenance < today:
                status = 'overdue'
            elif part.next_maintenance <= due_soon_date:
                status = 'due_soon'  # Changed from 'due-soon' to match frontend
            
            # Apply status filter if provided
            if status_filter and status != status_filter:
                continue
            
            # Get machine and site info
            machine_name = part.machine.name if part.machine else 'Unknown'
            machine_id = part.machine.id if part.machine else None
            machine_serial = part.machine.serial_number if part.machine and hasattr(part.machine, 'serial_number') else ''
            site_name = part.machine.site.name if part.machine and part.machine.site else ''
            site_id = part.machine.site.id if part.machine and part.machine.site else None
            
            # Calculate days overdue or days until due
            days_diff = (part.next_maintenance - today).days
            
            # Build task name, avoiding duplication of machine name
            task_name = part.name
            if part.description and part.description != part.name:
                # Only add description if it's different from part name
                task_name = f"{part.name} - {part.description}"
            
            task_dict = {
                'id': part.id,
                'part_name': part.name,
                'machine': machine_name,
                'machine_name': machine_name,
                'machine_id': machine_id,
                'machine_serial': machine_serial,
                'task': task_name,
                'dueDate': part.next_maintenance.strftime('%Y-%m-%d'),
                'next_maintenance': part.next_maintenance.strftime('%Y-%m-%d'),
                'status': status,
                'assignedTo': '',  # Can be added from maintenance records if needed
                'site': site_name,
                'site_name': site_name,
                'site_id': site_id,
                'priority': 'high' if status == 'overdue' else 'medium' if status == 'due_soon' else 'low',
                'lastMaintenance': part.last_maintenance.strftime('%Y-%m-%d') if part.last_maintenance else None,
                'frequency': f"{part.maintenance_frequency} {part.maintenance_unit}" if part.maintenance_frequency else None,
            }
            
            # Add days_overdue or days_until based on status
            if status == 'overdue':
                task_dict['days_overdue'] = abs(days_diff)
            else:
                task_dict['days_until'] = days_diff
            
            tasks_data.append(task_dict)
        
        # Sort by due date (overdue first, then upcoming)
        tasks_data.sort(key=lambda x: (x['status'] != 'overdue', x['dueDate']))
        
        logger.info(f'Returning {len(tasks_data)} maintenance tasks (status_filter={status_filter}, site_filter={site_id_filter})')
        return api_response(data=tasks_data)
        
    except Exception as e:
        logger.error(f'Get maintenance error: {str(e)}', exc_info=True)
        return api_response(error='Failed to load maintenance tasks', status=500)

@api_v1.route('/maintenance/part/<int:part_id>', methods=['GET'])
@api_login_required
def api_get_part_maintenance_detail(part_id):
    """Get detailed information for a part including its last maintenance record"""
    try:
        if not _has_any_permission('maintenance.view', 'maintenance.record', 'maintenance.complete'):
            return api_response(error='Insufficient permissions', status=403)
        from models import MaintenanceRecord, Machine, Part
        from sqlalchemy.orm import joinedload
        import re
        
        # Get the part with eager loading
        part = Part.query.options(
            joinedload(Part.machine).joinedload(Machine.site)
        ).get_or_404(part_id)
        
        if not _has_site_access(part.machine.site_id if part.machine else None):
            return api_response(error='Access denied', status=403)
        
        # Get the last maintenance record for this part
        last_record = MaintenanceRecord.query.filter_by(part_id=part_id).order_by(
            MaintenanceRecord.date.desc()
        ).first()
        
        # Build basic part info
        machine_name = part.machine.name if part.machine else 'Unknown'
        site_name = part.machine.site.name if part.machine and part.machine.site else ''
        
        # Parse materials and quantity from notes if there's a last record
        materials = ''
        quantity = ''
        frequency = f"{part.maintenance_frequency} {part.maintenance_unit}" if part.maintenance_frequency else ''
        notes_text = ''
        completed_by = ''
        completed_date = ''
        maintenance_type = ''
        description = part.description or ''
        comments = ''
        
        if last_record:
            notes_text = last_record.notes or last_record.description or last_record.comments or ''
            completed_by = last_record.performed_by or (last_record.user.username if last_record.user else '')
            completed_date = last_record.date.strftime('%Y-%m-%d %H:%M') if last_record.date else ''
            maintenance_type = last_record.maintenance_type or 'Routine'
            comments = last_record.comments or ''
            
            # Try to extract structured data from notes
            materials_match = re.search(r'Materials:\s*([^,]+)', notes_text)
            quantity_match = re.search(r'Qty:\s*([^,]+)', notes_text)
            frequency_match = re.search(r'Frequency:\s*(.+?)(?:,|$)', notes_text)
            
            if materials_match:
                materials = materials_match.group(1).strip()
            if quantity_match:
                quantity = quantity_match.group(1).strip()
            if frequency_match and not frequency:
                frequency = frequency_match.group(1).strip()
        
        # Calculate status
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        status = 'up-to-date'
        days_info = None
        
        if part.next_maintenance:
            if part.next_maintenance < today:
                status = 'overdue'
                days_info = (today - part.next_maintenance).days
            elif part.next_maintenance <= today + timedelta(days=7):
                status = 'due_soon'
                days_info = (part.next_maintenance - today).days
        
        part_data = {
            'id': part.id,
            'part_name': part.name,
            'machine': machine_name,
            'machine_id': part.machine.id if part.machine else None,
            'site': site_name,
            'site_id': part.machine.site.id if part.machine and part.machine.site else None,
            'description': description,
            'status': status,
            'days_info': days_info,
            'next_maintenance': part.next_maintenance.strftime('%Y-%m-%d') if part.next_maintenance else None,
            'last_maintenance': part.last_maintenance.strftime('%Y-%m-%d') if part.last_maintenance else None,
            'maintenance_frequency': part.maintenance_frequency,
            'maintenance_unit': part.maintenance_unit if hasattr(part, 'maintenance_unit') else 'days',
            'frequency': frequency,
            'materials': materials,
            'quantity': quantity,
            'notes': notes_text,
            'lastCompletedDate': completed_date,
            'lastCompletedBy': completed_by,
            'lastMaintenanceType': maintenance_type,
            'comments': comments,
        }
        
        return api_response(data=part_data)
        
    except Exception as e:
        logger.error(f'Get part maintenance detail error: {str(e)}', exc_info=True)
        return api_response(error='Failed to load part maintenance details', status=500)

@api_v1.route('/maintenance/<int:record_id>', methods=['GET'])
@api_login_required
def api_get_maintenance_record(record_id):
    """Get detailed information for a specific maintenance record"""
    try:
        if not _has_any_permission('maintenance.view', 'maintenance.record', 'maintenance.complete'):
            return api_response(error='Insufficient permissions', status=403)
        from models import MaintenanceRecord, Machine, Part
        from sqlalchemy.orm import joinedload
        import re
        
        # Get the record with eager loading
        record = MaintenanceRecord.query.options(
            joinedload(MaintenanceRecord.machine).joinedload(Machine.site),
            joinedload(MaintenanceRecord.part),
            joinedload(MaintenanceRecord.user)
        ).get_or_404(record_id)
        
        if not _has_site_access(record.machine.site_id if record.machine else None):
            return api_response(error='Access denied', status=403)
        
        # Build detailed response
        machine_name = record.machine.name if record.machine else 'Unknown'
        part_name = record.part.name if hasattr(record, 'part') and record.part else 'Unknown'
        site_name = record.machine.site.name if record.machine and record.machine.site else ''
        completed_by = record.performed_by or (record.user.username if record.user else '')
        
        # Parse materials and quantity from notes if available
        materials = ''
        quantity = ''
        frequency = ''
        notes_text = record.notes or record.description or record.comments or ''
        
        # Try to extract structured data from notes
        materials_match = re.search(r'Materials:\s*([^,]+)', notes_text)
        quantity_match = re.search(r'Qty:\s*([^,]+)', notes_text)
        frequency_match = re.search(r'Frequency:\s*(.+?)(?:,|$)', notes_text)
        
        if materials_match:
            materials = materials_match.group(1).strip()
        if quantity_match:
            quantity = quantity_match.group(1).strip()
        if frequency_match:
            frequency = frequency_match.group(1).strip()
        
        record_data = {
            'id': record.id,
            'machine': machine_name,
            'machine_id': record.machine.id if record.machine else None,
            'part': part_name,
            'part_id': record.part.id if hasattr(record, 'part') and record.part else None,
            'completedDate': record.date.strftime('%Y-%m-%d %H:%M') if record.date else '',
            'completedBy': completed_by,
            'site': site_name,
            'site_id': record.machine.site.id if record.machine and record.machine.site else None,
            'maintenanceType': record.maintenance_type or 'Routine',
            'description': record.description or '',
            'comments': record.comments or '',
            'notes': notes_text,
            'materials': materials,
            'quantity': quantity,
            'frequency': frequency,
            'status': record.status or 'completed',
        }
        
        return api_response(data=record_data)
        
    except Exception as e:
        logger.error(f'Get maintenance record error: {str(e)}', exc_info=True)
        return api_response(error='Failed to load maintenance record', status=500)

@api_v1.route('/maintenance/history', methods=['GET'])
@api_login_required
def api_get_maintenance_history():
    """Get list of all completed maintenance records
    
    Query parameters:
    - site_id: Filter by site ID
    - search: Search in machine name, part name, or notes
    """
    try:
        if not _has_any_permission('maintenance.view', 'maintenance.record', 'maintenance.complete'):
            return api_response(error='Insufficient permissions', status=403)
        from models import MaintenanceRecord, Machine, Part
        from sqlalchemy.orm import joinedload
        
        # Get query parameters
        site_id_filter = request.args.get('site_id', None)
        search_query = request.args.get('search', '').strip()
        
        # Build query with eager loading to avoid N+1 queries
        query = MaintenanceRecord.query.options(
            joinedload(MaintenanceRecord.machine).joinedload(Machine.site),
            joinedload(MaintenanceRecord.part),
            joinedload(MaintenanceRecord.user)
        )
        joined_machine = False
        
        # Apply site filter if provided
        if site_id_filter and site_id_filter != 'all':
            try:
                site_id = int(site_id_filter)
                if not _has_site_access(site_id):
                    return api_response(error='Site access denied', status=403)
                query = query.join(MaintenanceRecord.machine).filter(Machine.site_id == site_id)
                joined_machine = True
            except (ValueError, TypeError):
                pass

        allowed_site_ids = _allowed_site_ids()
        if allowed_site_ids is not None:
            if not allowed_site_ids:
                return api_response(data=[])
            if not joined_machine:
                query = query.join(MaintenanceRecord.machine)
                joined_machine = True
            query = query.filter(Machine.site_id.in_(allowed_site_ids))
        
        # Get all records
        records = query.order_by(MaintenanceRecord.date.desc()).all()
        
        # Build response data
        records_data = []
        for record in records:
            # Get related entities
            machine_name = record.machine.name if record.machine else 'Unknown'
            machine_id = record.machine.id if record.machine else None
            part_name = record.part.name if hasattr(record, 'part') and record.part else 'Unknown'
            part_id = record.part.id if hasattr(record, 'part') and record.part else None
            site_name = record.machine.site.name if record.machine and record.machine.site else ''
            site_id = record.machine.site.id if record.machine and record.machine.site else None
            
            # Get completed_by - prefer performed_by, fallback to user relationship
            completed_by = record.performed_by or ''
            if not completed_by and record.user:
                completed_by = record.user.username
            
            # Apply search filter if provided
            if search_query:
                search_lower = search_query.lower()
                if not any([
                    search_lower in machine_name.lower(),
                    search_lower in part_name.lower(),
                    search_lower in (record.notes or '').lower(),
                    search_lower in (record.description or '').lower(),
                    search_lower in completed_by.lower()
                ]):
                    continue
            
            record_dict = {
                'id': record.id,
                'machine': machine_name,
                'machineName': machine_name,
                'machine_id': machine_id,
                'part': part_name,
                'partName': part_name,
                'part_id': part_id,
                'completedDate': record.date.strftime('%Y-%m-%d') if record.date else '',
                'completedBy': completed_by,
                'site': site_name,
                'siteName': site_name,
                'site_id': site_id,
                'notes': record.notes or record.description or record.comments or '',
                'maintenanceType': record.maintenance_type or 'Routine',
                'status': record.status or 'completed',
            }
            
            records_data.append(record_dict)
        
        logger.info(f'Returning {len(records_data)} maintenance history records (site_filter={site_id_filter}, search={search_query})')
        return api_response(data=records_data)
        
    except Exception as e:
        logger.error(f'Get maintenance history error: {str(e)}', exc_info=True)
        return api_response(error='Failed to load maintenance history', status=500)

@api_v1.route('/machines/<int:machine_id>/parts', methods=['GET'])
@api_login_required
def api_get_machine_parts(machine_id):
    """Get all parts for a specific machine with their maintenance status"""
    try:
        if not _has_any_permission('maintenance.view', 'maintenance.record', 'maintenance.complete'):
            return api_response(error='Insufficient permissions', status=403)
        from models import Machine, Part
        from sqlalchemy.orm import joinedload
        
        machine = Machine.query.options(joinedload(Machine.parts)).get_or_404(machine_id)
        
        if not _has_site_access(machine.site_id):
            return api_response(error='Access denied', status=403)
        
        today = datetime.now().date()
        parts_data = []
        
        for part in machine.parts:
            # Determine status
            status = 'up-to-date'
            days_info = None
            
            if part.next_maintenance:
                # Convert next_maintenance to date for comparison if it's a datetime
                next_maint_date = part.next_maintenance.date() if isinstance(part.next_maintenance, datetime) else part.next_maintenance
                
                if next_maint_date < today:
                    status = 'overdue'
                    days_info = (today - next_maint_date).days
                elif next_maint_date <= today + timedelta(days=7):
                    status = 'due-soon'
                    days_info = (next_maint_date - today).days
            
            parts_data.append({
                'id': part.id,
                'name': part.name,
                'description': part.description if hasattr(part, 'description') else '',
                'last_maintenance': part.last_maintenance.strftime('%Y-%m-%d') if part.last_maintenance else None,
                'next_maintenance': part.next_maintenance.strftime('%Y-%m-%d') if part.next_maintenance else None,
                'maintenance_frequency': part.maintenance_frequency if hasattr(part, 'maintenance_frequency') else None,
                'maintenance_unit': part.maintenance_unit if hasattr(part, 'maintenance_unit') else 'days',
                'status': status,
                'days_info': days_info,
            })
        
        return api_response(data=parts_data)
        
    except Exception as e:
        logger.error(f'Get machine parts error: {str(e)}')
        return api_response(error='Failed to load machine parts', status=500)

@api_v1.route('/maintenance/complete-multiple', methods=['POST'])
@api_login_required
def api_complete_multiple_maintenance():
    """Complete maintenance for multiple parts in a single operation"""
    try:
        if not _has_any_permission('maintenance.complete', 'maintenance.record'):
            return api_response(error='Insufficient permissions', status=403)
        from models import Part, Machine, MaintenanceRecord
        from datetime import datetime, timedelta
        from sync_utils_enhanced import add_to_sync_queue_enhanced
        
        data = request.get_json()
        part_ids = data.get('part_ids', [])
        machine_id = data.get('machine_id')
        maintenance_date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        maintenance_type = data.get('type', 'Routine')
        description = data.get('description', '')
        notes = data.get('notes', '')
        
        if not part_ids or not machine_id:
            return api_response(error='Machine ID and at least one part required', status=400)
        
        # Verify machine exists and user has access
        machine = Machine.query.get_or_404(machine_id)
        if not _has_site_access(machine.site_id):
            return api_response(error='Access denied', status=403)
        
        completed_count = 0
        maintenance_records = []
        
        for part_id in part_ids:
            part = Part.query.get(part_id)
            if not part or part.machine_id != machine_id:
                continue
            
            # Create maintenance record
            maintenance_record = MaintenanceRecord(
                machine_id=machine_id,
                part_id=part_id,
                user_id=current_user.id,
                maintenance_type=maintenance_type,
                description=description or f"Maintenance completed for {part.name}",
                date=datetime.strptime(maintenance_date, '%Y-%m-%d').date(),
                performed_by=current_user.username if hasattr(current_user, 'username') else 'Unknown',
                status='completed',
                notes=notes
            )
            db.session.add(maintenance_record)
            
            # Update part's last_maintenance and calculate next_maintenance
            part.last_maintenance = datetime.strptime(maintenance_date, '%Y-%m-%d').date()
            
            if part.maintenance_frequency and part.maintenance_unit:
                if part.maintenance_unit == 'days':
                    part.next_maintenance = part.last_maintenance + timedelta(days=part.maintenance_frequency)
                elif part.maintenance_unit == 'weeks':
                    part.next_maintenance = part.last_maintenance + timedelta(weeks=part.maintenance_frequency)
                elif part.maintenance_unit == 'months':
                    part.next_maintenance = part.last_maintenance + timedelta(days=part.maintenance_frequency * 30)
                elif part.maintenance_unit == 'years':
                    part.next_maintenance = part.last_maintenance + timedelta(days=part.maintenance_frequency * 365)
            
            maintenance_records.append(maintenance_record)
            completed_count += 1
        
        db.session.commit()
        
        # Sync to cloud
        for record in maintenance_records:
            add_to_sync_queue_enhanced('maintenance_records', record.id, 'insert', {
                'id': record.id,
                'machine_id': record.machine_id,
                'part_id': record.part_id,
                'user_id': record.user_id,
                'maintenance_type': record.maintenance_type,
                'description': record.description,
                'date': record.date.isoformat() if record.date else None,
                'performed_by': record.performed_by,
                'status': record.status,
                'notes': record.notes
            }, immediate_sync=True)
        
        # Sync part updates
        for part_id in part_ids:
            part = Part.query.get(part_id)
            if part:
                add_to_sync_queue_enhanced('parts', part.id, 'update', {
                    'id': part.id,
                    'name': part.name,
                    'description': part.description,
                    'machine_id': part.machine_id,
                    'maintenance_frequency': part.maintenance_frequency,
                    'maintenance_unit': part.maintenance_unit,
                    'last_maintenance': part.last_maintenance.isoformat() if part.last_maintenance else None,
                    'next_maintenance': part.next_maintenance.isoformat() if part.next_maintenance else None,
                    'notes': part.notes if hasattr(part, 'notes') else None
                }, immediate_sync=True)
        
        return api_response(
            data={'completed_count': completed_count},
            message=f'Successfully completed maintenance for {completed_count} part(s)'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Complete multiple maintenance error: {str(e)}')
        return api_response(error='Failed to complete maintenance', status=500)

# ==================== SITES ENDPOINTS ====================

@api_v1.route('/sites', methods=['GET'])
@api_login_required
def api_get_sites():
    """Get list of sites"""
    try:
        if not _has_permission('sites.view'):
            return api_response(error='Insufficient permissions', status=403)
        from models import Site
        query = Site.query
        allowed_site_ids = _allowed_site_ids()
        if allowed_site_ids is not None:
            if not allowed_site_ids:
                return api_response(data=[])
            query = query.filter(Site.id.in_(allowed_site_ids))
        sites = query.all()
        
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
        if not _has_any_permission('audits.view', 'audits.edit', 'audits.create'):
            return api_response(error='Insufficient permissions', status=403)
        from models import AuditTask, AuditTaskCompletion
        from sqlalchemy.orm import joinedload
        
        query = AuditTask.query.options(joinedload(AuditTask.machines))
        allowed_site_ids = _allowed_site_ids()
        if allowed_site_ids is not None:
            if not allowed_site_ids:
                return api_response(data=[])
            query = query.filter(AuditTask.site_id.in_(allowed_site_ids))
        audit_tasks = query.all()
        
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

@api_v1.route('/audits/<int:audit_id>/machines', methods=['GET'])
@api_login_required
def api_get_audit_machines(audit_id):
    """Get machines for a specific audit task with their completion status"""
    try:
        if not _has_any_permission('audits.view', 'audits.edit', 'audits.create'):
            return api_response(error='Insufficient permissions', status=403)
        from models import AuditTask, AuditTaskCompletion
        from datetime import datetime
        
        audit_task = AuditTask.query.get_or_404(audit_id)
        
        if not _has_site_access(audit_task.site_id):
            return api_response(error='Access denied', status=403)
        
        today = datetime.utcnow().date()
        machines_data = []
        
        for machine in audit_task.machines:
            # Check if completed today
            completion = AuditTaskCompletion.query.filter_by(
                audit_task_id=audit_id,
                machine_id=machine.id,
                date=today
            ).first()
            
            machines_data.append({
                'id': machine.id,
                'name': machine.name,
                'model': machine.model if hasattr(machine, 'model') else '',
                'serial_number': machine.serial_number if hasattr(machine, 'serial_number') else '',
                'completed': completion.completed if completion else False,
                'completed_at': completion.completed_at.isoformat() if completion and completion.completed_at else None,
                'completed_by': completion.completed_by if completion else None,
            })
        
        return api_response(data=machines_data)
        
    except Exception as e:
        logger.error(f'Get audit machines error: {str(e)}')
        return api_response(error='Failed to load audit machines', status=500)

@api_v1.route('/audits/<int:audit_id>/complete', methods=['POST', 'OPTIONS'])
@api_login_required
def api_complete_audit_task(audit_id):
    """Complete audit task for specific machines"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    if not _has_any_permission('audits.edit', 'audits.create'):
        return api_response(error='Insufficient permissions', status=403)
    
    # Move imports outside try block to see import errors
    from models import AuditTask, AuditTaskCompletion, Machine
    from datetime import datetime
    from sync_utils_enhanced import add_to_sync_queue_enhanced
    from timezone_utils import get_timezone_aware_now
    
    try:
        logger.info(f'[AUDIT COMPLETE] Received POST request for audit_id={audit_id}')
        logger.info(f'[AUDIT COMPLETE] Request data: {request.get_json()}')
        logger.info('[AUDIT COMPLETE] Imports successful')
        audit_task = AuditTask.query.get_or_404(audit_id)
        logger.info(f'[AUDIT COMPLETE] Found audit task: {audit_task.id}')
        
        if not _has_site_access(audit_task.site_id):
            return api_response(error='Access denied', status=403)
        
        data = request.get_json()
        machine_ids = data.get('machine_ids', [])
        
        if not machine_ids:
            return api_response(error='No machines selected', status=400)
        
        today = datetime.utcnow().date()
        completed_count = 0
        
        for machine_id in machine_ids:
            machine = Machine.query.get(machine_id)
            if not machine or machine not in audit_task.machines:
                continue
            
            # Check if already completed today
            existing_completion = AuditTaskCompletion.query.filter_by(
                audit_task_id=audit_id,
                machine_id=machine_id,
                date=today
            ).first()
            
            if existing_completion:
                if existing_completion.completed:
                    continue  # Already completed
                # Update existing record
                existing_completion.completed = True
                existing_completion.completed_by = current_user.id
                existing_completion.completed_at = get_timezone_aware_now()
                completion = existing_completion
            else:
                # Create new completion record
                completion = AuditTaskCompletion(
                    audit_task_id=audit_id,
                    machine_id=machine_id,
                    date=today,
                    completed=True,
                    completed_by=current_user.id,
                    completed_at=get_timezone_aware_now()
                )
                db.session.add(completion)
            
            completed_count += 1
        
        logger.info(f'[AUDIT COMPLETE] About to commit {completed_count} completions')
        db.session.commit()
        logger.info('[AUDIT COMPLETE] Database commit successful')
        
        # Sync to cloud
        logger.info(f'[AUDIT COMPLETE] Starting sync for {len(machine_ids)} machines')
        for machine_id in machine_ids:
            completion = AuditTaskCompletion.query.filter_by(
                audit_task_id=audit_id,
                machine_id=machine_id,
                date=today
            ).first()
            if completion:
                # Format dates safely
                completion_date = completion.date.isoformat() if completion.date else None
                completion_at = completion.completed_at.isoformat() if completion.completed_at else None
                
                add_to_sync_queue_enhanced('audit_task_completions', completion.id, 'upsert', {
                    'id': completion.id,
                    'audit_task_id': completion.audit_task_id,
                    'machine_id': completion.machine_id,
                    'date': completion_date,
                    'completed': completion.completed,
                    'completed_by': completion.completed_by,
                    'completed_at': completion_at
                }, immediate_sync=True)
        
        logger.info(f'[AUDIT COMPLETE] Sync queue updated, preparing response')
        response = api_response(
            data={'completed_count': completed_count},
            message=f'Successfully completed {completed_count} audit task(s)'
        )
        logger.info(f'[AUDIT COMPLETE] Returning success response: {response}')
        return response
        
    except Exception as e:
        import traceback
        db.session.rollback()
        error_details = traceback.format_exc()
        logger.error(f'Complete audit task error: {str(e)}')
        logger.error(f'Full traceback:\n{error_details}')
        return api_response(error=f'Failed to complete audit task: {str(e)}', status=500)

# ==================== USERS ENDPOINTS ====================

@api_v1.route('/users', methods=['GET'])
@api_login_required
def api_get_users():
    """Get list of users (admin only)"""
    try:
        # Check admin permission
        if not _is_admin_user():
            return api_response(error='Admin access required', status=403)
        
        users = User.query.all()
        
        users_data = []
        for user in users:
            role = user.role if hasattr(user, 'role') else None
            
            # Debug: Log raw values
            logger.info(f'Processing user {user.id}: raw _username length={len(user._username) if user._username else 0}')
            
            # Explicitly call the property getters to decrypt values
            try:
                username = user.username  # This calls the @property getter which decrypts
                logger.info(f'User {user.id}: Successfully decrypted username: {username}')
            except Exception as e:
                logger.error(f'Failed to decrypt username for user {user.id}: {str(e)}', exc_info=True)
                # If it looks like encrypted data (long string), note that
                if user._username and len(user._username) > 50:
                    logger.error(f'User {user.id}: Value appears to be encrypted (length={len(user._username)})')
                username = f'user_{user.id}'  # Fallback
            
            try:
                email = user.email  # This calls the @property getter which decrypts
                logger.info(f'User {user.id}: Successfully decrypted email: {email}')
            except Exception as e:
                logger.error(f'Failed to decrypt email for user {user.id}: {str(e)}', exc_info=True)
                if user._email and len(user._email) > 50:
                    logger.error(f'User {user.id}: Email value appears to be encrypted (length={len(user._email)})')
                email = f'user_{user.id}@example.com'  # Fallback
            
            users_data.append({
                'id': user.id,
                'username': username,
                'email': email,
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
        if not _is_admin_user():
            return api_response(error='Admin access required', status=403)
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
