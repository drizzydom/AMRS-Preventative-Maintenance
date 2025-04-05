"""
Simple script to debug and fix Render routing issues
"""
import os
import sys

def apply_render_fixes():
    """
    Apply fixes specific to Render deployment
    Must be called before any routes are defined in app.py
    """
    print("[RENDER-FIX] Applying Render routing fixes...")
    
    # Clear SERVER_NAME which can cause routing issues
    os.environ.pop('SERVER_NAME', None)
    
    # Ensure PORT is properly set
    if not os.environ.get('PORT') and os.environ.get('RENDER_EXTERNAL_PORT'):
        os.environ['PORT'] = os.environ.get('RENDER_EXTERNAL_PORT')
        print(f"[RENDER-FIX] Set PORT to {os.environ['PORT']}")
    
    # Clear any problematic environment variables
    for var in ['SERVER_NAME', 'APPLICATION_ROOT', 'SCRIPT_NAME', 'FLASK_RUN_HOST']:
        if os.environ.get(var):
            print(f"[RENDER-FIX] Removed {var}={os.environ[var]}")
            del os.environ[var]

    # Print Render environment variables for debugging
    print("[RENDER-FIX] Render environment:")
    for key, value in os.environ.items():
        if 'RENDER' in key:
            print(f"  {key}={value}")

    print("[RENDER-FIX] Fixes applied successfully")
