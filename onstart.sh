#!/bin/bash
# Ultra-simple startup script with diagnostics

echo "==================== STARTUP DIAGNOSTICS ===================="
echo "Date: $(date)"
echo "Python version: $(python3 --version)"
echo "Working directory: $(pwd)"
echo "Environment variables:"
echo "PORT=${PORT}"
echo "FLASK_APP=${FLASK_APP}"

# Make sure data directory exists
mkdir -p /var/data
chmod -R 777 /var/data

# Print what's in the data directory
echo "Data directory contents:"
ls -la /var/data

echo "Installed Python packages:"
pip list

# Try to run the minimal app first as a sanity check
echo "==================== TRYING MINIMAL APP ===================="
python -c "
import os
print('Starting minimal diagnostic app')
from wsgiref.simple_server import make_server

def app(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'text/plain; charset=utf-8')]
    start_response(status, headers)
    return [b'AMRS Diagnostic: App is running']

port = int(os.environ.get('PORT', '10000'))
print(f'Attempting to start server on port {port}')

# Don't actually start the server, just check if we can initialize it
httpd = make_server('', port, app)
print('Server initialized successfully')
"

# Now try a minimal Flask app
echo "==================== TRYING MINIMAL FLASK APP ===================="
python -c "
import os
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return 'AMRS Minimal Flask Diagnostic'

print(f'Flask app created successfully')
"

# Actually start the application with fallbacks
echo "==================== STARTING APPLICATION ===================="

# First try the minimal app as Flask will be more complex
if ! python minimal_app.py; then
    echo "Minimal app failed, trying main app with gunicorn..."
    
    # Try with gunicorn
    if ! gunicorn app:app --bind 0.0.0.0:${PORT:-10000} --log-level debug; then
        echo "Gunicorn failed, trying direct Flask..."
        
        # Try direct Flask
        if ! python -m flask run --host=0.0.0.0 --port=${PORT:-10000}; then
            echo "Flask run failed, trying wsgi.py..."
            
            # Try wsgi
            if ! python wsgi.py; then
                echo "All app startup methods failed! Starting emergency diagnostic server..."
                
                # Start a very basic Python HTTP server as a last resort
                python -m http.server ${PORT:-10000}
            fi
        fi
    fi
fi
