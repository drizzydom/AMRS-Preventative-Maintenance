# Add route for offline functionality in main app
from flask import jsonify, request, Blueprint, render_template, flash
from flask_login import login_required, current_user
import os
import datetime
import json

# Create a blueprint for offline functionality
offline_bp = Blueprint('offline', __name__)

@offline_bp.route('/offline-status')
@login_required
def offline_status():
    """Check offline sync status"""
    return render_template('offline/status.html', 
                          user=current_user,
                          is_offline_enabled=True)

@offline_bp.route('/offline-sync')
@login_required
def offline_sync():
    """Synchronize data for offline use"""
    # This route will provide the UI for syncing data
    return render_template('offline/sync.html', 
                          user=current_user)

@offline_bp.route('/generate-offline-token', methods=['POST'])
@login_required
def generate_offline_token():
    """Generate an authentication token for offline use"""
    from app import app, db
    from models import User, Role
    import jwt
    
    # Secret key for JWT tokens
    JWT_SECRET_KEY = app.config.get('SECRET_KEY')

    # Generate token with user id, role and expiration (30 days)
    token_payload = {
        'user_id': current_user.id,
        'username': current_user.username,
        'role_id': current_user.role_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }
    
    token = jwt.encode(token_payload, JWT_SECRET_KEY, algorithm='HS256')
    
    # Get the user's role name
    role = Role.query.get(current_user.role_id)
    role_name = role.name if role else "Unknown"
    
    return jsonify({
        'token': token,
        'username': current_user.username,
        'role': role_name,
        'expires_in': 30 * 24 * 60 * 60,  # 30 days in seconds
        'generated_at': datetime.datetime.utcnow().isoformat()
    })

# Register this blueprint in your main app.py file with:
# from offline_routes import offline_bp
# app.register_blueprint(offline_bp, url_prefix='/offline')
