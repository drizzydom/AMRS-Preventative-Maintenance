import os
import json
import sqlite3
import logging
import requests
import datetime
from flask import Blueprint, request, jsonify

# Create blueprint
sync_bp = Blueprint('sync', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database paths
def get_db_path():
    """Get the SQLite database path based on platform"""
    if os.environ.get('APPDATA'):
        # Windows
        base_dir = os.environ.get('APPDATA')
    else:
        # macOS/Linux
        base_dir = os.path.expanduser('~/.config')
    
    app_data_dir = os.path.join(base_dir, 'AMRS-Maintenance-Tracker')
    os.makedirs(app_data_dir, exist_ok=True)
    
    return os.path.join(app_data_dir, 'maintenance.db')

def get_config():
    """Load configuration"""
    config_path = os.path.join(os.path.dirname(__file__), 'sync_config.json')
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
    
    # Default config
    return {
        'api_url': 'https://amrs-maintenance.yourdomain.com/api',
        'tables': ['users', 'maintenance_tasks', 'equipment', 'locations']
    }

# Synchronization endpoint
@sync_bp.route('/api/sync', methods=['POST'])
def sync_database():
    """Synchronize remote PostgreSQL database to local SQLite"""
    try:
        data = request.get_json()
        
        if not data or 'token' not in data:
            return jsonify({
                'success': False,
                'message': 'Authentication token is required'
            }), 401
        
        token = data['token']
        force_sync = data.get('forceSync', False)
        
        # Get configuration
        config = get_config()
        api_url = config['api_url']
        
        # Validate token with server
        validate_response = requests.get(
            f"{api_url}/validate-token",
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if validate_response.status_code != 200:
            return jsonify({
                'success': False,
                'message': 'Invalid authentication token'
            }), 401
        
        # Get database path
        db_path = get_db_path()
        logger.info(f"Database path: {db_path}")
        
        # Start synchronization
        sync_results = {}
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        for table in config['tables']:
            # Get table schema from server
            schema_response = requests.get(
                f"{api_url}/schema/{table}",
                headers={'Authorization': f'Bearer {token}'}
            )
            
            if schema_response.status_code == 200:
                schema_data = schema_response.json()
                create_sql = schema_data['create_sql']
                
                # Create table with schema
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}_temp")
                    cursor.execute(create_sql.replace(table, f"{table}_temp"))
                except Exception as e:
                    logger.error(f"Error creating temp table {table}: {e}")
            
            # Get data for table
            data_response = requests.get(
                f"{api_url}/data/{table}",
                headers={'Authorization': f'Bearer {token}'}
            )
            
            if data_response.status_code == 200:
                table_data = data_response.json()
                
                # Insert data into temp table
                rows_inserted = 0
                for row in table_data['data']:
                    cols = ', '.join(row.keys())
                    placeholders = ', '.join(['?' for _ in row.keys()])
                    sql = f"INSERT INTO {table}_temp ({cols}) VALUES ({placeholders})"
                    
                    try:
                        cursor.execute(sql, list(row.values()))
                        rows_inserted += 1
                    except Exception as e:
                        logger.error(f"Error inserting row: {e}")
                
                # Replace original table with temp
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    cursor.execute(f"ALTER TABLE {table}_temp RENAME TO {table}")
                    conn.commit()
                except Exception as e:
                    logger.error(f"Error replacing table: {e}")
                
                sync_results[table] = rows_inserted
        
        conn.close()
        
        # Write sync timestamp
        timestamp = datetime.datetime.now().isoformat()
        sync_file = os.path.join(os.path.dirname(db_path), 'last_sync.txt')
        with open(sync_file, 'w') as f:
            f.write(timestamp)
        
        return jsonify({
            'success': True,
            'message': 'Database synchronized successfully',
            'timestamp': timestamp,
            'results': sync_results
        })
        
    except Exception as e:
        logger.error(f"Sync error: {e}")
        return jsonify({
            'success': False,
            'message': f'Synchronization failed: {str(e)}'
        }), 500

def register_sync_blueprint(app):
    """Register the sync blueprint with a Flask app"""
    app.register_blueprint(sync_bp)
    logger.info("Sync blueprint registered with Flask app")
    return app

if __name__ == "__main__":
    # For testing directly
    from flask import Flask
    app = Flask(__name__)
    register_sync_blueprint(app)
    app.run(debug=True, port=8033)
