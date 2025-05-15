"""
This module provides comprehensive CORS support for Flask applications.
It addresses "Method Not Allowed" errors common in Electron apps.
"""
import os
import time
from datetime import datetime
from functools import wraps
from flask import Flask, request, make_response, jsonify, current_app

def enable_cors(app):
    """Enable full CORS support for a Flask app"""
    
    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        # Add cache control to avoid browser caching responses
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
        
    # Handle OPTIONS method for all routes
    @app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
    @app.route('/<path:path>', methods=['OPTIONS'])
    def handle_options(path):
        return make_response('', 204, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
            'Access-Control-Max-Age': '86400',  # 24 hours
        })
        
    # Add a route that specifically handles Electron connection
    @app.route('/electron-connect', methods=['GET', 'POST'])
    def electron_connect():
        method = request.method
        return jsonify({
            'status': 'success',
            'message': f'Successfully connected via {method}',
            'timestamp': datetime.now().isoformat(),
            'headers': dict(request.headers)
        })
        
    # Add an error handler for 405 Method Not Allowed
    @app.errorhandler(405)
    def method_not_allowed(e):
        allowed_methods = request.headers.get('Access-Control-Request-Method', 'GET, POST, OPTIONS')
        return jsonify({
            'error': 'Method Not Allowed',
            'message': str(e),
            'allowed_methods': allowed_methods,
            'current_method': request.method,
            'path': request.path,
            'timestamp': datetime.now().isoformat()
        }), 405, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With'
        }
        
    return app

def create_test_app():
    """Create a test app that has proper CORS handling"""
    app = Flask(__name__)
    app = enable_cors(app)
    
    # Add endpoints that explicitly support all methods
    @app.route('/', methods=['GET', 'POST'])
    def index():
        return f"""
        <html>
        <head><title>AMRS Maintenance Tracker</title></head>
        <body>
            <h1>AMRS Maintenance Tracker</h1>
            <p>The server is running correctly.</p>
            <p>Request method: {request.method}</p>
            <p>Timestamp: {datetime.now().isoformat()}</p>
            <hr>
            <p>Try these routes:</p>
            <ul>
                <li><a href="/dashboard">/dashboard</a></li>
                <li><a href="/login">/login</a></li>
                <li><a href="/electron-connect">/electron-connect</a></li>
            </ul>
        </body>
        </html>
        """
        
    @app.route('/dashboard', methods=['GET', 'POST'])
    def dashboard():
        return f"""
        <html>
        <head><title>AMRS Dashboard</title></head>
        <body>
            <h1>AMRS Dashboard</h1>
            <p>This is the dashboard page (supports GET and POST).</p>
            <p>Request method: {request.method}</p>
            <p>Timestamp: {datetime.now().isoformat()}</p>
            <hr>
            <p><a href="/">Back to home</a></p>
        </body>
        </html>
        """
    
    return app

# Run this file directly to test CORS handling
if __name__ == '__main__':
    print("Starting test CORS-enabled Flask app...")
    test_app = create_test_app()
    port = 8033
    
    # Write signal files for Electron if needed
    appdata_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
    status_dir = os.path.join(appdata_dir, 'AMRS-Maintenance-Tracker')
    os.makedirs(status_dir, exist_ok=True)
    
    with open(os.path.join(status_dir, 'flask_port.txt'), 'w') as f:
        f.write(str(port))
    
    with open(os.path.join(status_dir, 'flask_ready.txt'), 'w') as f:
        f.write(f"Test CORS app running on port {port} at {datetime.now().isoformat()}")
        
    print(f"Running on http://localhost:{port}")
    test_app.run(host='0.0.0.0', port=port, debug=True)
