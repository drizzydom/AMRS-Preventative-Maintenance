"""
This file should be imported in your Flask application to enable offline mode.

Example usage:
    from offline_mode_setup import setup_offline_mode
    
    app = Flask(__name__)
    setup_offline_mode(app)
"""
import os
import logging
from flask import Flask, render_template, jsonify

logger = logging.getLogger(__name__)

def setup_offline_mode(app):
    """
    Set up Flask app to handle offline mode.
    
    Args:
        app: Flask application instance
    """
    try:
        from offline_mode_handler import configure_offline_mode
        offline_handler = configure_offline_mode(app)
        logger.info("Offline mode handler configured successfully")
        return offline_handler
    except ImportError as e:
        logger.error(f"Failed to import offline mode handler: {e}")
        
        # Still create a minimal health endpoint
        @app.route('/health')
        def health_check():
            return jsonify({
                'status': 'ok',
                'offline_mode': os.environ.get('OFFLINE_MODE') == '1',
                'offline_handler_loaded': False
            })
