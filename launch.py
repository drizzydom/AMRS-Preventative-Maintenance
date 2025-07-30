#!/usr/bin/env python3
"""
Unified Application Launcher
Consolidates functionality from app-launcher.py and flask-launcher.py
"""
import os
import sys
import traceback

def main():
    """Main entry point for launching the AMRS application."""
    print("[LAUNCHER] Starting AMRS Preventative Maintenance System...")
    print(f"[LAUNCHER] Python: {sys.executable}")
    print(f"[LAUNCHER] Version: {sys.version}")
    print(f"[LAUNCHER] Working Directory: {os.getcwd()}")
    
    # Get script directory and ensure it's in Python path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
        print(f"[LAUNCHER] Added {script_dir} to Python path")
    
    # Verify app.py exists
    app_path = os.path.join(script_dir, 'app.py')
    if not os.path.isfile(app_path):
        print(f"[LAUNCHER ERROR] app.py not found at: {app_path}")
        sys.exit(1)
    
    print(f"[LAUNCHER] Found app.py at: {app_path}")
    
    # Parse command line arguments
    port = 5000
    if len(sys.argv) >= 3 and sys.argv[1] == '--port':
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(f"[LAUNCHER ERROR] Invalid port number: {sys.argv[2]}")
            sys.exit(1)
    elif len(sys.argv) >= 2:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass  # Not a port number, ignore
    
    # Set the port in environment for the app to use
    os.environ["PORT"] = str(port)
    
    try:
        # Import the app module
        print("[LAUNCHER] Importing app module...")
        import app
        
        # Verify app object exists
        if not hasattr(app, 'app'):
            print("[LAUNCHER ERROR] No Flask app object found in app.py")
            sys.exit(1)
        
        if not hasattr(app, 'socketio'):
            print("[LAUNCHER ERROR] No SocketIO object found in app.py")
            sys.exit(1)
        
        print(f"[LAUNCHER] Starting server on port {port}...")
        print(f"[LAUNCHER] Access the application at: http://127.0.0.1:{port}")
        
        # Run the application
        app.socketio.run(
            app.app, 
            host='127.0.0.1', 
            port=port, 
            debug=False,
            use_reloader=False  # Prevent multiple launches
        )
        
    except ImportError as e:
        print(f"[LAUNCHER ERROR] Failed to import app module: {e}")
        print("\n[LAUNCHER] Troubleshooting:")
        print("1. Ensure all dependencies are installed: pip install -r requirements.txt")
        print("2. Check that app.py is in the same directory as this launcher")
        print("3. Verify Python environment is properly configured")
        traceback.print_exc()
        sys.exit(2)
        
    except Exception as e:
        print(f"[LAUNCHER ERROR] Failed to start application: {e}")
        traceback.print_exc()
        sys.exit(3)

if __name__ == "__main__":
    main()
