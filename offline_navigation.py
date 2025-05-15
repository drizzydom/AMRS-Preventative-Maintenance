import os
import json
import logging
from flask import Blueprint, request, jsonify, send_from_directory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
offline_nav_bp = Blueprint('offline_navigation', __name__)

# Get templates directory
def get_templates_dir():
    """Get the path to the bundled templates"""
    # For development
    dev_path = os.path.join(os.path.dirname(__file__), 'electron_app', 'templates')
    if os.path.exists(dev_path):
        return dev_path
        
    # For production build
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller path
        return os.path.join(sys._MEIPASS, 'templates')
    
    # Check if running from Electron resources
    app_path = os.path.dirname(os.path.dirname(__file__))
    prod_path = os.path.join(app_path, 'resources', 'templates')
    if os.path.exists(prod_path):
        return prod_path
        
    # Fallback to a common location
    if os.environ.get('APPDATA'):
        fallback = os.path.join(os.environ.get('APPDATA'), 'AMRS-Maintenance-Tracker', 'templates')
        if os.path.exists(fallback):
            return fallback
            
    logger.error("Templates directory not found")
    return None

# Routes to serve bundled assets
@offline_nav_bp.route('/offline/<path:filename>')
def offline_template(filename):
    """Serve bundled template files"""
    templates_dir = get_templates_dir()
    if templates_dir:
        return send_from_directory(templates_dir, filename)
    return jsonify({'error': 'Templates not found'}), 404

@offline_nav_bp.route('/offline-assets/<path:asset_type>/<path:filename>')
def offline_asset(asset_type, filename):
    """Serve bundled assets (CSS, JS, images, fonts)"""
    templates_dir = get_templates_dir()
    if templates_dir:
        asset_dir = os.path.join(templates_dir, asset_type)
        return send_from_directory(asset_dir, filename)
    return jsonify({'error': 'Asset not found'}), 404

@offline_nav_bp.route('/offline/status')
def offline_status():
    """Check if offline templates are available"""
    templates_dir = get_templates_dir()
    if not templates_dir:
        return jsonify({'available': False})
        
    # Check for manifest
    manifest_path = os.path.join(templates_dir, 'manifest.json')
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            return jsonify({
                'available': True,
                'templates': manifest
            })
        except:
            pass
            
    # Fallback to basic detection
    templates = []
    for filename in os.listdir(templates_dir):
        if filename.endswith('.html'):
            templates.append(filename)
            
    return jsonify({
        'available': len(templates) > 0,
        'templates': templates
    })

def register_offline_navigation(app):
    """Register offline navigation with Flask app"""
    app.register_blueprint(offline_nav_bp)
    logger.info("Offline navigation registered with Flask app")
    return app
