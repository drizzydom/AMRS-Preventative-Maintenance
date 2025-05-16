"""
Simple Flask handler for offline mode that can be imported directly in your Flask app.
"""
import os
from flask import Flask, render_template, jsonify, request

def setup_offline_routes(app):
    """
    Add offline mode routes directly to existing Flask app.
    Simple approach that doesn't require additional imports.
    """
    print("Setting up offline mode routes")
    
    @app.route('/health')
    def health_check():
        """Health check endpoint for connectivity testing"""
        return jsonify({
            'status': 'ok',
            'offline_mode': os.environ.get('OFFLINE_MODE') == '1',
            'forced_offline': os.environ.get('FORCED_OFFLINE_MODE') == '1'
        })
    
    @app.route('/offline/login')
    def offline_login():
        """Simplified login page for offline mode"""
        return render_template('login.html', offline_mode=True)
    
    @app.route('/offline/dashboard')
    def offline_dashboard():
        """Dashboard for offline mode"""
        return render_template('dashboard.html', offline_mode=True)
    
    @app.route('/offline/equipment')
    def offline_equipment():
        """Equipment page for offline mode"""
        return render_template('equipment.html', offline_mode=True)
    
    @app.route('/api/offline/login', methods=['POST'])
    def offline_api_login():
        """Handle login in offline mode"""
        data = request.get_json()
        username = data.get('username', '')
        password = data.get('password', '')
        
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
