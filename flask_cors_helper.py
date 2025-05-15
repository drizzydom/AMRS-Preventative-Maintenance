"""
Helper module to fix CORS issues and Method Not Allowed errors in Flask apps
"""
import os
import sys
from datetime import datetime
from functools import wraps

def add_cors_headers(response):
    """Add CORS headers to a Flask response"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

def apply_cors_to_app(app):
    """Apply CORS handling to a Flask application"""
    # Add CORS headers to all responses
    @app.after_request
    def after_request_func(response):
        return add_cors_headers(response)

    # Handle OPTIONS requests for all routes
    @app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
    @app.route('/<path:path>', methods=['OPTIONS'])
    def options_handler(path):
        response = app.make_default_options_response()
        return add_cors_headers(response)

    # Log all requests to help with debugging
    @app.before_request
    def log_request_info():
        from flask import request
        app.logger.debug(f'Request: {request.method} {request.path} {dict(request.headers)}')

    return app

def fix_flask_app(app):
    """
    Fix a Flask application to work properly with Electron
    
    Call this from your app.py after creating your Flask app:
    app = Flask(__name__)
    # ... your setup ...
    if os.environ.get('ELECTRON') == '1':
        from flask_cors_helper import fix_flask_app
        app = fix_flask_app(app)
    """
    # Apply CORS fixes
    app = apply_cors_to_app(app)
    
    # Write signal files for Electron
    if os.environ.get('ELECTRON') == '1':
        port = int(os.environ.get('PORT', 8033))
        try:
            # Write signal files to both potential locations
            for appdata_dir in [
                os.environ.get('APPDATA'),
                os.path.expanduser('~/Library/Application Support'),
                os.path.join(os.path.dirname(os.environ.get('APPDATA', '')), 
                            'amrs-preventative-maintenance', 'AMRS-Maintenance-Tracker')
            ]:
                if not appdata_dir:
                    continue
                
                status_dir = os.path.join(appdata_dir, 'AMRS-Maintenance-Tracker')
                os.makedirs(status_dir, exist_ok=True)
                
                # Write the port file
                port_file = os.path.join(status_dir, 'flask_port.txt')
                with open(port_file, 'w') as f:
                    f.write(str(port))
                
                # Write the signal file
                signal_file = os.path.join(status_dir, 'flask_ready.txt')
                with open(signal_file, 'w') as f:
                    f.write(f"Main Flask application fully running on port {port} at {datetime.now().isoformat()}")
                
                print(f"Wrote Electron signal files to {status_dir}")
        except Exception as e:
            print(f"Warning: Could not write Electron signal files: {e}")
    
    return app
