import os
import json
import logging
import sqlite3
from flask import Blueprint, request, jsonify, current_app, g
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
offline_bp = Blueprint('offline', __name__)

# SQLite database path
def get_db_path():
    """Get the path to the local SQLite database"""
    if os.environ.get('APPDATA'):
        # Windows
        base_dir = os.environ.get('APPDATA')
    else:
        # macOS/Linux
        base_dir = os.path.expanduser('~/.config')
    
    app_data_dir = os.path.join(base_dir, 'AMRS-Maintenance-Tracker')
    os.makedirs(app_data_dir, exist_ok=True)
    
    return os.path.join(app_data_dir, 'maintenance.db')

# Database helpers
def get_db():
    """Get SQLite database connection"""
    if 'db' not in g:
        g.db = sqlite3.connect(get_db_path())
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Close SQLite database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Register teardown function
@offline_bp.teardown_app_request
def teardown_db(exception):
    close_db()

# Offline API routes
@offline_bp.route('/api/offline/status', methods=['GET'])
def offline_status():
    """Check offline mode status"""
    db_path = get_db_path()
    db_exists = os.path.exists(db_path)
    
    # Check if we have sync information
    sync_info_path = os.path.join(os.path.dirname(db_path), 'last_sync.txt')
    last_sync = None
    
    if os.path.exists(sync_info_path):
        with open(sync_info_path, 'r') as f:
            last_sync = f.read().strip()
    
    return jsonify({
        'offline_ready': db_exists,
        'last_sync': last_sync,
        'db_path': db_path
    })

@offline_bp.route('/api/offline/tables', methods=['GET'])
def get_tables():
    """Get list of available tables in the local database"""
    db = get_db()
    cursor = db.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Get row count for each table
    table_info = []
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        table_info.append({
            'name': table,
            'row_count': count
        })
    
    return jsonify({
        'tables': table_info
    })

@offline_bp.route('/api/offline/data/<table>', methods=['GET'])
def get_table_data(table):
    """Get data from a specific table"""
    # Basic query parameters
    limit = request.args.get('limit', 1000, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    db = get_db()
    cursor = db.cursor()
    
    # Verify table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    if not cursor.fetchone():
        return jsonify({
            'error': f"Table '{table}' does not exist"
        }), 404
    
    # Get column info
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Get data with pagination
    cursor.execute(f"SELECT * FROM {table} LIMIT ? OFFSET ?", (limit, offset))
    rows = cursor.fetchall()
    
    # Convert to list of dictionaries
    data = []
    for row in rows:
        row_dict = {}
        for i, column in enumerate(columns):
            row_dict[column] = row[i]
        data.append(row_dict)
    
    # Get total count
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    total = cursor.fetchone()[0]
    
    return jsonify({
        'table': table,
        'columns': columns,
        'count': total,
        'data': data,
        'limit': limit,
        'offset': offset
    })

@offline_bp.route('/api/offline/query', methods=['POST'])
def run_query():
    """Run a custom query against the local database"""
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({
            'error': "Missing 'query' parameter"
        }), 400
    
    query = data['query']
    params = data.get('params', [])
    
    # Basic SQL injection protection - only allow SELECT queries
    if not query.strip().upper().startswith('SELECT'):
        return jsonify({
            'error': "Only SELECT queries are allowed"
        }), 403
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        results = []
        for row in rows:
            row_dict = {}
            for i, column in enumerate(columns):
                row_dict[column] = row[i]
            results.append(row_dict)
        
        return jsonify({
            'columns': columns,
            'count': len(results),
            'data': results
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

def register_offline_blueprint(app):
    """Register the offline blueprint with a Flask app"""
    app.register_blueprint(offline_bp)
    app.teardown_appcontext(close_db)
    logger.info("Offline support registered with Flask app")
    return app
