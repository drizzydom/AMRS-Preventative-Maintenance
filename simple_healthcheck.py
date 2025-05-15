#!/usr/bin/env python3
"""
Simple health check module for AMRS Maintenance Tracker application.
"""
import os
import sys
import logging
from datetime import datetime
import sqlite3

logger = logging.getLogger(__name__)

class HealthCheck:
    """Simple health check implementation for Flask application."""
    
    def __init__(self, app=None):
        self.app = app
        self.checks = []
        if app:
            self.init_app(app)
        logger.info("HealthCheck initialized")
    
    def init_app(self, app):
        """Initialize with a Flask application"""
        self.app = app
        
        # Register health check endpoint
        @app.route('/healthcheck')
        def healthcheck_route():
            from flask import jsonify
            result = self.run_checks()
            return jsonify(result)
        
        logger.info("HealthCheck routes registered with Flask app")
    
    def add_check(self, check_func, name=None):
        """Add a health check function"""
        if name is None:
            name = check_func.__name__
        
        self.checks.append((name, check_func))
        return check_func
    
    def run_checks(self):
        """Run all registered health checks"""
        results = {
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        for name, check_func in self.checks:
            try:
                result = check_func()
                results['checks'][name] = {
                    'status': 'ok',
                    'result': result
                }
            except Exception as e:
                results['status'] = 'error'
                results['checks'][name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return results

# Default database health check
def db_check():
    """Check database connection"""
    try:
        # Find the database path through environment variables
        appdata_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
        db_dir = os.path.join(appdata_dir, 'amrs-preventative-maintenance', 'AMRS-Maintenance-Tracker')
        db_path = os.path.join(db_dir, 'amrs_maintenance.db')
        
        if not os.path.exists(db_path):
            return {'status': 'not_found', 'path': db_path}
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT sqlite_version();")
        version = cursor.fetchone()[0]
        
        # Get table information
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        
        conn.close()
        
        return {
            'status': 'connected',
            'version': version,
            'tables': tables,
            'path': db_path
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def main():
    """Run all checks and report results"""
    print("Starting system health check...")
    
    # Wait for app to be fully initialized
    time.sleep(2)
    
    db_result = db_check()
    
    if db_result['status'] == 'connected':
        print("\n==== ALL CHECKS PASSED! System is ready. ====")
        return True
    else:
        print("\n==== SOME CHECKS FAILED! Please check the logs. ====")
        return False

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
