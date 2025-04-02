import os
from flask import Blueprint, jsonify, current_app, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, User

# Define the blueprint
user_blueprint = Blueprint('user', __name__, url_prefix='/api/user')

@user_blueprint.route('/profile', endpoint='user_profile')
@jwt_required()
def user_profile():
    """Get current user profile information"""
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'last_login': user.last_login.isoformat() if user.last_login else None
    })

# Add debug route
@user_blueprint.route('/debug-db', endpoint='debug_db')
def debug_db():
    """Database debug info endpoint"""
    info = {
        'database_url': current_app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured'),
        'environment_var': os.environ.get('DATABASE_URL', 'Not set')
    }
    tables = db.metadata.tables.keys()
    
    return jsonify({
        'database_config': info,
        'tables': list(tables),
        'app_config': {
            'debug': current_app.config.get('DEBUG', False),
            'testing': current_app.config.get('TESTING', False),
            'secret_key_set': bool(current_app.config.get('SECRET_KEY'))
        }
    })

@app.route('/ssl_info')
def ssl_info():
    """Information page about SSL certificate warnings"""
    return render_template('ssl_info.html')