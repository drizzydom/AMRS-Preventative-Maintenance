"""
Minimal Flask application for testing the bundled application
"""
from flask import Flask, jsonify, render_template_string
import os
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Create the Flask application
app = Flask(__name__)

@app.route('/')
def home():
    """Root route that provides a simple HTML interface"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AMRS Maintenance Tracker</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: #f5f5f5; 
            }
            .container {
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 20px;
                max-width: 800px;
                margin: 0 auto;
            }
            h1 { color: #ff6600; }
            .status { 
                padding: 15px;
                border-radius: 4px;
                background: #f0f0f0;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>AMRS Maintenance Tracker</h1>
            <p>This is a minimal test application to verify that bundling works correctly.</p>
            
            <div class="status" id="status">Checking server status...</div>
            
            <script>
                // Make a request to the status API
                fetch('/api/status')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('status').innerHTML = `
                            <strong>Status:</strong> ${data.status}<br>
                            <strong>Message:</strong> ${data.message}<br>
                            <strong>Flask server:</strong> Running<br>
                            <strong>Environment:</strong> ${data.environment}<br>
                            <strong>Working directory:</strong> ${data.working_dir}<br>
                            <strong>Python version:</strong> ${data.python_version}
                        `;
                    })
                    .catch(error => {
                        document.getElementById('status').innerHTML = 
                            `<strong>Error:</strong> Failed to connect to API: ${error}`;
                    });
            </script>
        </div>
    </body>
    </html>
    """)

@app.route('/api/status')
def status():
    """API endpoint that returns server status information"""
    import platform
    return jsonify({
        'status': 'OK',
        'message': 'Flask server is running successfully',
        'environment': os.environ.get('FLASK_ENV', 'production'),
        'working_dir': os.getcwd(),
        'python_version': platform.python_version()
    })

if __name__ == '__main__':
    # Parse command line arguments
    port = 5000
    debug = False
    
    # Check for --port argument
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--port" and i+1 < len(sys.argv):
            try:
                port = int(sys.argv[i+1])
                i += 2
            except ValueError:
                logger.error(f"Invalid port: {sys.argv[i+1]}")
                i += 2
        elif sys.argv[i] == "--debug":
            debug = True
            i += 1
        else:
            i += 1
    
    logger.info(f"Starting Flask server on port {port} (debug={debug})")
    app.run(host='127.0.0.1', port=port, debug=debug)
