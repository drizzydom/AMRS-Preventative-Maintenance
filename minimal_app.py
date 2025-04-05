"""
Minimal fallback application for debugging purposes.
This will run if the main app fails to load.
"""
import os
import sys
import sqlite3
import datetime
from pathlib import Path

def application(environ, start_response):
    """Minimal WSGI application for emergency debug purposes."""
    status = '200 OK'
    output = []
    
    # Get path from request
    path = environ.get('PATH_INFO', '').lstrip('/')
    
    # Handle health check specially
    if path == 'healthz' or path == 'health':
        output = [f"AMRS Minimal Status Check\n\n"
                 f"Time: {datetime.datetime.now().isoformat()}\n"
                 f"Python: {sys.version}\n"
                 f"Working Directory: {os.getcwd()}\n"]
    # If requesting the status page, serve it
    elif path == 'status' or path == 'status.html':
        try:
            with open('status.html', 'rb') as f:
                start_response('200 OK', [('Content-Type', 'text/html')])
                return [f.read()]
        except Exception as e:
            output = [f"Error reading status.html: {str(e)}"]
    # For all other paths, show some debug info
    else:
        output = [f"AMRS Debug Page\n\n"]
        output.append(f"Path requested: {path}\n")
        output.append(f"Time: {datetime.datetime.now().isoformat()}\n")
        output.append(f"Python: {sys.version}\n")
        output.append(f"Working Directory: {os.getcwd()}\n\n")
        
        output.append("Environment Variables:\n")
        for key in sorted(environ):
            if key.startswith(('FLASK', 'RENDER', 'PATH', 'PYTHON', 'SERVER', 'wsgi', 'gunicorn')):
                output.append(f"  {key}: {environ[key]}\n")
        
        # Try to get database info
        output.append("\nDatabase Check:\n")
        try:
            # Check the main database location
            db_path = '/var/data/maintenance.db'
            db_exists = os.path.exists(db_path)
            output.append(f"  DB exists at {db_path}: {db_exists}\n")
            
            if db_exists:
                output.append(f"  DB size: {os.path.getsize(db_path)} bytes\n")
                
                # Try to connect and get table info
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                conn.close()
                
                output.append(f"  Tables: {', '.join(t[0] for t in tables)}\n")
        except Exception as e:
            output.append(f"  DB error: {str(e)}\n")
    
    headers = [('Content-Type', 'text/plain')]
    start_response(status, headers)
    
    return [s.encode('utf-8') for s in output]

# This allows running the script directly for testing
if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    port = int(os.environ.get('PORT', 8000))
    httpd = make_server('', port, application)
    print(f"Serving minimal app on port {port}...")
    httpd.serve_forever()
