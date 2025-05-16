"""
Simple offline routes for Flask application to use in offline mode
"""
import os
import sys
import logging
from flask import Flask, jsonify, request, render_template, send_from_directory, make_response

# Setup basic logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("offline-routes")

def add_offline_routes(app):
    """Add all required offline routes to Flask app"""
    logger.info("Setting up offline routes")
    
    # Add context processor to replace url_for and other Flask functions
    @app.context_processor
    def inject_functions():
        return {
            'url_for': lambda endpoint, **kwargs: f"/{endpoint}",
            'get_flashed_messages': lambda: []
        }
    
    # Root and health endpoints
    @app.route('/')
    @app.route('/health')
    def index():
        return jsonify({"status": "ok", "mode": "offline"})
    
    # Login page
    @app.route('/login')
    def login_page():
        logger.info("Serving login page")
        try:
            return render_template('login.html', offline_mode=True)
        except Exception as e:
            logger.exception("Error rendering login template")
            return serve_fallback_html('login')
    
    # Dashboard page
    @app.route('/dashboard')
    def dashboard_page():
        logger.info("Serving dashboard page")
        try:
            return render_template('dashboard.html', offline_mode=True)
        except Exception as e:
            logger.exception("Error rendering dashboard template")
            return serve_fallback_html('dashboard')
    
    # Equipment page
    @app.route('/equipment')
    def equipment_page():
        logger.info("Serving equipment page")
        try:
            return render_template('equipment.html', offline_mode=True)
        except Exception as e:
            logger.exception("Error rendering equipment template")
            return serve_fallback_html('equipment')
    
    # API login endpoint - always succeed in offline mode
    @app.route('/api/login', methods=['POST'])
    def api_login():
        logger.info("Handling offline login")
        data = request.get_json() or {}
        username = data.get('username', 'offline_user')
        password = data.get('password', '')
        
        # Always succeed with login in offline mode
        if username and password:
            response = {
                'success': True,
                'user': {
                    'username': username,
                    'name': username,
                    'role': 'user',
                    'permissions': ['view', 'edit']
                },
                'token': 'offline-token-' + username,
                'message': 'Offline login successful'
            }
            return jsonify(response)
        
        return jsonify({
            'success': False,
            'message': 'Username and password are required'
        })
    
    # Catch-all route for any other paths
    @app.route('/<path:path>')
    def catch_all(path):
        logger.info(f"Catch-all route handling path: {path}")
        try:
            if path.endswith('.html'):
                template_name = path
            else:
                template_name = f"{path}.html"
            
            return render_template(template_name, offline_mode=True)
        except Exception as e:
            logger.exception(f"Error in catch-all handler for {path}")
            return serve_fallback_html(path)
    
    # Handle OPTIONS requests for CORS
    @app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
    @app.route('/<path:path>', methods=['OPTIONS'])
    def options_handler(path):
        resp = make_response()
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp

def serve_fallback_html(page_name):
    """Serve fallback HTML for pages that can't be rendered from templates"""
    logger.info(f"Serving fallback HTML for {page_name}")
    
    if page_name == 'login':
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>AMRS - Login (Offline Mode)</title>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px; }
                .login-container { max-width: 400px; margin: 50px auto; background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h2 { color: #2c3e50; text-align: center; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
                button { width: 100%; padding: 10px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
                button:hover { background: #2980b9; }
                .offline-notice { background: #f39c12; color: white; padding: 8px; text-align: center; border-radius: 4px; margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <div class="login-container">
                <div class="offline-notice">You are in offline mode (FALLBACK PAGE)</div>
                <h2>AMRS Maintenance Tracker</h2>
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" placeholder="Enter username">
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" placeholder="Enter password">
                </div>
                <button onclick="login()">Login</button>
            </div>
            <script>
                function login() {
                    const username = document.getElementById('username').value;
                    const password = document.getElementById('password').value;
                    
                    if (!username || !password) {
                        alert('Please enter username and password');
                        return;
                    }
                    
                    // Call API directly since we're in offline fallback mode
                    fetch('/api/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, password })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Login successful in offline mode');
                            window.location.href = '/dashboard';
                        } else {
                            alert(data.message || 'Login failed');
                        }
                    })
                    .catch(err => {
                        alert('Error: ' + err.message);
                    });
                }
            </script>
        </body>
        </html>
        '''
    elif page_name == 'dashboard':
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>AMRS - Dashboard (Offline Mode)</title>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px; }
                .container { max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #2c3e50; }
                .offline-notice { background: #f39c12; color: white; padding: 8px; text-align: center; border-radius: 4px; margin-bottom: 20px; }
                .nav { display: flex; margin-bottom: 20px; flex-wrap: wrap; }
                .nav a { margin-right: 15px; text-decoration: none; color: #3498db; padding: 5px 10px; }
                .nav a:hover { background-color: #f8f9fa; border-radius: 4px; }
                .card { border: 1px solid #ddd; border-radius: 4px; padding: 15px; margin-bottom: 15px; }
                .card h3 { margin-top: 0; }
                .cards { display: flex; flex-wrap: wrap; }
                .card-item { width: 300px; margin-right: 20px; margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="offline-notice">You are in offline mode (FALLBACK PAGE)</div>
                <h1>AMRS Dashboard</h1>
                <div class="nav">
                    <a href="/dashboard">Dashboard</a>
                    <a href="/equipment">Equipment</a>
                    <a href="/maintenance">Maintenance</a>
                    <a href="/login">Logout</a>
                </div>
                <div class="cards">
                    <div class="card card-item">
                        <h3>Equipment</h3>
                        <p>View and manage equipment</p>
                        <button onclick="location.href='/equipment'">View Equipment</button>
                    </div>
                    <div class="card card-item">
                        <h3>Maintenance</h3>
                        <p>Schedule and track maintenance tasks</p>
                        <button onclick="location.href='/maintenance'">Go to Maintenance</button>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
    else:
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>AMRS - Page Not Available</title>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 50px auto; background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #e74c3c; }}
                .nav {{ margin-top: 20px; }}
                .nav a {{ display: inline-block; margin-right: 10px; padding: 8px 15px; background: #3498db; color: white; text-decoration: none; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Page Not Available Offline</h1>
                <p>The requested page "{page_name}" is not available in offline mode.</p>
                <div class="nav">
                    <a href="/dashboard">Go to Dashboard</a>
                    <a href="/login">Go to Login</a>
                </div>
            </div>
        </body>
        </html>
        '''
