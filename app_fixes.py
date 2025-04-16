"""
Application fixes for common issues
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[APP_FIXES] %(message)s')
logger = logging.getLogger("app_fixes")

def fix_sqlalchemy():
    """Apply SQLAlchemy compatibility fix"""
    try:
        # First try to load the module directly
        import sqlalchemy_compat
        logger.info("Applied SQLAlchemy compatibility fix")
        return True
    except ImportError:
        logger.warning("sqlalchemy_compat module not found, skipping SQLAlchemy fix")
        return False
    except Exception as e:
        logger.error(f"Error applying SQLAlchemy fix: {e}")
        return False

def fix_flask_routes(app):
    """
    Fix Flask routing issues
    
    Args:
        app: Flask application instance
    """
    try:
        # Check if the app has a login route
        has_login_route = 'login' in app.view_functions
        
        # If no login route exists, create a simple one
        if not has_login_route:
            @app.route('/login', methods=['GET', 'POST'])
            def login():
                """Simple login page"""
                return """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Login</title>
                    <style>
                        body { 
                            font-family: Arial, sans-serif;
                            margin: 0;
                            padding: 20px;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                        }
                        .login-container {
                            padding: 20px;
                            border: 1px solid #ccc;
                            border-radius: 5px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                            width: 300px;
                        }
                        h1 { color: #333; }
                        .form-group {
                            margin-bottom: 15px;
                        }
                        input {
                            width: 100%;
                            padding: 8px;
                            box-sizing: border-box;
                        }
                        button {
                            background: #4285f4;
                            color: white;
                            border: none;
                            padding: 10px 15px;
                            border-radius: 4px;
                            cursor: pointer;
                        }
                    </style>
                </head>
                <body>
                    <div class="login-container">
                        <h1>Login</h1>
                        <form method="post" action="/login">
                            <div class="form-group">
                                <label for="username">Username:</label>
                                <input type="text" id="username" name="username" required>
                            </div>
                            <div class="form-group">
                                <label for="password">Password:</label>
                                <input type="password" id="password" name="password" required>
                            </div>
                            <button type="submit">Login</button>
                        </form>
                    </div>
                </body>
                </html>
                """
            
            logger.info("Added simple login route")
        
        # Make sure there's a root route
        has_index_route = 'index' in app.view_functions or '/' in [rule.rule for rule in app.url_map.iter_rules()]
        
        if not has_index_route:
            @app.route('/')
            def index():
                """Simple index/home page"""
                try:
                    from flask import redirect, url_for
                    # Only redirect if login route exists
                    if 'login' in app.view_functions:
                        return redirect(url_for('login'))
                except Exception:
                    pass
                    
                # Fallback to a static page
                return """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>AMRS Maintenance Tracker</title>
                    <style>
                        body { 
                            font-family: Arial, sans-serif; 
                            margin: 0;
                            padding: 20px;
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                        }
                        h1 { color: #333; }
                        .button {
                            background: #4285f4;
                            color: white;
                            text-decoration: none;
                            padding: 10px 20px;
                            border-radius: 4px;
                            margin-top: 20px;
                            display: inline-block;
                        }
                    </style>
                </head>
                <body>
                    <h1>AMRS Maintenance Tracker</h1>
                    <p>Welcome to the AMRS Preventative Maintenance System</p>
                    <p>Please log in to continue.</p>
                    <a href="/login" class="button">Log In</a>
                </body>
                </html>
                """
            
            logger.info("Added simple index route")
        
        return True
    except Exception as e:
        logger.error(f"Error fixing Flask routes: {e}")
        return False

def apply_all_fixes(app=None):
    """Apply all fixes"""
    # Fix SQLAlchemy
    fix_sqlalchemy()
    
    # Fix Flask routes if app is provided
    if app:
        fix_flask_routes(app)
    
    logger.info("Applied all available fixes")
    return True
