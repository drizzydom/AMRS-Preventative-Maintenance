import logging
from flask import Flask

def register_with_flask_app(app):
    """Register offline support with Flask app"""
    from offline_support import register_offline_blueprint
    register_offline_blueprint(app)
    logging.info("Offline support registered with Flask app")
    return app

# For testing directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = Flask(__name__)
    register_with_flask_app(app)
    app.run(debug=True, port=8033)
