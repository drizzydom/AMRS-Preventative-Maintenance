# Additional API endpoints for offline sync support
from flask import jsonify, request, abort
from flask_login import current_user, login_required
from functools import wraps
import datetime
import jwt
from app import app, db
from models import User, Site, Machine, Part, MaintenanceRecord, Role

# These endpoints should be added to your main Flask application

# Secret key for JWT tokens
JWT_SECRET_KEY = app.config.get('SECRET_KEY')

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
            user = User.query.get(data['user_id'])
            if not user:
                return jsonify({'error': 'Invalid user'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(user, *args, **kwargs)
    return decorated

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """API endpoint for user login, returns JWT token"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400
    
    user = User.query.filter_by(username=data.get('username')).first()
    
    if user and user.check_password(data.get('password')):
        # Generate token with user id, role and expiration
        token_payload = {
            'user_id': user.id,
            'role_id': user.role_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=TOKEN_EXPIRE_MINUTES)
        }
        
        token = jwt.encode(token_payload, JWT_SECRET_KEY, algorithm='HS256')
        
        return jsonify({
            'token': token,
            'user_id': user.id,
            'username': user.username,
            'role_id': user.role_id,
            'exp': TOKEN_EXPIRE_MINUTES
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/auth/refresh-token', methods=['POST'])
def api_refresh_token():
    """API endpoint to refresh an existing token"""
    data = request.get_json()
    
    if not data or not data.get('token'):
        return jsonify({'error': 'Token is required'}), 400
    
    try:
        # Decode token without verifying expiration
        decoded = jwt.decode(
            data.get('token'), 
            JWT_SECRET_KEY, 
            algorithms=['HS256'],
            options={'verify_exp': False}
        )
        
        # Check if user exists
        user = User.query.get(decoded.get('user_id'))
        
        if not user:
            return jsonify({'error': 'Invalid user'}), 401
        
        # Generate new token
        token_payload = {
            'user_id': user.id,
            'role_id': user.role_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=TOKEN_EXPIRE_MINUTES)
        }
        
        new_token = jwt.encode(token_payload, JWT_SECRET_KEY, algorithm='HS256')
        
        return jsonify({
            'token': new_token,
            'exp': TOKEN_EXPIRE_MINUTES
        })
        
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401

@app.route('/api/auth/user-info', methods=['GET'])
@token_required
def api_user_info(user):
    """Get the current user's information"""
    role = Role.query.get(user.role_id)
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email if hasattr(user, 'email') else None,
        'role_id': user.role_id,
        'role_name': role.name if role else None
    })

@app.route('/api/healthcheck', methods=['GET'])
def api_healthcheck():
    """API endpoint to check if the server is running"""
    return jsonify({'status': 'ok'})

@app.route('/api/sync/<string:table_name>', methods=['GET'])
@token_required
def api_sync_get_updates(user, table_name):
    """API endpoint to get updates for a table since a specific time"""
    # Check for valid table names to prevent SQL injection
    allowed_tables = {
        'sites': Site,
        'machines': Machine,
        'parts': Part,
        'maintenance_records': MaintenanceRecord
    }
    
    if table_name not in allowed_tables:
        return jsonify({'error': 'Invalid table name'}), 400
    
    model = allowed_tables[table_name]
    
    # Get the 'since' parameter
    since = request.args.get('since', '1970-01-01T00:00:00.000Z')
    
    try:
        since_date = datetime.datetime.fromisoformat(since.replace('Z', '+00:00'))
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    # Query records updated since the given date
    # This assumes your models have an 'updated_at' column
    query = model.query
    
    # Add role-based filtering if needed
    if user.role_id > 1:  # If not admin
        if table_name == 'sites' and hasattr(model, 'user_id'):
            query = query.filter(model.user_id == user.id)
    
    # Get records updated since the date
    if hasattr(model, 'updated_at'):
        records = query.filter(model.updated_at >= since_date).all()
    else:
        # If no updated_at field, get all records (inefficient but works)
        records = query.all()
    
    # Convert records to dictionaries
    result = []
    for record in records:
        record_dict = {}
        for column in record.__table__.columns:
            value = getattr(record, column.name)
            # Convert dates to ISO format
            if isinstance(value, datetime.datetime):
                value = value.isoformat()
            record_dict[column.name] = value
        result.append(record_dict)
    
    return jsonify({
        'table': table_name,
        'records': result,
        'count': len(result)
    })

@app.route('/api/sync/<string:table_name>', methods=['POST'])
@token_required
def api_sync_update(user, table_name):
    """API endpoint to sync updates from client to server"""
    # Check for valid table names to prevent SQL injection
    allowed_tables = {
        'sites': Site,
        'machines': Machine,
        'parts': Part,
        'maintenance_records': MaintenanceRecord
    }
    
    if table_name not in allowed_tables:
        return jsonify({'error': 'Invalid table name'}), 400
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    model = allowed_tables[table_name]
    
    try:
        action = data.get('action', 'update')
        record_data = data.get('data', {})
        
        if not record_data:
            return jsonify({'error': 'No record data provided'}), 400
        
        # Create new record
        if action == 'create':
            # Remove id if present for new records
            if 'id' in record_data:
                del record_data['id']
                
            # Add user_id for records that need it
            if hasattr(model, 'user_id'):
                record_data['user_id'] = user.id
                
            new_record = model(**record_data)
            db.session.add(new_record)
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': f'New {table_name} record created',
                'id': new_record.id
            })
            
        # Update existing record
        elif action == 'update':
            if 'id' not in record_data:
                return jsonify({'error': 'Record ID is required for updates'}), 400
                
            record = model.query.get(record_data['id'])
            
            if not record:
                return jsonify({'error': f'Record not found with ID {record_data["id"]}'}), 404
                
            # Check permissions if needed
            if hasattr(record, 'user_id') and user.role_id > 1:  # If not admin
                if record.user_id != user.id:
                    return jsonify({'error': 'You do not have permission to update this record'}), 403
            
            # Update record fields
            for key, value in record_data.items():
                if hasattr(record, key) and key != 'id':
                    setattr(record, key, value)
                    
            # Update timestamp if available
            if hasattr(record, 'updated_at'):
                record.updated_at = datetime.datetime.utcnow()
                
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': f'{table_name} record updated'
            })
            
        # Delete existing record
        elif action == 'delete':
            if 'id' not in record_data:
                return jsonify({'error': 'Record ID is required for deletion'}), 400
                
            record = model.query.get(record_data['id'])
            
            if not record:
                return jsonify({'error': f'Record not found with ID {record_data["id"]}'}), 404
                
            # Check permissions if needed
            if hasattr(record, 'user_id') and user.role_id > 1:  # If not admin
                if record.user_id != user.id:
                    return jsonify({'error': 'You do not have permission to delete this record'}), 403
            
            db.session.delete(record)
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': f'{table_name} record deleted'
            })
            
        else:
            return jsonify({'error': f'Invalid action: {action}'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
