"""
Helper module to fix Method Not Allowed errors in the Flask application.
Run this directly or import into your Flask app.
"""
import os
import sys
from datetime import datetime
from functools import wraps

try:
    from flask import Flask, request, jsonify, make_response
except ImportError:
    print("Flask not installed. Install with: pip install flask")
    sys.exit(1)

def fix_method_allowed_errors(app):
    """
    Apply fixes to a Flask app to handle Method Not Allowed errors properly
    """
    # Add a generic OPTIONS handler for all routes
    @app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
    @app.route('/<path:path>', methods=['OPTIONS'])
    def options_handler(path):
        response = make_response('')
        response.headers['Allow'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With'
        return response

    # Properly handle 405 Method Not Allowed errors
    @app.errorhandler(405)
    def method_not_allowed(e):
        # Get the list of allowed methods for the current route
        adapter = app.url_map.bind('')
        try:
            method, func = adapter.match(request.path, method='HEAD')
            allowed_methods = getattr(func, 'methods', ['GET'])
        except:
            allowed_methods = ['GET']
            
        response = jsonify({
            'error': 'Method Not Allowed',
            'message': str(e),
            'method': request.method,
            'path': request.path,
            'allowed_methods': ', '.join(allowed_methods)
        })
        response.status_code = 405
        response.headers['Allow'] = ', '.join(allowed_methods)
        return response

    # Add test endpoints that support all methods
    @app.route('/test-methods', methods=['GET', 'POST', 'PUT', 'DELETE'])
    def test_methods():
        """Endpoint that supports multiple HTTP methods for testing"""
        method = request.method
        if method == 'GET':
            return jsonify({
                'message': 'GET request successful',
                'method': method,
                'timestamp': datetime.now().isoformat()
            })
        elif method == 'POST':
            return jsonify({
                'message': 'POST request successful',
                'method': method,
                'data': request.get_json(silent=True) or {},
                'timestamp': datetime.now().isoformat()
            })
        elif method == 'PUT':
            return jsonify({
                'message': 'PUT request successful',
                'method': method,
                'data': request.get_json(silent=True) or {},
                'timestamp': datetime.now().isoformat()
            })
        elif method == 'DELETE':
            return jsonify({
                'message': 'DELETE request successful',
                'method': method,
                'timestamp': datetime.now().isoformat()
            })

    return app

# Create a standalone test app if run directly
if __name__ == '__main__':
    app = Flask(__name__)
    app = fix_method_allowed_errors(app)
    
    @app.route('/')
    def index():
        return f"""
        <html>
        <head>
            <title>Method Fix Test</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #2c3e50; }}
                button {{ padding: 8px 15px; margin: 5px; cursor: pointer; }}
                pre {{ background: #f8f9fa; padding: 10px; border-radius: 4px; overflow: auto; }}
            </style>
        </head>
        <body>
            <h1>HTTP Method Test Server</h1>
            <p>This server is set up to correctly handle all HTTP methods.</p>
            
            <h2>Test Methods:</h2>
            <button onclick="sendRequest('GET')">GET</button>
            <button onclick="sendRequest('POST')">POST</button>
            <button onclick="sendRequest('PUT')">PUT</button>
            <button onclick="sendRequest('DELETE')">DELETE</button>
            <button onclick="sendRequest('OPTIONS')">OPTIONS</button>
            
            <h3>Response:</h3>
            <pre id="response">Click a button to make a request</pre>
            
            <script>
                async function sendRequest(methodType) {{
                    const responseElem = document.getElementById('response');
                    responseElem.textContent = 'Sending ' + methodType + ' request...';
                    
                    try {{
                        const response = await fetch('/test-methods', {{
                            method: methodType,
                            headers: {{
                                'Content-Type': 'application/json'
                            }},
                            body: methodType === 'GET' || methodType === 'OPTIONS' ? null : 
                                  JSON.stringify({{ test: true, time: new Date().toISOString() }})
                        }});
                        
                        const contentType = response.headers.get('content-type');
                        let responseData;
                        
                        if (contentType && contentType.includes('application/json')) {{
                            responseData = await response.json();
                        }} else {{
                            responseData = await response.text();
                        }}
                        
                        responseElem.textContent = 
                            'Status: ' + response.status + ' ' + response.statusText + '\\n\\n' +
                            JSON.stringify(responseData, null, 2);
                    }} catch (error) {{
                        responseElem.textContent = 'Error: ' + error.message;
                    }}
                }}
            </script>
        </body>
        </html>
        """
    
    # Write signal files for Electron
    port = 8033
    app_data_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
    status_dir = os.path.join(app_data_dir, 'AMRS-Maintenance-Tracker')
    os.makedirs(status_dir, exist_ok=True)
    
    with open(os.path.join(status_dir, 'flask_port.txt'), 'w') as f:
        f.write(str(port))
    
    with open(os.path.join(status_dir, 'flask_ready.txt'), 'w') as f:
        f.write(f"Method fix server running on port {port} at {datetime.now().isoformat()}")
    
    print(f"Starting server on http://localhost:{port}")
    print(f"Signal files written to {status_dir}")
    app.run(host='0.0.0.0', port=port)
