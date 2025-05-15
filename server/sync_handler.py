import os
import json
import sqlite3
import logging
import requests
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from werkzeug.security import generate_password_hash
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
sync_bp = Blueprint('sync_handler', __name__)

# Database configuration
def get_db_path():
    """Get the SQLite database path"""
    if os.environ.get('APPDATA'):
        # Windows
        base_dir = os.environ.get('APPDATA')
    else:
        # macOS/Linux
        base_dir = os.path.expanduser('~/.config')
    
    app_data_dir = os.path.join(base_dir, 'AMRS-Maintenance-Tracker')
    os.makedirs(app_data_dir, exist_ok=True)
    
    return os.path.join(app_data_dir, 'maintenance.db')

@sync_bp.route('/api/sync', methods=['POST'])
def sync_database():
    """Synchronize database from server to client SQLite"""
    from api_sync import token_required  # Import here to avoid circular imports
    
    @token_required
    def _sync_database():
        try:
            data = request.get_json()
            token = data.get('token')
            
            if not token:
                return jsonify({
                    'success': False,
                    'message': 'Authentication token is required'
                }), 401
            
            # Get database connection
            db = current_app.extensions.get('sqlalchemy').db
            
            # Create SQLite database
            sqlite_path = get_db_path()
            logger.info(f"Creating/updating SQLite database at: {sqlite_path}")
            
            # Get tables to sync
            tables = data.get('tables', [])
            if not tables:
                # Get all non-system tables if none specified
                inspector = db.inspect(db.engine)
                tables = [t for t in inspector.get_table_names() 
                          if not t.startswith('sqlite_') and 
                          not t.startswith('pg_') and 
                          t != 'alembic_version']
            
            # Connect to SQLite database
            sqlite_conn = sqlite3.connect(sqlite_path)
            sqlite_cursor = sqlite_conn.cursor()
            
            # Track sync results
            results = {}
            
            # Process each table
            for table in tables:
                try:
                    # Get table schema
                    inspector = db.inspect(db.engine)
                    columns = inspector.get_columns(table)
                    
                    # Generate CREATE TABLE statement
                    create_sql = _generate_sqlite_create_statement(table, columns)
                    
                    # Create table in SQLite
                    sqlite_cursor.execute(f"DROP TABLE IF EXISTS {table}_temp")
                    sqlite_cursor.execute(create_sql.replace(table, f"{table}_temp"))
                    
                    # Get data from PostgreSQL
                    query = f"SELECT * FROM {table}"
                    pg_result = db.session.execute(text(query))
                    
                    # Insert data into SQLite
                    row_count = 0
                    col_names = pg_result.keys()
                    
                    for row in pg_result:
                        # Convert data types as needed for SQLite
                        values = []
                        for val in row:
                            if isinstance(val, datetime):
                                values.append(val.isoformat())
                            elif val is None:
                                values.append(None)
                            else:
                                values.append(str(val))
                        
                        # Create INSERT statement
                        placeholders = ", ".join(["?" for _ in values])
                        insert_sql = f"INSERT INTO {table}_temp ({', '.join(col_names)}) VALUES ({placeholders})"
                        
                        # Execute insert
                        sqlite_cursor.execute(insert_sql, values)
                        row_count += 1
                    
                    # Replace old table with new one
                    sqlite_cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    sqlite_cursor.execute(f"ALTER TABLE {table}_temp RENAME TO {table}")
                    
                    # Commit changes
                    sqlite_conn.commit()
                    
                    # Track result
                    results[table] = {
                        'status': 'success',
                        'rows': row_count
                    }
                    
                except Exception as e:
                    logger.error(f"Error syncing table {table}: {str(e)}")
                    results[table] = {
                        'status': 'error',
                        'message': str(e)
                    }
            
            # Close SQLite connection
            sqlite_conn.close()
            
            # Write sync timestamp
            timestamp = datetime.utcnow().isoformat()
            sync_file = os.path.join(os.path.dirname(sqlite_path), 'last_sync.txt')
            with open(sync_file, 'w') as f:
                f.write(timestamp)
            
            return jsonify({
                'success': True,
                'message': 'Database synchronized successfully',
                'timestamp': timestamp,
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Database sync error: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Synchronization failed: {str(e)}'
            }), 500
    
    return _sync_database()

def _generate_sqlite_create_statement(table, columns):
    """Helper function to generate SQLite CREATE TABLE statement"""
    col_defs = []
    pk_cols = []
    
    for col in columns:
        name = col['name']
        col_type = _map_pg_to_sqlite_type(str(col['type']))
        
        definition = f"{name} {col_type}"
        
        # Handle primary key
        if col.get('primary_key'):
            pk_cols.append(name)
        # Handle NOT NULL
        elif not col.get('nullable', True):
            definition += " NOT NULL"
            
        col_defs.append(definition)
    
    # Add primary key constraint if needed
    if pk_cols:
        pk_constraint = f"PRIMARY KEY ({', '.join(pk_cols)})"
        col_defs.append(pk_constraint)
    
    create_stmt = f"CREATE TABLE {table} (\n  " + ",\n  ".join(col_defs) + "\n)"
    return create_stmt

def _map_pg_to_sqlite_type(pg_type):
    """Map PostgreSQL types to SQLite types"""
    pg_type = pg_type.lower()
    
    if "int" in pg_type:
        return "INTEGER"
    elif "char" in pg_type or "text" in pg_type:
        return "TEXT"
    elif "bool" in pg_type:
        return "INTEGER"  # SQLite doesn't have boolean
    elif "float" in pg_type or "double" in pg_type or "numeric" in pg_type:
        return "REAL"
    elif "date" in pg_type or "time" in pg_type:
        return "TEXT"  # Store as ISO format text
    elif "json" in pg_type:
        return "TEXT"  # Store as JSON string
    else:
        return "TEXT"  # Default for unknown types

def register_sync_handler(app):
    """Register sync handler with Flask app"""
    app.register_blueprint(sync_bp)
    logger.info("Sync handler registered with Flask app")
    return app
