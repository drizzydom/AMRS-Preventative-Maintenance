import os
import jwt
import json
import datetime
import logging
from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint for API and sync functionality
api_bp = Blueprint('api', __name__)

# JWT Secret Key - in production, use a secure environment variable
JWT_SECRET = os.environ.get('JWT_SECRET', 'your_super_secure_jwt_secret_key')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = 24 * 7  # 7 days token validity for offline access

# =====================
# Authentication functions
# =====================

def generate_token(user_id, username, role='user'):
    """Generate a JWT token for authentication"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRY_HOURS),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token):
    """Decode and validate a JWT token"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise ValueError("Expired token")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")

def token_required(f):
    """Decorator to protect API routes with JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split('Bearer ')[1]
            
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
            
        try:
            # Decode and validate token
            payload = decode_token(token)
            # Add user info to request context
            request.user = payload
        except Exception as e:
            return jsonify({'message': f'Invalid token: {str(e)}'}), 401
            
        return f(*args, **kwargs)
    return decorated

# =====================
# Database sync endpoints
# =====================

@api_bp.route('/api/v1/sync/validate-token', methods=['GET'])
@token_required
def validate_token():
    """Endpoint to validate token and return user info"""
    return jsonify({
        'valid': True,
        'user': {
            'user_id': request.user['user_id'],
            'username': request.user['username'],
            'role': request.user['role']
        },
        'expires': request.user['exp']
    })

@api_bp.route('/api/v1/sync/schema/<table>', methods=['GET'])
@token_required
def get_table_schema(table):
    """Get schema for a specific table"""
    # Verify user has access to this table
    if not has_table_access(request.user, table):
        return jsonify({'message': 'Access denied to this table'}), 403
    
    try:
        db = current_app.extensions.get('sqlalchemy').db
        inspector = inspect(db.engine)
        
        # Verify table exists
        if table not in inspector.get_table_names():
            return jsonify({'message': f'Table {table} does not exist'}), 404
            
        # Get column information
        columns = inspector.get_columns(table)
        column_defs = []
        
        for column in columns:
            col_def = {
                'name': column['name'],
                'type': str(column['type']),
                'nullable': column.get('nullable', True),
                'primary_key': column.get('primary_key', False)
            }
            column_defs.append(col_def)
            
        # Generate SQLite create table statement
        create_sql = generate_sqlite_create_statement(table, columns)
            
        return jsonify({
            'table': table,
            'columns': column_defs,
            'create_sql': create_sql
        })
    except Exception as e:
        logger.error(f"Error getting schema for {table}: {str(e)}")
        return jsonify({'message': f'Error: {str(e)}'}), 500

@api_bp.route('/api/v1/sync/data/<table>', methods=['GET'])
@token_required
def get_table_data(table):
    """Get data for a specific table"""
    # Verify user has access to this table
    if not has_table_access(request.user, table):
        return jsonify({'message': 'Access denied to this table'}), 403
        
    try:
        # Get query parameters
        since = request.args.get('since')  # For incremental sync
        limit = request.args.get('limit', 1000)
        offset = request.args.get('offset', 0)
        
        db = current_app.extensions.get('sqlalchemy').db
        
        # Build query
        query = f"SELECT * FROM {table}"
        
        # Add incremental sync condition if 'since' parameter is provided
        if since and has_updated_at_column(db, table):
            query += f" WHERE updated_at >= '{since}'"
            
        # Add pagination
        query += f" LIMIT {limit} OFFSET {offset}"
        
        # Execute query
        result = db.session.execute(text(query))
        
        # Convert to list of dictionaries
        columns = result.keys()
        rows = []
        
        for row in result:
            row_dict = {}
            for i, column in enumerate(columns):
                # Handle different data types for JSON serialization
                value = row[i]
                if isinstance(value, datetime.datetime):
                    row_dict[column] = value.isoformat()
                elif isinstance(value, datetime.date):
                    row_dict[column] = value.isoformat()
                else:
                    row_dict[column] = value
            rows.append(row_dict)
            
        # Get total count
        count_query = f"SELECT COUNT(*) FROM {table}"
        if since and has_updated_at_column(db, table):
            count_query += f" WHERE updated_at >= '{since}'"
            
        count_result = db.session.execute(text(count_query)).scalar()
            
        return jsonify({
            'table': table,
            'total_count': count_result,
            'returned_count': len(rows),
            'offset': offset,
            'limit': limit,
            'data': rows
        })
    except Exception as e:
        logger.error(f"Error getting data for {table}: {str(e)}")
        return jsonify({'message': f'Error: {str(e)}'}), 500

@api_bp.route('/api/v1/sync', methods=['POST'])
@token_required
def sync_all_data():
    """Endpoint to trigger full database sync"""
    user = request.user
    data = request.get_json()
    force_sync = data.get('forceSync', False)
    
    try:
        db = current_app.extensions.get('sqlalchemy').db
        inspector = inspect(db.engine)
        
        # Get all tables
        all_tables = inspector.get_table_names()
        
        # Filter tables user has access to
        accessible_tables = [table for table in all_tables if has_table_access(user, table)]
        
        result = {
            'success': True,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'tables': [],
            'message': 'Database sync information prepared'
        }
        
        for table in accessible_tables:
            # Skip system tables
            if table.startswith('sqlite_') or table.startswith('pg_') or table == 'alembic_version':
                continue
                
            # Get row count
            count_query = f"SELECT COUNT(*) FROM {table}"
            count = db.session.execute(text(count_query)).scalar()
            
            result['tables'].append({
                'name': table,
                'row_count': count,
                'sync_url': f"/api/v1/sync/data/{table}"
            })
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error preparing sync: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

# =====================
# Helper functions
# =====================

def has_table_access(user, table):
    """Check if user has access to a specific table"""
    # Admin can access all tables
    if user.get('role') == 'admin':
        return True
        
    # Basic implementation - can be extended with more complex rules
    restricted_tables = ['users', 'roles', 'permissions']
    
    # Regular users can't access certain tables
    if user.get('role') == 'user' and table in restricted_tables:
        return False
        
    return True

def has_updated_at_column(db, table):
    """Check if a table has an updated_at column"""
    inspector = inspect(db.engine)
    columns = inspector.get_columns(table)
    return any(col['name'] == 'updated_at' for col in columns)

def generate_sqlite_create_statement(table, columns):
    """Generate a SQLite CREATE TABLE statement from column definitions"""
    col_defs = []
    pk_cols = []
    
    for col in columns:
        col_name = col['name']
        col_type = map_pg_to_sqlite_type(col['type'])
        
        col_def = f"{col_name} {col_type}"
        
        if col.get('primary_key'):
            pk_cols.append(col_name)
        elif not col.get('nullable', True):
            col_def += " NOT NULL"
            
        if col.get('default') is not None:
            default_val = col['default']
            if isinstance(default_val, str):
                default_val = f"'{default_val}'"
            col_def += f" DEFAULT {default_val}"
            
        col_defs.append(col_def)
        
    # Add primary key constraint
    if pk_cols:
        col_defs.append(f"PRIMARY KEY ({', '.join(pk_cols)})")
        
    create_stmt = f"CREATE TABLE IF NOT EXISTS {table} (\n  " + ",\n  ".join(col_defs) + "\n)"
    return create_stmt

def map_pg_to_sqlite_type(pg_type):
    """Map PostgreSQL data types to SQLite types"""
    pg_type = str(pg_type).lower()
    
    # Basic type mapping
    if 'int' in pg_type:
        return 'INTEGER'
    elif 'varchar' in pg_type or 'text' in pg_type or 'char' in pg_type:
        return 'TEXT'
    elif 'float' in pg_type or 'double' in pg_type or 'real' in pg_type or 'decimal' in pg_type:
        return 'REAL'
    elif 'bool' in pg_type:
        return 'INTEGER'
    elif 'date' in pg_type or 'time' in pg_type:
        return 'TEXT'
    elif 'json' in pg_type or 'jsonb' in pg_type:
        return 'TEXT'
    elif 'uuid' in pg_type:
        return 'TEXT'
    else:
        return 'TEXT'  # Default to TEXT for unknown types

def register_api_blueprint(app):
    """Register the API blueprint with a Flask app"""
    app.register_blueprint(api_bp)
    logger.info("API/Sync blueprint registered with Flask app")
    return app
