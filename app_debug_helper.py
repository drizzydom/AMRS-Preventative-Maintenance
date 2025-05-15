"""
Debug helper module for AMRS Maintenance Tracker application.
"""
import os
import sys
import platform
import logging
from datetime import datetime
from flask import Flask, jsonify
from flask_login import login_required
from models import db, AuditTaskCompletion
from app import app

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def register_debug_routes(app):
    """Register debug routes with the Flask application"""
    logger.info("Registering debug routes")
    
    @app.route('/debug/info')
    def debug_info():
        """Return system information for debugging"""
        
        # System information
        info = {
            'timestamp': datetime.now().isoformat(),
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'processor': platform.processor()
            },
            'python': {
                'version': sys.version,
                'executable': sys.executable,
                'path': sys.path
            },
            'environment': {
                'cwd': os.getcwd(),
                'env_vars': {k: v for k, v in os.environ.items() 
                             if not k.lower().startswith(('pass', 'secret', 'key'))}
            }
        }
        
        return jsonify(info)
    
    @app.route('/debug/database')
    def debug_database():
        """Return database information"""
        import sqlite3
        
        try:
            # Find database path
            appdata_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
            db_dir = os.path.join(appdata_dir, 'amrs-preventative-maintenance', 'AMRS-Maintenance-Tracker')
            db_path = os.path.join(db_dir, 'amrs_maintenance.db')
            
            if not os.path.exists(db_path):
                return jsonify({
                    'status': 'error',
                    'message': f'Database not found at {db_path}'
                })
            
            # Connect to database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get schema information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [table[0] for table in cursor.fetchall()]
            
            # Get table schemas
            schemas = {}
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table});")
                columns = [{
                    'cid': col[0],
                    'name': col[1],
                    'type': col[2],
                    'notnull': col[3],
                    'default': col[4],
                    'pk': col[5]
                } for col in cursor.fetchall()]
                schemas[table] = columns
                
            conn.close()
            
            return jsonify({
                'status': 'success',
                'database_path': db_path,
                'tables': tables,
                'schemas': schemas
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            })
    
    logger.info("Debug routes registered")
    return app

def debug_app():
    """Run diagnostic checks for app packaging"""
    # Print environment info
    print("=== Environment Information ===")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    # Check for critical files
    print("\n=== Checking Critical Files ===")
    app_path = os.path.join(os.getcwd(), 'app.py')
    if os.path.exists(app_path):
        print(f"app.py: Found at {app_path}")
        with open(app_path, 'r', encoding='utf-8') as f:
            first_lines = [f.readline() for _ in range(5)]
        print("First 5 lines:")
        print(''.join(first_lines))
    else:
        print(f"app.py: MISSING at {app_path}")
    
    # Check for directories
    print("\n=== Checking Directories ===")
    directories = ['static', 'templates', 'modules']
    for directory in directories:
        dir_path = os.path.join(os.getcwd(), directory)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            files = os.listdir(dir_path)
            print(f"{directory}: Found with {len(files)} files")
            if files:
                print(f"Sample files: {', '.join(files[:5])}")
        else:
            print(f"{directory}: MISSING")
    
    # Check for Flask
    print("\n=== Checking Flask ===")
    try:
        import flask
        print(f"Flask version: {flask.__version__}")
        print(f"Flask location: {flask.__file__}")
    except ImportError as e:
        print(f"Failed to import Flask: {e}")
    
    # Check other dependencies
    print("\n=== Checking Other Dependencies ===")
    dependencies = [
        'pandas', 'werkzeug', 'jinja2', 'click', 'itsdangerous'
    ]
    
    for dep in dependencies:
        try:
            module = __import__(dep)
            if hasattr(module, '__version__'):
                print(f"{dep}: {module.__version__}")
            else:
                print(f"{dep}: Imported successfully, but no version info")
        except ImportError as e:
            print(f"{dep}: Import failed - {e}")
    
    # Save directory listing
    print("\n=== Saving Directory Listing ===")
    try:
        with open('resources-files.txt', 'w') as f:
            for root, dirs, files in os.walk('.'):
                for file in files:
                    if not file.endswith('.pyc') and '__pycache__' not in root:
                        f.write(os.path.join(root, file) + '\n')
        print("Directory listing saved to resources-files.txt")
    except Exception as e:
        print(f"Error saving directory listing: {e}")

@app.route('/debug/audit-completions')
@login_required
def debug_audit_completions():
    records = AuditTaskCompletion.query.order_by(AuditTaskCompletion.id.desc()).limit(20).all()
    output = []
    for r in records:
        output.append({
            'id': r.id,
            'audit_task_id': r.audit_task_id,
            'machine_id': r.machine_id,
            'date': str(r.date),
            'completed': r.completed,
            'completed_at': str(r.completed_at),
        })
    return {'records': output}

# Automatically registering with app is not necessary, will be imported in app.py
logger.info("app_debug_helper module loaded successfully")

if __name__ == "__main__":
    print("Running app.py diagnostics...")
    try:
        debug_app()
        print("\nDiagnostics completed successfully")
    except Exception as e:
        print(f"Error during diagnostics: {e}")
        traceback.print_exc()
    
    print("\nPress Enter to exit...")
    try:
        input()
    except:
        pass
