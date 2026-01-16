"""
REST API v1 endpoints for React frontend
Performance optimized with caching and query optimization
"""
import uuid
from flask import Blueprint, jsonify, request, session
from flask_login import login_user, logout_user, current_user, login_required
from functools import wraps, lru_cache
from models import User, db, hash_value, maybe_decrypt
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
import math
from datetime import datetime, timedelta

# Import sync utility for write operations
try:
    from sync_utils_enhanced import add_to_sync_queue_enhanced
except ImportError:
    # Fallback or dummy if not available
    def add_to_sync_queue_enhanced(*args, **kwargs):
        pass

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
        sites = getattr(current_user, 'sites', [])
        ids = [site.id for site in sites if getattr(site, 'id', None) is not None]
        return ids
    except Exception as e:
        logger.error(f"Error getting user sites: {e}")
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


def _device_hint(device_id: str | None) -> str:
    if not device_id:
        return 'unknown'
    tail = device_id[-6:]
    return tail if len(device_id) <= 6 else f'...{tail}'


def _login_feedback_step(key: str, label: str, status: str, detail: str):
    return {
        'key': key,
        'label': label,
        'status': status,
        'detail': detail,
    }


def _login_feedback_payload(attempt_id: str, final_status: str, steps, **context):
    payload = {
        'attempt_id': attempt_id,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'final_status': final_status,
        'steps': steps,
    }
    context = {k: v for k, v in context.items() if v is not None}
    if context:
        payload['context'] = context
    return payload

def api_response(data=None, message=None, error=None, status=200, meta=None):
    """Standard API response format"""
    response = {
        'status': 'error' if error else 'success'
    }
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    if error:
        response['error'] = error
        status = status if status >= 400 else 400
    if meta is not None:
        response['meta'] = meta
    
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
    attempt_id = str(uuid.uuid4())
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')
    raw_remember = data.get('remember_me', False)
    provided_device_id = sanitize_device_id(data.get('device_id'))
    device_hint = _device_hint(provided_device_id)
    request_ip = _request_ip()
    user_agent = request.headers.get('User-Agent', '')

    if isinstance(raw_remember, str):
        remember_me = raw_remember.strip().lower() in {'1', 'true', 'yes', 'on'}
    else:
        remember_me = bool(raw_remember)

    def feedback_meta(final_status: str, steps, extra_context=None):
        context = {
            'device_hint': device_hint,
            'remember_requested': remember_me,
            'ip_fragment': (request_ip or '')[:24],
        }
        if extra_context:
            context.update({k: v for k, v in extra_context.items() if v is not None})
        return {
            'login_feedback': _login_feedback_payload(
                attempt_id,
                final_status,
                steps,
                **context,
            )
        }

    def error_response(message_text: str, final_status: str, steps, status_code: int):
        return api_response(
            error=message_text,
            message=message_text,
            status=status_code,
            meta=feedback_meta(final_status, steps),
        )

    if not username or not password:
        steps = [
            _login_feedback_step('credentials', 'Validate credentials', 'error', 'Username and password are required.'),
            _login_feedback_step('session', 'Secure session', 'skipped', 'Awaiting valid credentials.'),
            _login_feedback_step('workspace', 'Prepare workspace', 'skipped', 'Login required before syncing.'),
        ]
        return error_response('Username and password are required', 'validation_failed', steps, 400)

    try:
        # Find user using hashed username (for encrypted username support in offline mode)
        # Explicitly join the role relationship to ensure it's loaded
        from models import Role
        user = User.query.options(db.joinedload(User.role)).filter_by(username_hash=hash_value(username)).first()

        if not user:
            logger.warning(f'Login attempt for non-existent user: {username}')
            steps = [
                _login_feedback_step('credentials', 'Verify credentials', 'error', 'Username or password was incorrect.'),
                _login_feedback_step('session', 'Secure session', 'skipped', 'Session not created due to invalid credentials.'),
                _login_feedback_step('workspace', 'Prepare workspace', 'skipped', 'Requires a successful login.'),
            ]
            return error_response('Invalid username or password', 'invalid_credentials', steps, 401)

        # Check password
        if not check_password_hash(user.password_hash, password):
            logger.warning(f'Failed login attempt for user: {username}')
            steps = [
                _login_feedback_step('credentials', 'Verify credentials', 'error', 'Username or password was incorrect.'),
                _login_feedback_step('session', 'Secure session', 'skipped', 'Session not created due to invalid credentials.'),
                _login_feedback_step('workspace', 'Prepare workspace', 'skipped', 'Requires a successful login.'),
            ]
            return error_response('Invalid username or password', 'invalid_credentials', steps, 401)

        # Check if account is active (check 'active' column if it exists, otherwise use is_active property)
        is_user_active = getattr(user, 'active', True) if hasattr(user, 'active') else getattr(user, 'is_active', True)
        if not is_user_active:
            logger.warning(f'Login attempt for inactive account: {username}')
            steps = [
                _login_feedback_step('credentials', 'Verify credentials', 'success', 'Password accepted.'),
                _login_feedback_step('session', 'Secure session', 'error', 'Account locked. Contact an administrator.'),
                _login_feedback_step('workspace', 'Prepare workspace', 'skipped', 'Unlock account to continue.'),
            ]
            return error_response('Account locked - contact administrator', 'account_locked', steps, 403)

        # Login user (custom remember handled below)
        login_user(user, remember=False)
        logger.info(f'User logged in successfully: {username}')

        # Return user data - handle role safely
        role_name = 'user'
        permissions = []

        try:
            logger.info(
                f'Accessing role for user {username}: role_id={user.role_id}, role type={type(user.role)}, role value={repr(user.role)}'
            )
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
            'username': maybe_decrypt(user._username),
            'email': maybe_decrypt(user._email),
            'role': role_name,
            'permissions': permissions,
            'is_admin': bool(getattr(user, 'is_admin', False) or role_name.lower() == 'admin'),
        }

        device_id = _resolve_device_id(provided_device_id)
        success_steps = [
            _login_feedback_step('credentials', 'Verify credentials', 'success', 'Credentials accepted.'),
            _login_feedback_step('session', 'Secure session', 'success', f'Session established for {maybe_decrypt(user._username)}.'),
        ]
        extra_context = {}

        if remember_me:
            session_record, raw_token = create_or_update_session(
                user,
                device_id,
                user_agent=user_agent,
                ip_address=request_ip,
                fingerprint=_request_fingerprint(device_id),
            )
            queue_cookie_refresh(session_record.id, raw_token, device_id)
            remember_status = 'success'
            remember_detail = f'Device {device_hint} trusted for faster login.'
            extra_context['remember_session_id'] = session_record.id
        else:
            revoke_user_sessions(user.id, device_id=device_id)
            queue_cookie_clear()
            remember_status = 'skipped'
            remember_detail = 'Not requested for this login.'

        success_steps.append(_login_feedback_step('trust_device', 'Trust this device', remember_status, remember_detail))
        success_steps.append(_login_feedback_step('workspace', 'Prepare workspace', 'pending', 'Launching background sync.'))

        return api_response(
            data={'user': user_data},
            message='Login successful',
            meta=feedback_meta('session_ready', success_steps, extra_context or None),
        )

    except Exception as e:
        logger.error(f'Login error: {str(e)}')
        steps = [
            _login_feedback_step('credentials', 'Verify credentials', 'pending', 'Waiting for server to respond.'),
            _login_feedback_step('session', 'Secure session', 'error', 'Server error prevented login.'),
            _login_feedback_step('workspace', 'Prepare workspace', 'skipped', 'Retry once login succeeds.'),
        ]
        return error_response('Server connection failed', 'server_error', steps, 500)

@api_v1.route('/auth/logout', methods=['POST'])
@api_login_required
def api_logout():
    """Logout endpoint"""
    try:
        username = maybe_decrypt(current_user._username)
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
            'username': maybe_decrypt(current_user._username),
            'email': maybe_decrypt(current_user._email),
            'role': role_name,
            'permissions': permissions,
            'is_admin': _is_admin_user(),
        }
        return api_response(data=user_data)
    except Exception as e:
        logger.error(f'Get current user error: {str(e)}')
        return api_response(error='Failed to load user profile', status=500)

@api_v1.route('/auth/change-password', methods=['POST'])
@api_login_required
def api_change_password():
    """Change current user's password"""
    try:
        data = request.get_json()
        if not data:
            return api_response(error='No data provided', status=400)
            
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return api_response(error='Current and new password are required', status=400)
            
        # Verify current password
        if not current_user.check_password(current_password):
            return api_response(error='Current password is incorrect', status=401)
            
        # Validate new password length
        if len(new_password) < 8:
            return api_response(error='New password must be at least 8 characters long', status=400)
            
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        logger.info(f'Password changed for user: {maybe_decrypt(current_user._username)}')
        return api_response(message='Password updated successfully')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Change password error: {str(e)}')
        return api_response(error='Failed to update password', status=500)
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
        
        # Calculate maintenance statistics based on ACTUAL maintenance records
        # Not the stored next_maintenance field which may have placeholder dates
        MIN_VALID_DATE = datetime(2010, 1, 1)
        
        overdue_count = 0
        due_soon_count = 0
        
        # Build part query based on site scope
        part_query = Part.query
        if site_scope is not None:
            part_query = part_query.join(Machine, Part.machine_id == Machine.id).filter(Machine.site_id.in_(site_scope))
        
        all_parts = part_query.all()
        
        for part in all_parts:
            # Find the latest valid maintenance record (after MIN_VALID_DATE)
            valid_records = [r for r in part.maintenance_records 
                           if r.date and r.date >= MIN_VALID_DATE]
            
            if valid_records:
                # Has valid maintenance history
                latest_record = max(valid_records, key=lambda r: r.date)
                
                # Calculate next maintenance from latest record
                interval_days = part.maintenance_interval_days() if hasattr(part, 'maintenance_interval_days') else 30
                if isinstance(latest_record.date, datetime):
                    next_due = latest_record.date + timedelta(days=interval_days)
                else:
                    next_due = datetime.combine(latest_record.date, datetime.min.time()) + timedelta(days=interval_days)
                
                if next_due < today:
                    overdue_count += 1
                elif next_due <= due_soon_date:
                    due_soon_count += 1
            # Parts without valid maintenance history are NOT counted as overdue
        
        logger.debug(f'Overdue parts (calculated): {overdue_count}')
        logger.debug(f'Due soon parts (calculated): {due_soon_count}')
        
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
            'overdue': overdue_count,
            'due_soon': due_soon_count,
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
        
        site_id_filter = request.args.get('site_id', type=int)

        # Optimize with eager loading to avoid N+1 queries
        query = Machine.query.options(joinedload(Machine.site), joinedload(Machine.parts)).filter_by(decommissioned=False)

        # Explicit site filter if provided
        if site_id_filter:
            if not _has_site_access(site_id_filter):
                return api_response(error='Access denied to this site', status=403)
            query = query.filter(Machine.site_id == site_id_filter)

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
                'cycle_count': machine.cycle_count if hasattr(machine, 'cycle_count') else 0,
                'last_cycle_update': machine.last_cycle_update.strftime('%Y-%m-%d %H:%M:%S') if hasattr(machine, 'last_cycle_update') and machine.last_cycle_update else None,
                'status': 'active',  # Add status logic as needed
                'lastMaintenance': machine.last_maintenance.strftime('%Y-%m-%d') if hasattr(machine, 'last_maintenance') and machine.last_maintenance else None,
                'nextMaintenance': machine.next_maintenance.strftime('%Y-%m-%d') if hasattr(machine, 'next_maintenance') and machine.next_maintenance else None,
            })
        
        return api_response(data=machines_data)
        
    except Exception as e:
        logger.error(f'Get machines error: {str(e)}')
        return api_response(error='Failed to load machines', status=500)


@api_v1.route('/machines/<int:machine_id>/cycle-count', methods=['PUT', 'PATCH'])
@api_login_required
def api_update_machine_cycle_count(machine_id):
    """Update the cycle count for a machine (for cycle-based maintenance tracking)
    
    Request body:
    - cycle_count: New cycle count value (absolute)
    - OR increment: Number to add to current cycle count
    """
    try:
        if not (_has_permission('machines.edit') or _is_admin_user()):
            return api_response(error='Insufficient permissions', status=403)
        
        from models import Machine
        
        machine = Machine.query.get(machine_id)
        if not machine:
            return api_response(error='Machine not found', status=404)
        
        # Check site access
        if not _can_view_all_sites():
            site_ids = _user_site_ids()
            if machine.site_id not in site_ids:
                return api_response(error='Access denied to this machine', status=403)
        
        data = request.get_json() or {}
        
        if 'cycle_count' in data:
            # Set absolute cycle count
            machine.update_cycle_count(int(data['cycle_count']))
        elif 'increment' in data:
            # Increment cycle count
            machine.increment_cycles(int(data['increment']))
        else:
            return api_response(error='Must provide cycle_count or increment', status=400)
        
        db.session.commit()
        
        return api_response(data={
            'id': machine.id,
            'name': machine.name,
            'cycle_count': machine.cycle_count,
            'last_cycle_update': machine.last_cycle_update.strftime('%Y-%m-%d %H:%M:%S') if machine.last_cycle_update else None,
        }, message='Cycle count updated')
        
    except Exception as e:
        logger.error(f'Update machine cycle count error: {str(e)}')
        db.session.rollback()
        return api_response(error='Failed to update cycle count', status=500)


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

        from models import Part, Machine, Site, MaintenanceRecord
        from sqlalchemy.orm import joinedload
        from sqlalchemy import and_
        
        # Use datetime for consistent comparisons (parts store datetime, not just date)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        due_soon_date = today + timedelta(days=7)
        
        # Minimum valid date - anything before this is considered a placeholder/invalid
        MIN_VALID_DATE = datetime(2010, 1, 1)
        
        # Get query parameters
        status_filter = request.args.get('status', None)
        site_id_filter = request.args.get('site_id', None)
        
        # Get all parts - we'll calculate status from maintenance records
        # Optimize with eager loading to avoid N+1 queries
        query = Part.query.options(
            joinedload(Part.machine).joinedload(Machine.site),
            joinedload(Part.maintenance_records)
        )
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
            
            # Find the latest valid maintenance record (after MIN_VALID_DATE)
            valid_records = [r for r in part.maintenance_records 
                           if r.date and r.date >= MIN_VALID_DATE]
            
            if not valid_records:
                # No valid maintenance history - skip (not counted as overdue)
                # These parts need initial maintenance but aren't "overdue"
                continue
            
            latest_record = max(valid_records, key=lambda r: r.date)
            
            # Calculate next maintenance from latest record
            interval_days = part.maintenance_interval_days() if hasattr(part, 'maintenance_interval_days') else 30
            if isinstance(latest_record.date, datetime):
                calculated_next_maintenance = latest_record.date + timedelta(days=interval_days)
            else:
                calculated_next_maintenance = datetime.combine(latest_record.date, datetime.min.time()) + timedelta(days=interval_days)
                
            # Determine status based on maintenance type (cycle-based or time-based)
            status = 'pending'
            is_cycle_based = getattr(part, 'is_cycle_based', False) if hasattr(part, 'is_cycle_based') else False
            
            if is_cycle_based:
                # Use cycle-based status calculation
                cycle_status = part.get_cycle_status() if hasattr(part, 'get_cycle_status') else None
                if cycle_status:
                    status = cycle_status
            else:
                # Time-based status calculation using calculated next maintenance
                if calculated_next_maintenance < today:
                    status = 'overdue'
                elif calculated_next_maintenance <= due_soon_date:
                    status = 'due_soon'
            
            # Apply status filter if provided
            if status_filter and status != status_filter:
                continue
            
            # Get machine and site info
            machine_name = part.machine.name if part.machine else 'Unknown'
            machine_id = part.machine.id if part.machine else None
            machine_serial = part.machine.serial_number if part.machine and hasattr(part.machine, 'serial_number') else ''
            machine_cycle_count = part.machine.cycle_count if part.machine and hasattr(part.machine, 'cycle_count') else 0
            site_name = part.machine.site.name if part.machine and part.machine.site else ''
            site_id = part.machine.site.id if part.machine and part.machine.site else None
            
            # Calculate days overdue or days until due (using calculated next maintenance)
            days_diff = (calculated_next_maintenance - today).days
            
            # Build task name, avoiding duplication of machine name
            task_name = part.name
            if part.description and part.description != part.name:
                # Only add description if it's different from part name
                task_name = f"{part.name} - {part.description}"
            
            # Build frequency display
            frequency_display = None
            if is_cycle_based:
                cycle_freq = getattr(part, 'maintenance_cycle_frequency', None) or part.maintenance_frequency
                frequency_display = f"Every {cycle_freq} cycles"
            elif part.maintenance_frequency:
                frequency_display = f"{part.maintenance_frequency} {part.maintenance_unit}"
            
            # Use calculated values for display
            last_maint_display = latest_record.date.strftime('%Y-%m-%d') if latest_record.date else None
            next_maint_display = calculated_next_maintenance.strftime('%Y-%m-%d')
            
            task_dict = {
                'id': part.id,
                'part_name': part.name,
                'machine': machine_name,
                'machine_name': machine_name,
                'machine_id': machine_id,
                'machine_serial': machine_serial,
                'machine_cycle_count': machine_cycle_count,
                'task': task_name,
                'dueDate': next_maint_display,
                'next_maintenance': next_maint_display,
                'status': status,
                'is_cycle_based': is_cycle_based,
                'assignedTo': '',  # Can be added from maintenance records if needed
                'site': site_name,
                'site_name': site_name,
                'site_id': site_id,
                'priority': 'high' if status == 'overdue' else 'medium' if status == 'due_soon' else 'low',
                'lastMaintenance': last_maint_display,
                'frequency': frequency_display,
            }
            
            # Add cycle-specific info for cycle-based parts
            if is_cycle_based:
                cycle_freq = getattr(part, 'maintenance_cycle_frequency', None) or part.maintenance_frequency
                task_dict['cycle_frequency'] = cycle_freq
                task_dict['next_cycle'] = getattr(part, 'next_maintenance_cycle', None)
                task_dict['last_cycle'] = getattr(part, 'last_maintenance_cycle', 0)
                cycles_remaining = (task_dict['next_cycle'] or 0) - machine_cycle_count
                task_dict['cycles_remaining'] = cycles_remaining  # Can be negative if overdue
                task_dict['cycles_overdue'] = abs(min(0, cycles_remaining))
            else:
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
    """Get detailed information for a part plus recent maintenance history"""
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
        
        history_limit = request.args.get('history_limit', 10)
        try:
            history_limit = max(1, min(100, int(history_limit)))
        except (TypeError, ValueError):
            history_limit = 10

        history_query = MaintenanceRecord.query.options(
            joinedload(MaintenanceRecord.user)
        ).filter_by(part_id=part_id).order_by(MaintenanceRecord.date.desc())

        history_records = history_query.limit(history_limit).all()
        last_record = history_records[0] if history_records else None
        
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
            maintenance_type = last_record.maintenance_type or 'Scheduled'
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
        
        history_payload = []
        for record in history_records:
            history_payload.append({
                'id': record.id,
                'date': record.date.isoformat() if record.date else None,
                'performed_by': record.performed_by or (record.user.username if record.user else ''),
                'maintenance_type': record.maintenance_type or 'Scheduled',
                'description': record.description or '',
                'notes': record.notes or record.comments or '',
                'status': record.status or 'completed',
            })

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
            'history': history_payload,
            'history_limit': history_limit,
            'history_total': history_query.count(),
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
            'maintenanceType': record.maintenance_type or 'Scheduled',
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
    """Get list of completed maintenance records with pagination and filters
    
    Query parameters:
    - site_id: Filter by site ID (or "all" for every site)
    - machine_id: Filter by machine ID
    - part_id: Filter by part ID
    - search: Search in machine name, part name, notes, description, performed_by
    - page: 1-based page number (default 1)
    - page_size: Records per page (default 25, max 100)
    """
    try:
        if not _has_any_permission('maintenance.view', 'maintenance.record', 'maintenance.complete'):
            return api_response(error='Insufficient permissions', status=403)
        from models import MaintenanceRecord, Machine, Part
        from sqlalchemy.orm import joinedload
        from sqlalchemy import or_, func
        
        # Query parameters & pagination guards
        site_id_filter = request.args.get('site_id', None)
        search_query = (request.args.get('search', '') or '').strip()
        machine_id_filter = request.args.get('machine_id', type=int)
        part_id_filter = request.args.get('part_id', type=int)
        page = request.args.get('page', 1, type=int) or 1
        page_size = request.args.get('page_size', 25, type=int) or 25
        page = max(page, 1)
        page_size = max(1, min(page_size, 100))
        search_pattern = f"%{search_query.lower()}%" if search_query else None
        
        # Build query with eager loading to avoid N+1 queries
        query = MaintenanceRecord.query.options(
            joinedload(MaintenanceRecord.machine).joinedload(Machine.site),
            joinedload(MaintenanceRecord.part),
            joinedload(MaintenanceRecord.user)
        )
        joined_machine = False
        joined_part = False
        
        # Apply explicit filters
        if machine_id_filter:
            query = query.filter(MaintenanceRecord.machine_id == machine_id_filter)
        if part_id_filter:
            query = query.filter(MaintenanceRecord.part_id == part_id_filter)
        
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
                return api_response(data={'records': [], 'pagination': {'page': page, 'page_size': page_size, 'total_records': 0, 'total_pages': 0}})
            if not joined_machine:
                query = query.join(MaintenanceRecord.machine)
                joined_machine = True
            query = query.filter(Machine.site_id.in_(allowed_site_ids))
        
        # Search filter
        if search_pattern:
            if not joined_machine:
                query = query.outerjoin(MaintenanceRecord.machine)
                joined_machine = True
            if not joined_part:
                query = query.outerjoin(MaintenanceRecord.part)
                joined_part = True
            query = query.filter(or_(
                func.lower(func.coalesce(Machine.name, '')).like(search_pattern),
                func.lower(func.coalesce(Part.name, '')).like(search_pattern),
                func.lower(func.coalesce(MaintenanceRecord.notes, '')).like(search_pattern),
                func.lower(func.coalesce(MaintenanceRecord.description, '')).like(search_pattern),
                func.lower(func.coalesce(MaintenanceRecord.comments, '')).like(search_pattern),
                func.lower(func.coalesce(MaintenanceRecord.performed_by, '')).like(search_pattern),
                func.lower(func.coalesce(MaintenanceRecord.po_number, '')).like(search_pattern),
                func.lower(func.coalesce(MaintenanceRecord.work_order_number, '')).like(search_pattern),
            ))

        total_records = query.count()
        paginated_query = query.order_by(MaintenanceRecord.date.desc())
        records = paginated_query.offset((page - 1) * page_size).limit(page_size).all()
        
        # Build response data
        records_data = []
        for record in records:
            machine_name = record.machine.name if record.machine else 'Unknown'
            machine_id = record.machine.id if record.machine else None
            machine_serial = record.machine.serial_number if record.machine and hasattr(record.machine, 'serial_number') else ''
            part_name = record.part.name if hasattr(record, 'part') and record.part else 'Unknown'
            part_id = record.part.id if hasattr(record, 'part') and record.part else None
            site_name = record.machine.site.name if record.machine and record.machine.site else ''
            site_id = record.machine.site.id if record.machine and record.machine.site else None
            
            completed_by = record.performed_by or ''
            # Try to decrypt if it looks encrypted
            completed_by = maybe_decrypt(completed_by)
            
            if not completed_by and record.user:
                # Use maybe_decrypt on the user's raw username field
                completed_by = maybe_decrypt(record.user._username)
            
            records_data.append({
                'id': record.id,
                'machine': machine_name,
                'machineName': machine_name,
                'machine_id': machine_id,
                'machine_serial': machine_serial,
                'part': part_name,
                'partName': part_name,
                'part_id': part_id,
                'completedDate': record.date.strftime('%Y-%m-%d') if record.date else '',
                'completedBy': completed_by,
                'site': site_name,
                'siteName': site_name,
                'site_id': site_id,
                'notes': record.notes or record.description or record.comments or '',
                'maintenanceType': record.maintenance_type or 'Scheduled',
                'status': record.status or 'completed',
            })
        
        total_pages = math.ceil(total_records / page_size) if total_records else 0
        payload = {
            'records': records_data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_records': total_records,
                'total_pages': total_pages,
            }
        }
        logger.info(
            'Returning %s maintenance history records (page=%s, page_size=%s, site_filter=%s, search=%s)',
            len(records_data),
            page,
            page_size,
            site_id_filter,
            search_query,
        )
        return api_response(data=payload)
        
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

@api_v1.route('/parts', methods=['POST'])
@api_login_required
def api_create_part():
    """Create a new service/part for a machine"""
    try:
        if not _has_any_permission('machines.edit', 'admin.full'):
            return api_response(error='Insufficient permissions', status=403)
        
        from models import Part, Machine, db
        from sync_utils_enhanced import add_to_sync_queue_enhanced
        
        data = request.form
        machine_id = data.get('machine_id')
        name = data.get('name')
        
        if not machine_id or not name:
            return api_response(error='Machine ID and Name are required', status=400)
            
        machine = Machine.query.get(machine_id)
        if not machine:
            return api_response(error='Machine not found', status=404)
            
        if not _has_site_access(machine.site_id):
            return api_response(error='Access denied', status=403)
            
        part = Part(
            name=name,
            machine_id=machine_id,
            description=data.get('description', ''),
            maintenance_frequency=data.get('maintenance_frequency', type=int),
            maintenance_unit=data.get('maintenance_unit', 'days'),
            next_maintenance=datetime.strptime(data.get('next_maintenance'), '%Y-%m-%d') if data.get('next_maintenance') else None
            # assigned_user_id is available in model but maybe not used here?
        )
        
        db.session.add(part)
        db.session.commit()
        
        # Add to sync queue
        add_to_sync_queue_enhanced('parts', part.id, 'INSERT', part.to_dict())
        
        return api_response(message='Service created successfully', data={'id': part.id})
        
    except Exception as e:
        logger.error(f'Create part error: {str(e)}')
        db.session.rollback()
        return api_response(error=f'Failed to create service: {str(e)}', status=500)

@api_v1.route('/parts/<int:part_id>', methods=['POST'])
@api_login_required
def api_update_part(part_id):
    """Update an existing service/part"""
    try:
        if not _has_any_permission('machines.edit', 'admin.full'):
            return api_response(error='Insufficient permissions', status=403)
            
        from models import Part, db
        from sync_utils_enhanced import add_to_sync_queue_enhanced
        
        part = Part.query.get_or_404(part_id)
        
        # specific permission check if needed (e.g. site access via part.machine)
        if part.machine and not _has_site_access(part.machine.site_id):
            return api_response(error='Access denied', status=403)
            
        data = request.form
        
        part.name = data.get('name', part.name)
        part.description = data.get('description', part.description)
        
        if 'maintenance_frequency' in data:
            freq = data.get('maintenance_frequency')
            part.maintenance_frequency = int(freq) if freq else None
            
        if 'maintenance_unit' in data:
            part.maintenance_unit = data.get('maintenance_unit')
            
        if 'next_maintenance' in data:
            nm = data.get('next_maintenance')
            part.next_maintenance = datetime.strptime(nm, '%Y-%m-%d') if nm else None
            
        db.session.commit()
        
        # Add to sync queue
        add_to_sync_queue_enhanced('parts', part.id, 'UPDATE', part.to_dict())
        
        return api_response(message='Service updated successfully')
        
    except Exception as e:
        logger.error(f'Update part error: {str(e)}')
        db.session.rollback()
        return api_response(error=f'Failed to update service: {str(e)}', status=500)

@api_v1.route('/parts/<int:part_id>/delete', methods=['POST'])
@api_login_required
def api_delete_part(part_id):
    """Delete a service/part"""
    try:
        if not _has_any_permission('machines.edit', 'admin.full'):
            return api_response(error='Insufficient permissions', status=403)
            
        from models import Part, db
        from sync_utils_enhanced import add_to_sync_queue_enhanced
        
        part = Part.query.get_or_404(part_id)
        
        if part.machine and not _has_site_access(part.machine.site_id):
            return api_response(error='Access denied', status=403)
            
        # Capture ID before deletion
        p_id = part.id
        
        db.session.delete(part)
        db.session.commit()
        
        # Add to sync queue
        add_to_sync_queue_enhanced('parts', p_id, 'DELETE', {})
        
        return api_response(message='Service deleted successfully')
        
    except Exception as e:
        logger.error(f'Delete part error: {str(e)}')
        db.session.rollback()
        return api_response(error=f'Failed to delete service: {str(e)}', status=500)

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
        maintenance_type = data.get('type', 'Scheduled')
        description = data.get('description', '')
        notes = data.get('notes', '')
        po_number = (data.get('po_number') or '').strip()
        work_order_number = (data.get('work_order_number') or '').strip()
        
        if not part_ids or not machine_id:
            return api_response(error='Machine ID and at least one part required', status=400)
        if not po_number or not work_order_number:
            return api_response(error='PO Number and Work Order Number are required.', status=400)
        if len(po_number) > 32:
            return api_response(error='PO Number must be 32 characters or fewer.', status=400)
        if len(work_order_number) > 128:
            return api_response(error='Work Order Number must be 128 characters or fewer.', status=400)

        try:
            completion_date = datetime.strptime(maintenance_date, '%Y-%m-%d').date()
        except ValueError:
            return api_response(error='Invalid date format. Use YYYY-MM-DD.', status=400)
        
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
                date=completion_date,
                performed_by=current_user.username if hasattr(current_user, 'username') else 'Unknown',
                status='completed',
                notes=notes,
                po_number=po_number,
                work_order_number=work_order_number
            )
            db.session.add(maintenance_record)
            
            part.update_next_maintenance(completion_date)
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
                'notes': record.notes,
                'po_number': record.po_number,
                'work_order_number': record.work_order_number
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

@api_v1.route('/maintenance/request', methods=['POST'])
@api_login_required
def api_request_maintenance():
    """Request emergency maintenance via email"""
    try:
        from models import Machine, Part, Site
        
        data = request.get_json()
        machine_id = data.get('machine_id')
        service_ids = data.get('part_ids', [])
        description = data.get('description', '')
        # notes often contains the "details"
        notes = data.get('notes', '')
        
        if not machine_id:
            return api_response(error='Machine ID required', status=400)

        machine = Machine.query.get_or_404(machine_id)
        site = machine.site or Site.query.get(machine.site_id)
        site_name = site.name if site else 'Unknown Site'
        
        services = []
        if service_ids:
            services = Part.query.filter(Part.id.in_(service_ids)).all()
        service_names = [s.name for s in services]
        
        # Construct email body
        subject = f"URGENT: Emergency Maintenance Request - {site_name} - {machine.name}"
        body = f"""
EMERGENCY MAINTENANCE REQUEST

Site: {site_name}
Machine: {machine.name} (ID: {machine_id})
Requested By: {current_user.username} ({current_user.email})
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Services/Parts Affected:
{', '.join(service_names) if service_names else 'General/Unknown'}

Description:
{description}

Notes:
{notes}

Please schedule maintenance immediately.
"""
        
        # Mock sending email (Log to console/file)
        # in a real app: send_email('maintenance@accuratemachinerepair.com', subject, body)
        logger.warning(f"--- MOCK EMAIL SENT ---\nTo: maintenance@accuratemachinerepair.com\nSubject: {subject}\n{body}\n-----------------------")
        
        return api_response(message='Emergency maintenance request sent successfully')
        
    except Exception as e:
        logger.error(f'Request maintenance error: {str(e)}', exc_info=True)
        return api_response(error='Failed to send maintenance request', status=500)

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

@api_v1.route('/sites/<int:site_id>/machines', methods=['GET'])
@api_login_required
def api_get_site_machines(site_id):
    """Get list of machines for a specific site"""
    try:
        from models import Machine
        
        # Check permissions
        if not _has_site_access(site_id):
            return api_response(error='Access denied', status=403)
            
        machines = Machine.query.filter_by(site_id=site_id, decommissioned=False).all()
        
        machines_data = []
        for m in machines:
            machines_data.append({
                'id': m.id,
                'name': m.name,
                'site_id': m.site_id,
                'serial_number': m.serial_number if hasattr(m, 'serial_number') else '',
                'make': m.make if hasattr(m, 'make') else '',
                'model': m.model if hasattr(m, 'model') else '',
                'location': m.location if hasattr(m, 'location') else ''
            })
            
        return api_response(data=machines_data)
        
    except Exception as e:
        logger.error(f'Get site machines error: {str(e)}')
        return api_response(error='Failed to load machines', status=500)

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
        
        # Use Eastern timezone for consistent date boundaries with audit completions
        from timezone_utils import get_eastern_date
        today = get_eastern_date()
        
        audits_data = []
        for task in audit_tasks:
            # Get completion stats
            total_machines = len(task.machines) if hasattr(task, 'machines') else 0
            completed_today = AuditTaskCompletion.query.filter_by(
                audit_task_id=task.id,
                date=today,
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
        from timezone_utils import get_eastern_date
        
        audit_task = AuditTask.query.get_or_404(audit_id)
        
        if not _has_site_access(audit_task.site_id):
            return api_response(error='Access denied', status=403)
        
        # Use Eastern timezone for consistent date boundaries with audit completions
        today = get_eastern_date()
        
        # Get date range from query params
        date_from_str = request.args.get('date_from')
        date_to_str = request.args.get('date_to')
        grouped_by_date = request.args.get('grouped_by_date', '0') == '1'
        
        start_date = today
        end_date = today
        
        if date_from_str:
            try:
                start_date = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        if date_to_str:
            try:
                end_date = datetime.strptime(date_to_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        if grouped_by_date:
            # Fetch all completions in range
            completions = AuditTaskCompletion.query.filter(
                AuditTaskCompletion.audit_task_id == audit_id,
                AuditTaskCompletion.date >= start_date,
                AuditTaskCompletion.date <= end_date,
                AuditTaskCompletion.completed == True
            ).all()
            
            # Map by (date, machine_id)
            completion_map = {}
            user_ids = set()
            for c in completions:
                completion_map[(c.date, c.machine_id)] = c
                if c.completed_by:
                    user_ids.add(c.completed_by)
            
            # Fetch users
            users = {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}
            
            daily_results = []
            current_date = start_date
            while current_date <= end_date:
                day_machines = []
                for machine in audit_task.machines:
                    completion = completion_map.get((current_date, machine.id))
                    
                    completed_by_name = None
                    if completion and completion.completed_by:
                        user = users.get(completion.completed_by)
                        if user:
                            completed_by_name = maybe_decrypt(user._username)
                            
                    day_machines.append({
                        'id': machine.id,
                        'name': machine.name,
                        'model': machine.model if hasattr(machine, 'model') else '',
                        'serial_number': machine.serial_number if hasattr(machine, 'serial_number') else '',
                        'completed': completion.completed if completion else False,
                        'completed_at': completion.completed_at.isoformat() if completion and completion.completed_at else None,
                        'completed_by': completed_by_name,
                        'completed_by_id': completion.completed_by if completion else None,
                    })
                
                daily_results.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'machines': day_machines
                })
                current_date += timedelta(days=1)
                
            return api_response(data=daily_results)
        
        machines_data = []
        
        for machine in audit_task.machines:
            # Check if completed in range (get latest completion)
            completion = AuditTaskCompletion.query.filter(
                AuditTaskCompletion.audit_task_id == audit_id,
                AuditTaskCompletion.machine_id == machine.id,
                AuditTaskCompletion.date >= start_date,
                AuditTaskCompletion.date <= end_date,
                AuditTaskCompletion.completed == True
            ).order_by(AuditTaskCompletion.date.desc()).first()
            
            # Resolve completed_by user name
            completed_by_name = None
            if completion and completion.completed_by:
                user = User.query.get(completion.completed_by)
                if user:
                    # Use maybe_decrypt on the user's raw username field
                    completed_by_name = maybe_decrypt(user._username)

            machines_data.append({
                'id': machine.id,
                'name': machine.name,
                'model': machine.model if hasattr(machine, 'model') else '',
                'serial_number': machine.serial_number if hasattr(machine, 'serial_number') else '',
                'completed': completion.completed if completion else False,
                'completed_at': completion.completed_at.isoformat() if completion and completion.completed_at else None,
                'completed_by': completed_by_name,
                'completed_by_id': completion.completed_by if completion else None,
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
    
    # Check for permissions using both backend (dot) and frontend (underscore) conventions
    if not _has_any_permission('audits.edit', 'audits.create', 'edit_audits', 'complete_audits'):
        return api_response(error='Insufficient permissions', status=403)
    
    # Move imports outside try block to see import errors
    from models import AuditTask, AuditTaskCompletion, Machine
    from sync_utils_enhanced import add_to_sync_queue_enhanced
    from timezone_utils import get_timezone_aware_now, get_eastern_date
    
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
        
        # Use Eastern timezone for consistent date boundaries with audit completions
        today = get_eastern_date()
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
                # Use maybe_decrypt on the raw fields directly to be safe
                username = maybe_decrypt(user._username)
                # If maybe_decrypt returns the same encrypted-looking string, try to force it
                if username and username.startswith('gAAAAA'):
                    # This shouldn't happen with the updated maybe_decrypt, but just in case
                    pass
            except Exception as e:
                logger.error(f'Failed to decrypt username for user {user.id}: {str(e)}', exc_info=True)
                username = f'user_{user.id}'  # Fallback
            
            try:
                email = maybe_decrypt(user._email)
            except Exception as e:
                logger.error(f'Failed to decrypt email for user {user.id}: {str(e)}', exc_info=True)
                email = f'user_{user.id}@example.com'  # Fallback
            
            users_data.append({
                'id': user.id,
                'username': username,
                'email': email,
                'full_name': user.full_name if hasattr(user, 'full_name') else '',
                'role': role.name if role and hasattr(role, 'name') else (role if isinstance(role, str) else 'User'),
                'role_id': user.role_id if hasattr(user, 'role_id') else None,
                'is_admin': user.is_admin if hasattr(user, 'is_admin') else False,
                'assigned_sites': [s.id for s in user.sites] if hasattr(user, 'sites') else [],
                'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
            })
        
        return api_response(data=users_data)
        
    except Exception as e:
        logger.error(f'Get users error: {str(e)}')
        return api_response(error='Failed to load users', status=500)

@api_v1.route('/users/<int:user_id>', methods=['PUT'])
@api_login_required
def api_update_user(user_id):
    """Update user details, role, and assigned sites"""
    try:
        from models import Role, Site
        from security_event_logger import log_security_event

        if not _is_admin_user():
            return api_response(error='Admin access required', status=403)

        user = User.query.get(user_id)
        if not user:
            return api_response(error='User not found', status=404)

        data = request.get_json()
        
        # Check uniqueness if username/email changed
        if 'username' in data and data['username'] != maybe_decrypt(user._username):
            existing = User.query.filter_by(username_hash=hash_value(data['username'])).first()
            if existing:
                return api_response(error='Username already taken', status=400)
            user.username = data['username']
            
        if 'email' in data and data['email'] != maybe_decrypt(user._email):
             # Basic check, though hash might not match due to salt if implemented differently
             # For now relying on unique constraint catch or hash check
             # But here we just update if provided
             user.email = data['email']

        if 'full_name' in data:
            user.full_name = data['full_name']
            
        # Role update
        if 'role_id' in data:
            role_id = data['role_id']
            if role_id:
                role = Role.query.get(role_id)
                if role:
                    user.role = role
                else:
                    return api_response(error='Role not found', status=400)
            else:
                user.role = None
                
        # Site assignment (Task #46)
        if 'site_ids' in data:
            site_ids = data['site_ids']
            # Clear current sites
            user.sites = []
            if site_ids:
                sites = Site.query.filter(Site.id.in_(site_ids)).all()
                user.sites = sites
        
        # Admin status
        if 'is_admin' in data:
            user.is_admin = bool(data['is_admin'])

        db.session.commit()
        
        # Log event
        log_security_event(
            event_type="admin_user_edit",
            details=f"User {user_id} updated via API by {current_user.username}",
            is_critical=True
        )
        
        # Sync updates
        # 1. User record
        add_to_sync_queue_enhanced('users', user.id, 'update', {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'role_id': user.role_id,
            'is_admin': user.is_admin
        })
        
        # 2. Site associations 
        # (This is tricky with sync, but we send individual associations)
        #Ideally we sync the whole set, but current sync might expect single rows
        for site in user.sites:
            add_to_sync_queue_enhanced('user_sites', f'{user.id}_{site.id}', 'update', {
                'user_id': user.id,
                'site_id': site.id
            })

        return api_response(message='User updated successfully')

    except Exception as e:
        db.session.rollback()
        logger.error(f'Update user error: {str(e)}', exc_info=True)
        return api_response(error=f'Failed to update user: {str(e)}', status=500)

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
