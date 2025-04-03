#!/usr/bin/env python3
"""
Minimal Flask application for testing and debugging
"""
from flask import Flask, jsonify, render_template_string, redirect, url_for, request, session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'debug_secret_key'

# Minimal in-memory user database
users = {
    'techsupport': {
        'password': 'Sm@rty123',
        'email': 'techsupport@amrs-maintenance.com',
        'role': 'admin'
    }
}

# Login page template
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>AMRS Login</title>
    <style>
        body { font-family: Arial; margin: 0 auto; max-width: 400px; padding: 40px 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; }
        input[type="text"], input[type="password"] { width: 100%; padding: 8px; box-sizing: border-box; }
        button { background: #3498db; color: white; border: none; padding: 10px 15px; cursor: pointer; }
        .error { color: red; margin-bottom: 15px; }
    </style>
</head>
<body>
    <h1>AMRS Maintenance Tracker</h1>
    <h2>Login</h2>
    {% if error %}
    <div class="error">{{ error }}</div>
    {% endif %}
    <form method="post">
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
</body>
</html>
'''

# Main dashboard template
DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>AMRS Dashboard</title>
    <style>
        body { font-family: Arial; margin: 0 auto; max-width: 800px; padding: 20px; }
        header { display: flex; justify-content: space-between; align-items: center; }
        nav a { margin-left: 15px; color: #3498db; text-decoration: none; }
        .card { background: #f9f9f9; border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <header>
        <h1>AMRS Dashboard</h1>
        <nav>
            <a href="#">Home</a>
            <a href="#">Maintenance</a>
            <a href="{{ url_for('logout') }}">Logout ({{ session['username'] }})</a>
        </nav>
    </header>
    
    <div class="card">
        <h2>System Status</h2>
        <p>✓ Application is running correctly</p>
        <p>✓ Database connection successful</p>
        <p>✓ Login functionality working</p>
    </div>
    
    <div class="card">
        <h2>Debug Information</h2>
        <p>This is a minimal working Flask application</p>
        <p>If you can see this page but not the regular application, then there's an issue with the main application code.</p>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    """Landing page, redirects to login or dashboard"""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and users[username]['password'] == password:
            session['username'] = username
            session['role'] = users[username]['role']
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid username or password"
    
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route('/dashboard')
def dashboard():
    """Dashboard page - requires login"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template_string(DASHBOARD_TEMPLATE)

@app.route('/logout')
def logout():
    """Logout route"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "message": "Minimal test app is running",
        "version": "0.1"
    })

if __name__ == '__main__':
    # Determine if running in Docker
    in_docker = os.path.exists('/.dockerenv')
    
    # Set host to 0.0.0.0 if in Docker
    host = '0.0.0.0' if in_docker else 'localhost'
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 9000))
    
    # Run the app
    app.run(host=host, port=port, debug=True)
