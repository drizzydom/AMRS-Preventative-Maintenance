#!/usr/bin/env python3
"""
Ultra-minimal diagnostic application that will definitely run.
"""
import os
import sys
import time
import traceback
from datetime import datetime

# Ensure as little external dependencies as possible
try:
    from http.server import HTTPServer, BaseHTTPRequestHandler
except ImportError:
    print("ERROR: Cannot import http.server - Python 3 required")
    sys.exit(1)

class DiagnosticHandler(BaseHTTPRequestHandler):
    """Simple request handler that returns diagnostics"""
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            if self.path == "/health" or self.path == "/healthz":
                self.health_check()
            elif self.path == "/env":
                self.show_environment()
            elif self.path == "/disk":
                self.check_disk()
            else:
                self.show_main_page()
        except Exception as e:
            self.send_error_response(str(e))
    
    def health_check(self):
        """Return basic health check"""
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(f"OK - {datetime.now().isoformat()}".encode())
    
    def show_environment(self):
        """Show environment variables"""
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        output = ["Environment Variables:"]
        for key, value in sorted(os.environ.items()):
            # Redact potentially sensitive information
            if "KEY" in key or "SECRET" in key or "PASSWORD" in key or "TOKEN" in key:
                value = "[REDACTED]"
            output.append(f"{key}={value}")
        self.wfile.write("\n".join(output).encode())
    
    def check_disk(self):
        """Check disk space and permissions"""
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        output = ["Disk Diagnostics:"]
        
        # Check data directory
        data_dir = "/var/data"
        output.append(f"Data directory exists: {os.path.exists(data_dir)}")
        if os.path.exists(data_dir):
            output.append(f"Is directory: {os.path.isdir(data_dir)}")
            output.append(f"Can read: {os.access(data_dir, os.R_OK)}")
            output.append(f"Can write: {os.access(data_dir, os.W_OK)}")
            output.append(f"Can execute: {os.access(data_dir, os.X_OK)}")
            
            # Try to write a test file
            test_file = os.path.join(data_dir, "test_write.txt")
            try:
                with open(test_file, "w") as f:
                    f.write("Test write")
                output.append(f"Successfully wrote test file: {test_file}")
                os.remove(test_file)
                output.append(f"Successfully removed test file: {test_file}")
            except Exception as e:
                output.append(f"Error writing test file: {str(e)}")
            
            # List directory contents
            try:
                files = os.listdir(data_dir)
                output.append(f"Directory contents ({len(files)} items):")
                for item in files:
                    item_path = os.path.join(data_dir, item)
                    item_type = "dir" if os.path.isdir(item_path) else "file"
                    item_size = os.path.getsize(item_path) if os.path.isfile(item_path) else "-"
                    output.append(f"  {item} ({item_type}, {item_size} bytes)")
            except Exception as e:
                output.append(f"Error listing directory: {str(e)}")
        
        self.wfile.write("\n".join(output).encode())
    
    def show_main_page(self):
        """Show main diagnostic page"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        
        html = f"""<!DOCTYPE html>
        <html>
        <head>
            <title>AMRS Diagnostics</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #FE7900; }}
                .section {{ margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .btn {{ padding: 10px 15px; background-color: #FE7900; color: white; border: none; border-radius: 4px; cursor: pointer; display: inline-block; margin: 5px; text-decoration: none; }}
                .btn:hover {{ background-color: #E56C00; }}
                pre {{ background-color: #f8f8f8; padding: 10px; overflow: auto; }}
            </style>
        </head>
        <body>
            <h1>AMRS Diagnostic Server</h1>
            <p>This is a minimal diagnostic server to help troubleshoot the application.</p>
            
            <div class="section">
                <h2>System Information:</h2>
                <p><strong>Time:</strong> {datetime.now().isoformat()}</p>
                <p><strong>Python Version:</strong> {sys.version}</p>
                <p><strong>Working Directory:</strong> {os.getcwd()}</p>
                <p><strong>Process ID:</strong> {os.getpid()}</p>
            </div>
            
            <div class="section">
                <h2>Diagnostic Tools:</h2>
                <a href="/health" class="btn">Health Check</a>
                <a href="/env" class="btn">Environment Variables</a>
                <a href="/disk" class="btn">Disk Diagnostics</a>
            </div>
            
            <div class="section">
                <h2>Next Steps:</h2>
                <p>If you're seeing this page, the diagnostic server is working. This means that:</p>
                <ol>
                    <li>The server is running and can bind to the required port</li>
                    <li>The basic Python installation is working</li>
                    <li>We can output diagnostic information</li>
                </ol>
                <p>If the main application isn't working, it likely has issues with:</p>
                <ol>
                    <li>Flask installation or configuration</li>
                    <li>Database access or permissions</li>
                    <li>Errors in the application code</li>
                </ol>
            </div>
        </body>
        </html>"""
        
        self.wfile.write(html.encode())
    
    def send_error_response(self, error):
        """Send an error response"""
        self.send_response(500)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        output = ["ERROR:", str(error), "", "Traceback:", traceback.format_exc()]
        self.wfile.write("\n".join(output).encode())

def run_server():
    """Run the diagnostic server"""
    port = int(os.environ.get("PORT", "10000"))
    print(f"Starting diagnostic server on port {port}...")
    
    server = None
    try:
        server = HTTPServer(("0.0.0.0", port), DiagnosticHandler)
        print(f"Server started successfully, listening on port {port}")
        server.serve_forever()
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        if server:
            server.server_close()
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(run_server())
