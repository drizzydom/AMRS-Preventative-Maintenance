"""
This script starts a Flask server that correctly handles all HTTP methods.
Run this directly to test if it resolves the Method Not Allowed issue.
"""
import os
import sys
from datetime import datetime
from flask import Flask, jsonify, request, make_response

def create_app():
    app = Flask(__name__)
    
    # Configure CORS
    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response
        
    # Handle OPTIONS method for all routes
    @app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
    @app.route('/<path:path>', methods=['OPTIONS'])
    def handle_options(path):
        return make_response('', 204)
        
    # Home route with explicit method support
    @app.route('/', methods=['GET', 'POST'])
    def home():
        if request.method == 'POST':
            return jsonify({
                'status': 'success',
                'message': 'POST request received',
                'data': request.get_json(silent=True) or {}
            })
        else:
            # Return HTML for GET requests - fix the JavaScript template string issue
            return f"""
            <html>
            <head>
                <title>Method Test Server</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; }}
                    h1 {{ color: #3498db; }}
                    .box {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                    button {{ padding: 8px 15px; background: #3498db; color: white; border: none; 
                            border-radius: 4px; cursor: pointer; margin-right: 10px; }}
                </style>
            </head>
            <body>
                <h1>HTTP Method Test Server</h1>
                <p>This server is configured to correctly handle all HTTP methods.</p>
                
                <div class="box">
                    <h3>Current Request Information:</h3>
                    <p><strong>Method:</strong> {request.method}</p>
                    <p><strong>Path:</strong> {request.path}</p>
                    <p><strong>Time:</strong> {datetime.now().isoformat()}</p>
                </div>
                
                <div class="box">
                    <h3>Test Different Methods:</h3>
                    <button onclick="sendRequest('GET')">GET</button>
                    <button onclick="sendRequest('POST')">POST</button>
                    <button onclick="sendRequest('PUT')">PUT</button>
                    <button onclick="sendRequest('DELETE')">DELETE</button>
                    <button onclick="sendRequest('OPTIONS')">OPTIONS</button>
                    <div id="result" style="margin-top: 15px;"></div>
                </div>
                
                <script>
                    async function sendRequest(methodType) {{
                        const resultDiv = document.getElementById('result');
                        resultDiv.innerHTML = 'Sending ' + methodType + ' request...';
                        
                        try {{
                            const response = await fetch('/', {{
                                method: methodType,
                                headers: {{
                                    'Content-Type': 'application/json'
                                }},
                                body: methodType === 'GET' || methodType === 'OPTIONS' ? null : JSON.stringify({{
                                    test: true,
                                    method: methodType,
                                    time: new Date().toISOString()
                                }})
                            }});
                            
                            let result;
                            try {{
                                result = await response.json();
                            }} catch (e) {{
                                result = await response.text();
                            }}
                            
                            resultDiv.innerHTML = 
                                '<p>Status: ' + response.status + ' ' + response.statusText + '</p>' +
                                '<pre>' + JSON.stringify(result, null, 2) + '</pre>';
                        }} catch (error) {{
                            resultDiv.innerHTML = 
                                '<p style="color: red;">Error: ' + error.message + '</p>';
                        }}
                    }}
                </script>
            </body>
            </html>
            """
    
    # Add error handlers to debug Method Not Allowed
    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({
            'error': 'Method Not Allowed',
            'message': str(e),
            'method': request.method,
            'path': request.path,
            'allowed_methods': request.headers.get('Allow', 'Unknown')
        }), 405
    
    return app

if __name__ == "__main__":
    print("Starting HTTP Method Test Server...")
    port = 8033
    app = create_app()
    
    # Write status files for Electron
    appdata_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
    status_dir = os.path.join(appdata_dir, 'AMRS-Maintenance-Tracker')
    
    try:
        os.makedirs(status_dir, exist_ok=True)
        with open(os.path.join(status_dir, 'flask_port.txt'), 'w') as f:
            f.write(str(port))
        with open(os.path.join(status_dir, 'flask_ready.txt'), 'w') as f:
            f.write(f"Method test server running on port {port} at {datetime.now().isoformat()}")
        print(f"Wrote status files to {status_dir}")
    except Exception as e:
        print(f"Warning: Could not write status files: {e}")
    
    print(f"Running on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
