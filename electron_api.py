"""
API endpoints for Electron offline mode functionality
"""

from flask import Blueprint, jsonify, request, current_app
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Blueprint for electron-specific routes
electron_bp = Blueprint('electron', __name__)

def is_electron():
    """Detect if running in Electron environment"""
    return os.environ.get('ELECTRON_RUN_AS_NODE') is not None or os.environ.get('AMRS_ELECTRON') == '1' or os.environ.get('ELECTRON') == '1'

@electron_bp.route('/status')
def electron_status():
    """Get Electron app status"""
    if not is_electron():
        return jsonify({
            'mode': 'web',
            'electron': False,
            'timestamp': datetime.now().isoformat()
        })
    
    try:
        # Get sync status
        from offline_adapter import get_sync_status, is_online
        
        status = get_sync_status()
        
        return jsonify({
            'mode': 'electron',
            'electron': True,
            'online': is_online(),
            'sync': status,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting Electron status: {e}")
        return jsonify({
            'mode': 'electron',
            'electron': True,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@electron_bp.route('/sync', methods=['POST'])
def trigger_sync():
    """Trigger a database synchronization"""
    if not is_electron():
        return jsonify({
            'status': 'error',
            'message': 'Not running in Electron mode',
            'timestamp': datetime.now().isoformat()
        }), 400
    
    try:
        # Trigger a sync
        from offline_adapter import schedule_sync, is_online
        
        if not is_online():
            return jsonify({
                'status': 'error',
                'message': 'Cannot sync while offline',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Schedule an immediate sync
        schedule_sync(immediate=True)
        
        return jsonify({
            'status': 'ok',
            'message': 'Synchronization scheduled',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error triggering sync: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@electron_bp.route('/backup', methods=['POST'])
def backup_database():
    """Create a backup of the current database"""
    if not is_electron():
        return jsonify({
            'status': 'error',
            'message': 'Not running in Electron mode',
            'timestamp': datetime.now().isoformat()
        }), 400
    
    try:
        # Create a backup
        from electron_sqlite_setup import backup_database
        
        success = backup_database()
        
        if success:
            return jsonify({
                'status': 'ok',
                'message': 'Database backup created successfully',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to create database backup',
                'timestamp': datetime.now().isoformat()
            }), 500
    except Exception as e:
        logger.error(f"Error backing up database: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Function to register the blueprint
def register_electron_routes(app):
    """Register Electron-specific routes with the Flask app"""
    app.register_blueprint(electron_bp, url_prefix='/electron')
