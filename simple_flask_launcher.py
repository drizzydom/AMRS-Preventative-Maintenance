#!/usr/bin/env python
"""
Simplified launcher script for the Flask app in Electron
"""
import os
import sys
import json
from flask import Flask, request, jsonify, render_template_string, send_from_directory

app = Flask(__name__)

# Get templates directory
def get_templates_dir():
    if os.environ.get('APPDATA'):
        base_dir = os.environ.get('APPDATA')
    else:
        base_dir = os.path.expanduser('~/.config')
    
    app_data_dir = os.path.join(base_dir, 'AMRS-Maintenance-Tracker')
    templates_dir = os.path.join(app_data_dir, 'templates')
    
    if not os.path.exists(templates_dir):
        app_dir = os.path.dirname(os.path.abspath(__file__))
        electron_app_dir = os.path.join(app_dir, 'electron_app')
        templates_dir = os.path.join(electron_app_dir, 'templates')
    
    return templates_dir

# Set up templates folder
templates_dir = get_templates_dir()

@app.route('/ping')
def ping():
    return jsonify({"status": "ok", "message": "Flask API is running"})

@app.route('/')
def index():
    return jsonify({
        "status": "ok",
        "message": "AMRS Flask API is running",
        "version": "1.0.0"
    })

@app.route('/api/sync', methods=['POST'])
def sync():
    return jsonify({
        "success": True,
        "message": "Sync operation completed successfully",
        "timestamp": "2023-01-01T00:00:00.000Z"
    })

# Serve static assets
@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(os.path.join(templates_dir, 'css'), filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(templates_dir, 'js'), filename)

@app.route('/images/<path:filename>')
def serve_images(filename):
    return send_from_directory(os.path.join(templates_dir, 'images'), filename)

@app.route('/fonts/<path:filename>')
def serve_fonts(filename):
    return send_from_directory(os.path.join(templates_dir, 'fonts'), filename)

# Render templates with Jinja
@app.route('/render/<path:template_name>')
def render_template_page(template_name):
    if not template_name.endswith('.html'):
        template_name += '.html'
        
    template_path = os.path.join(templates_dir, template_name)
    if not os.path.exists(template_path):
        # Create a better error response
        error_html = f"""
        <html>
        <head>
            <title>AMRS - Template Not Found</title>
            <style>
                body {{ font-family: Arial; padding: 20px; }}
                h1 {{ color: #e74c3c; }}
                pre {{ background: #f8f9fa; padding: 10px; overflow: auto; }}
            </style>
        </head>
        <body>
            <h1>Template Not Found</h1>
            <p>The requested template could not be found:</p>
            <pre>{template_name}</pre>
            <p>Available templates in {templates_dir}:</p>
            <ul>
        """
        
        # List available templates
        try:
            files = os.listdir(templates_dir)
            for file in files:
                if file.endswith('.html'):
                    error_html += f"<li>{file}</li>"
        except Exception as e:
            error_html += f"<li>Error listing templates: {str(e)}</li>"
        
        error_html += """
            </ul>
        </body>
        </html>
        """
        return error_html, 404
    
    # Sample data that would normally come from a database
    context = {
        'title': 'AMRS Maintenance Tracker',
        'user': {'name': 'Admin User'},
        'offline_mode': True,
        'equipment_list': [
            {'id': 1, 'name': 'Equipment 1', 'status': 'Operational'},
            {'id': 2, 'name': 'Equipment 2', 'status': 'Maintenance'}
        ]
    }
    
    try:
        with open(template_path, 'r') as f:
            template_content = f.read()
        return render_template_string(template_content, **context)
    except Exception as e:
        print(f"Error rendering template: {str(e)}")
        return f"Error rendering template: {str(e)}", 500

if __name__ == '__main__':
    # Get port from environment or default to 8033
    port = int(os.environ.get('PORT', 8033))
    
    # Create signal files for Electron
    appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    status_dir = os.path.join(appdata, 'AMRS-Maintenance-Tracker')
    os.makedirs(status_dir, exist_ok=True)
    
    # Write port and ready files
    with open(os.path.join(status_dir, 'flask_port.txt'), 'w') as f:
        f.write(str(port))
    
    with open(os.path.join(status_dir, 'flask_ready.txt'), 'w') as f:
        f.write(f"Flask fully running on port {port}")
    
    # Only bind to IPv4 localhost to avoid IPv6 issues
    app.run(host='127.0.0.1', port=port)
