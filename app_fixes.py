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
    Fix Flask routing issues - carefully check if routes already exist
    
    Args:
        app: Flask application instance
    """
    try:
        # Check existing routes
        existing_endpoints = set(app.view_functions.keys())
        existing_rules = set(rule.rule for rule in app.url_map.iter_rules())
        
        logger.info(f"Found existing endpoints: {', '.join(existing_endpoints)}")
        
        # Check if login route exists but only add if it doesn't exist
        if 'login' not in existing_endpoints and '/login' not in existing_rules:
            from flask import request, redirect, url_for, flash, session
            from werkzeug.security import check_password_hash, generate_password_hash
            
            # Create a simple login function that actually handles credentials
            @app.route('/login', methods=['GET', 'POST'], endpoint='login')
            def login():
                """Simple login handler with default credentials"""
                # Default credentials for emergency access
                default_username = "admin"
                default_password_hash = generate_password_hash("admin123")
                error = None
                
                # Handle form submission
                if request.method == 'POST':
                    username = request.form.get('username')
                    password = request.form.get('password')
                    
                    if not username:
                        error = "Username is required."
                    elif not password:
                        error = "Password is required."
                    # Check against default credentials
                    elif username != default_username or not check_password_hash(default_password_hash, password):
                        error = "Invalid credentials."
                        logger.warning(f"Failed login attempt for user: {username}")
                    
                    if error is None:
                        # Set session data for the user
                        session.clear()
                        session['user_id'] = 1
                        session['username'] = username
                        session['is_authenticated'] = True
                        
                        logger.info(f"User {username} successfully logged in")
                        
                        # Redirect to index if it exists, or just show welcome page
                        try:
                            return redirect(url_for('index'))
                        except:
                            return """
                            <!DOCTYPE html>
                            <html>
                            <head>
                                <title>Welcome</title>
                                <style>
                                    body { 
                                        font-family: Arial, sans-serif;
                                        margin: 20px;
                                    }
                                </style>
                            </head>
                            <body>
                                <h1>Login Successful</h1>
                                <p>You have successfully logged in.</p>
                            </body>
                            </html>
                            """
                
                # Always add the secret key if not set
                if not app.secret_key:
                    app.secret_key = os.urandom(24)
                    logger.info("Added Flask secret_key for session support")
                    
                # Show login form for GET requests or if validation failed
                error_html = f"<p style='color: red;'>{error}</p>" if error else ""
                return f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Login</title>
                    <style>
                        body {{ 
                            font-family: Arial, sans-serif;
                            margin: 0;
                            padding: 20px;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                        }}
                        .login-container {{
                            padding: 20px;
                            border: 1px solid #ccc;
                            border-radius: 5px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                            width: 300px;
                        }}
                        h1 {{ color: #333; }}
                        .form-group {{
                            margin-bottom: 15px;
                        }}
                        input {{
                            width: 100%;
                            padding: 8px;
                            box-sizing: border-box;
                        }}
                        button {{
                            background: #4285f4;
                            color: white;
                            border: none;
                            padding: 10px 15px;
                            border-radius: 4px;
                            cursor: pointer;
                        }}
                        .error {{
                            color: red;
                            margin-bottom: 15px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="login-container">
                        <h1>Login</h1>
                        {error_html}
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
                        <p style="margin-top: 15px; font-size: 12px; color: #666;">
                            Use default credentials: admin / admin123
                        </p>
                    </div>
                </body>
                </html>
                """
            
            logger.info("Added simple login route with credential handling (endpoint: login)")
        else:
            logger.info("Login route already exists, skipping")
        
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
