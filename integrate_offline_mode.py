#!/usr/bin/env python3
"""
Utility script to integrate offline mode components into the main application.
This script performs the necessary modifications to add offline functionality
to the main AMRS Preventative Maintenance application.
"""
import os
import sys
import shutil
import re
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='[OFFLINE_INTEGRATION] %(levelname)s - %(message)s')
logger = logging.getLogger('offline_integration')

# Define workspace root
WORKSPACE_ROOT = os.path.dirname(os.path.abspath(__file__))

def backup_file(file_path):
    """Create a backup of a file before modifying it"""
    backup_path = f"{file_path}.bak"
    if os.path.exists(file_path):
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
    return backup_path

def modify_app_py():
    """Modify app.py to add offline mode support"""
    app_path = os.path.join(WORKSPACE_ROOT, 'app.py')
    backup_file(app_path)
    
    with open(app_path, 'r') as f:
        content = f.read()
    
    # Add imports for offline mode
    if 'from db_controller import DatabaseController' not in content:
        import_section = re.search(r'import.*?from.*?\n\n', content, re.DOTALL)
        if import_section:
            modified_imports = import_section.group(0)
            modified_imports = modified_imports.rstrip() + '\nfrom db_controller import DatabaseController\n\n'
            content = content.replace(import_section.group(0), modified_imports)
    
    # Add offline mode configuration
    if 'OFFLINE_MODE' not in content:
        config_section = re.search(r'# Configure.*?app\.config.*?\n\n', content, re.DOTALL)
        if config_section:
            modified_config = config_section.group(0)
            modified_config = modified_config.rstrip() + '\n\n# Offline mode configuration\napp.config[\'OFFLINE_MODE\'] = os.environ.get(\'OFFLINE_MODE\', \'false\').lower() == \'true\'\n\n'
            content = content.replace(config_section.group(0), modified_config)
    
    # Add offline mode context processor
    if 'inject_offline_mode' not in content:
        context_processor_code = """
@app.context_processor
def inject_offline_mode():
    return {'offline_mode': app.config.get('OFFLINE_MODE', False)}
"""
        if '@app.context_processor' in content:
            last_context_processor = re.search(r'@app\.context_processor.*?def .*?\(\).*?\n}', content, re.DOTALL)
            if last_context_processor:
                content = content.replace(last_context_processor.group(0), 
                                         last_context_processor.group(0) + '\n\n' + context_processor_code)
        else:
            # Add it before the routes
            routes_section = re.search(r'# Routes.*?@app\.route', content, re.DOTALL)
            if routes_section:
                content = content.replace(routes_section.group(0), 
                                         context_processor_code + '\n\n' + routes_section.group(0))
    
    # Add API endpoints for offline sync
    if 'api_connection_status' not in content:
        route_code = """
# Offline mode API endpoints
@app.route('/api/connection/status', methods=['GET'])
def api_connection_status():
    \"\"\"API endpoint to check connection status\"\"\"
    offline_mode = app.config.get('OFFLINE_MODE', False)
    return jsonify({
        'status': 'offline_mode' if offline_mode else 'connected',
        'offline_mode': offline_mode,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/sync/status', methods=['GET'])
def api_sync_status():
    \"\"\"API endpoint to check sync status\"\"\"
    if app.config.get('OFFLINE_MODE', False):
        from db_controller import db_controller
        last_sync = db_controller.get_last_sync_time()
        pending_sync = db_controller.get_pending_sync_count()
        
        return jsonify({
            'last_sync': last_sync,
            'pending_sync': pending_sync,
            'offline_mode': True
        })
    else:
        return jsonify({
            'last_sync': datetime.utcnow().isoformat(),
            'pending_sync': {'total': 0},
            'offline_mode': False
        })

@app.route('/api/sync/trigger', methods=['POST'])
@login_required
def api_trigger_sync():
    \"\"\"API endpoint to trigger data synchronization\"\"\"
    if app.config.get('OFFLINE_MODE', False):
        from db_controller import db_controller
        success = db_controller.update_last_sync_time()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Sync completed successfully',
                'offline_mode': True
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Sync failed',
                'offline_mode': True
            })
    else:
        return jsonify({
            'success': True,
            'message': 'Application is in online mode, no sync needed',
            'offline_mode': False
        })
"""
        # Add at the end of the file
        content += '\n' + route_code
    
    # Write modified content back to file
    with open(app_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Modified {app_path} to add offline mode support")

def modify_templates():
    """Modify templates to add offline mode indicators"""
    base_template = os.path.join(WORKSPACE_ROOT, 'templates', 'base.html')
    if os.path.exists(base_template):
        backup_file(base_template)
        
        with open(base_template, 'r') as f:
            content = f.read()
        
        # Add offline.js script
        if 'offline.js' not in content:
            script_section = re.search(r'{% block scripts %}.*?{% endblock %}', content, re.DOTALL)
            if script_section:
                modified_scripts = script_section.group(0).replace(
                    '{% endblock %}',
                    '    {% if offline_mode is defined and offline_mode %}\n'
                    '    <script src="{{ url_for(\'static\', filename=\'js/offline.js\') }}"></script>\n'
                    '    {% endif %}\n'
                    '{% endblock %}'
                )
                content = content.replace(script_section.group(0), modified_scripts)
        
        # Add offline indicator in navbar
        if 'connection-status' not in content:
            navbar_section = re.search(r'<nav.*?</nav>', content, re.DOTALL)
            if navbar_section:
                nav_content = navbar_section.group(0)
                nav_items = re.search(r'<ul class="navbar-nav.*?</ul>', nav_content, re.DOTALL)
                if nav_items:
                    modified_nav_items = nav_items.group(0).replace(
                        '</ul>',
                        '    {% if offline_mode is defined and offline_mode %}\n'
                        '    <li class="nav-item ms-2">\n'
                        '        <div class="d-flex align-items-center">\n'
                        '            <span class="nav-link">Status: <span id="connection-status" class="status-offline">Offline</span></span>\n'
                        '        </div>\n'
                        '    </li>\n'
                        '    <li class="nav-item">\n'
                        '        <button id="sync-button" class="btn btn-sm btn-outline-light ms-2" onclick="triggerSync()">Sync</button>\n'
                        '    </li>\n'
                        '    {% endif %}\n'
                        '</ul>'
                    )
                    content = content.replace(nav_items.group(0), modified_nav_items)
        
        # Write modified content back to file
        with open(base_template, 'w') as f:
            f.write(content)
        
        logger.info(f"Modified {base_template} to add offline mode indicators")

def copy_offline_files():
    """Copy necessary files for offline mode"""
    # Make sure static/js directory exists
    js_dir = os.path.join(WORKSPACE_ROOT, 'static', 'js')
    os.makedirs(js_dir, exist_ok=True)
    
    # Copy offline.js if it's not already there
    offline_js = os.path.join(js_dir, 'offline.js')
    if not os.path.exists(offline_js):
        shutil.copy2(
            os.path.join(WORKSPACE_ROOT, 'static', 'js', 'offline.js'), 
            offline_js
        )
        logger.info(f"Copied offline.js to {offline_js}")
    
    # Ensure db_controller.py is in the root directory
    db_controller = os.path.join(WORKSPACE_ROOT, 'db_controller.py')
    if not os.path.exists(db_controller):
        source_controller = os.path.join(WORKSPACE_ROOT, 'db_controller.py')
        if os.path.exists(source_controller):
            shutil.copy2(source_controller, db_controller)
            logger.info(f"Copied db_controller.py to {db_controller}")
        else:
            logger.error("db_controller.py not found!")

def main():
    """Main function to integrate offline mode"""
    print("AMRS Preventative Maintenance - Offline Mode Integration")
    print("======================================================")
    print("This script will integrate offline mode into the main application.")
    print("Make sure you have committed your changes before proceeding.")
    print()
    
    proceed = input("Do you want to proceed? (y/n): ").lower().strip()
    if proceed != 'y':
        print("Integration aborted.")
        return
    
    try:
        # Create backups directory
        backup_dir = os.path.join(WORKSPACE_ROOT, 'backups', f'offline_integration_{int(datetime.now().timestamp())}')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Perform integration steps
        copy_offline_files()
        modify_app_py()
        modify_templates()
        
        print("\nOffline mode integration completed successfully!")
        print("Please check the modified files and make any necessary adjustments.")
        print("See OFFLINE_MODE_README.md for more information on the offline mode implementation.")
        
    except Exception as e:
        logger.error(f"Error during integration: {e}")
        print(f"\nError during integration: {e}")
        print("Please check the logs for more information.")
        print("You may need to restore from backups.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
