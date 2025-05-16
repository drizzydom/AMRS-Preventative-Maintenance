import os
import logging
from flask import Flask, request, jsonify, render_template, redirect, url_for, session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OfflineModeHandler:
    """Helper class to enable Flask to work in offline mode with Electron."""
    
    def __init__(self, app):
        self.app = app
        self.offline_mode = os.environ.get('OFFLINE_MODE') == '1'
        self.forced_offline = os.environ.get('FORCED_OFFLINE_MODE') == '1'
        self.electron_path = os.environ.get('ELECTRON_APP_PATH', '')
        
        logger.info(f"Offline mode: {self.offline_mode}, Forced: {self.forced_offline}")
        logger.info(f"Electron app path: {self.electron_path}")
        
        # Register routes for offline mode
        self.register_offline_routes()
    
    def register_offline_routes(self):
        """Register routes specifically for offline mode."""
        
        @self.app.route('/health')
        def health_check():
            return jsonify({
                'status': 'ok',
                'offline_mode': self.offline_mode,
                'forced_offline': self.forced_offline
            })
        
        @self.app.route('/offline/login')
        def offline_login():
            """Offline-specific login page."""
            return render_template('login.html', offline_mode=True)
        
        @self.app.route('/offline/dashboard')
        def offline_dashboard():
            """Offline-specific dashboard page."""
            return render_template('dashboard.html', offline_mode=True)
        
        @self.app.route('/offline/equipment')
        def offline_equipment():
            """Offline-specific equipment page."""
            return render_template('equipment.html', offline_mode=True)
        
        # Add API endpoint for offline login
        @self.app.route('/api/offline/login', methods=['POST'])
        def offline_api_login():
            """Handle login in offline mode."""
            data = request.get_json()
            username = data.get('username', '')
            password = data.get('password', '')
            
            # In offline mode, we'll accept any non-empty credentials
            if username and password:
                return jsonify({
                    'success': True,
                    'user': {
                        'username': username,
                        'name': username,
                        'role': 'user'
                    },
                    'message': 'Offline login successful'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Username and password are required'
                })

# Function to apply to Flask app
def configure_offline_mode(app):
    """Configure Flask app for offline mode operation."""
    handler = OfflineModeHandler(app)
    return handler
