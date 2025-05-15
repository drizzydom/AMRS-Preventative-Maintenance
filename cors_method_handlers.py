"""
CORS and HTTP method handlers for AMRS application
"""
import os
import logging
from datetime import datetime
from flask import Flask, request, make_response, jsonify

logger = logging.getLogger(__name__)

def apply_cors_fixes(app):
    """Apply CORS and method handling fixes to a Flask app"""
    logger.info("Applying CORS fixes to Flask app")
    
    @app.after_request
    def add_cors_headers(response):
        """Add CORS headers to all responses"""
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Max-Age'] = '86400'  # 24 hours
        return response
    
    @app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
    @app.route('/<path:path>', methods=['OPTIONS'])
    def options_handler(path):
        """Handle OPTIONS requests for all routes"""
        response = make_response('')
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        return response
    
    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        """Handle Method Not Allowed errors gracefully"""
        return jsonify({
            'error': 'Method Not Allowed',
            'message': str(e),
            'method': request.method,
            'path': request.path,
        }), 405
    
    logger.info("CORS fixes applied successfully")
    return app

def write_electron_signal_files(port):
    """Write signal files for Electron integration"""
    try:
        paths = []
        
        # Try multiple potential paths to ensure Electron finds the signal files
        paths.append(os.environ.get('APPDATA', ''))
        paths.append(os.environ.get('AMRS_DATA_DIR', ''))
        paths.append(os.environ.get('AMRS_ALT_DATA_DIR', ''))
        
        for base_dir in paths:
            if not base_dir:
                continue
                
            status_dir = os.path.join(base_dir, 'AMRS-Maintenance-Tracker')
            os.makedirs(status_dir, exist_ok=True)
            
            with open(os.path.join(status_dir, 'flask_port.txt'), 'w') as f:
                f.write(str(port))
                
            with open(os.path.join(status_dir, 'flask_ready.txt'), 'w') as f:
                f.write(f"Flask fully running on port {port} at {datetime.now().isoformat()}")
                
            logger.info(f"Wrote Electron signal files to {status_dir}")
            
    except Exception as e:
        logger.error(f"Error writing Electron signal files: {str(e)}")

logger.info("cors_method_handlers module loaded successfully")
