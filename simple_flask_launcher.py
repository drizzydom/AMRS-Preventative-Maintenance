#!/usr/bin/env python
"""Simple Flask app launcher for Electron integration"""

import os
import sys
import logging
import time
from datetime import datetime
import signal
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import Flask
try:
    from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
except ImportError as e:
    logger.error(f"Could not import Flask: {e}")
    logger.error("Please install Flask with: pip install flask")
    sys.exit(1)

# Create Flask app with a unique instance_path to avoid conflicts
app = Flask(__name__, 
           template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
           static_folder=os.path.join(os.path.dirname(__file__), 'static'),
           instance_path=os.path.join(os.path.dirname(__file__), 'instance_' + str(int(time.time()))))

# Get configuration from environment variables
PORT = int(os.environ.get('PORT', 8033))
DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'
OFFLINE_MODE = os.environ.get('OFFLINE_MODE', '0') == '1'
FORCED_OFFLINE_MODE = os.environ.get('FORCED_OFFLINE_MODE', '0') == '1'
ELECTRON_APP_PATH = os.environ.get('ELECTRON_APP_PATH', '')
SKIP_ROUTE_CHECK = os.environ.get('SKIP_ROUTE_CHECK', '0') == '1'
ROUTE_PREFIX = os.environ.get('ROUTE_PREFIX', '')

# Track registered routes to avoid duplicates
registered_routes = set()

# Safe route registration function to avoid conflicts
def register_route(rule, **options):
    def decorator(f):
        endpoint = options.pop('endpoint', None) or f.__name__
        
        # Check if route already exists - this fixes the duplicate route issue
        if SKIP_ROUTE_CHECK or endpoint not in registered_routes:
            registered_routes.add(endpoint)
            app.add_url_rule(rule, endpoint=endpoint, view_func=f, **options)
        else:
            logger.warning(f"Route {rule} with endpoint {endpoint} already registered. Skipping.")
            
        return f
    return decorator

# Basic routes for the application
@register_route('/')
def index():
    return redirect(url_for('login'))

@register_route('/login')
def login():
    logger.info("Serving login page")
    return render_template('login.html', offline_mode=OFFLINE_MODE)

@register_route('/dashboard')
def dashboard():
    logger.info("Serving dashboard page")
    return render_template('dashboard.html', offline_mode=OFFLINE_MODE)

@register_route('/api/login', methods=['POST'])
def api_login():
    # Simple API login endpoint
    username = request.json.get('username', '')
    password = request.json.get('password', '')
    
    # In offline mode, accept any credentials
    if OFFLINE_MODE:
        return jsonify({
            'success': True,
            'user': {'username': username, 'name': username, 'role': 'user'},
            'token': f"offline-token-{username}-{int(time.time())}",
            'message': 'Offline login successful'
        })
    
    # In online mode, this would verify against a backend
    # For demo purposes, accept any login
    return jsonify({
        'success': True,
        'user': {'username': username, 'name': username, 'role': 'user'},
        'token': f"demo-token-{username}-{int(time.time())}",
        'message': 'Demo login successful'
    })

# Health check endpoint
@register_route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'offline_mode': OFFLINE_MODE
    })

# Setup offline mode routes if necessary
if OFFLINE_MODE:
    logger.info("Running in offline mode, setting up offline routes")
    try:
        from offline_routes import setup_offline_routes
        setup_offline_routes(app, register_route)
        logger.info("Successfully added offline routes")
    except ImportError:
        logger.warning("Could not import offline_routes module")
    except Exception as e:
        logger.error(f"Failed to setup offline routes: {e}")

# Run the Flask app
if __name__ == '__main__':
    logger.info(f"Starting Flask on port {PORT}")
    app.run(host='127.0.0.1', port=PORT, debug=DEBUG, use_reloader=False)
