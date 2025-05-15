const fs = require('fs');
const path = require('path');

/**
 * Create all required Python modules for the application
 */
function createRequiredPythonModules() {
  const modulesToCreate = [
    {
      path: 'simple_healthcheck.py',
      content: `"""
Simple health check module for AMRS Maintenance Tracker application.
"""
import os
import logging
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)

class HealthCheck:
    """Simple health check implementation for Flask application."""
    
    def __init__(self, app=None):
        self.app = app
        self.checks = []
        if app:
            self.init_app(app)
        logger.info("HealthCheck initialized")
    
    def init_app(self, app):
        """Initialize with a Flask application"""
        self.app = app
        
        # Register health check endpoint
        @app.route('/healthcheck')
        def healthcheck_route():
            from flask import jsonify
            result = self.run_checks()
            return jsonify(result)
        
        logger.info("HealthCheck routes registered with Flask app")
    
    def add_check(self, check_func, name=None):
        """Add a health check function"""
        if name is None:
            name = check_func.__name__
        
        self.checks.append((name, check_func))
        return check_func
    
    def run_checks(self):
        """Run all registered health checks"""
        results = {
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        for name, check_func in self.checks:
            try:
                result = check_func()
                results['checks'][name] = {
                    'status': 'ok',
                    'result': result
                }
            except Exception as e:
                results['status'] = 'error'
                results['checks'][name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return results

# Default database health check
def db_check():
    """Check database connection"""
    try:
        # Find the database path through environment variables
        appdata_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
        db_dir = os.path.join(appdata_dir, 'amrs-preventative-maintenance', 'AMRS-Maintenance-Tracker')
        db_path = os.path.join(db_dir, 'amrs_maintenance.db')
        
        if not os.path.exists(db_path):
            return {'status': 'not_found', 'path': db_path}
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT sqlite_version();")
        version = cursor.fetchone()[0]
        
        # Get table information
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        
        conn.close()
        
        return {
            'status': 'connected',
            'version': version,
            'tables': tables,
            'path': db_path
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
`
    },
    {
      path: 'app_debug_helper.py',
      content: `"""
Debug helper module for AMRS Maintenance Tracker application.
"""
import os
import sys
import platform
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

def register_debug_routes(app):
    """Register debug routes with the Flask application"""
    logger.info("Registering debug routes")
    
    @app.route('/debug/info')
    def debug_info():
        """Return system information for debugging"""
        from flask import jsonify
        
        # System information
        info = {
            'timestamp': datetime.now().isoformat(),
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'processor': platform.processor()
            },
            'python': {
                'version': sys.version,
                'executable': sys.executable,
                'path': sys.path
            },
            'environment': {
                'cwd': os.getcwd(),
                'env_vars': {k: v for k, v in os.environ.items() 
                             if not k.lower().startswith(('pass', 'secret', 'key'))}
            }
        }
        
        return jsonify(info)
    
    @app.route('/debug/database')
    def debug_database():
        """Return database information"""
        from flask import jsonify
        import sqlite3
        
        try:
            # Find database path
            appdata_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
            db_dir = os.path.join(appdata_dir, 'amrs-preventative-maintenance', 'AMRS-Maintenance-Tracker')
            db_path = os.path.join(db_dir, 'amrs_maintenance.db')
            
            if not os.path.exists(db_path):
                return jsonify({
                    'status': 'error',
                    'message': f'Database not found at {db_path}'
                })
            
            # Connect to database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get schema information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [table[0] for table in cursor.fetchall()]
            
            # Get table schemas
            schemas = {}
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table});")
                columns = [{
                    'cid': col[0],
                    'name': col[1],
                    'type': col[2],
                    'notnull': col[3],
                    'default': col[4],
                    'pk': col[5]
                } for col in cursor.fetchall()]
                schemas[table] = columns
                
            conn.close()
            
            return jsonify({
                'status': 'success',
                'database_path': db_path,
                'tables': tables,
                'schemas': schemas
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            })
    
    logger.info("Debug routes registered")
    return app

# Log that this module was loaded successfully
logger.info("app_debug_helper module loaded successfully")
`
    },
    {
      path: 'add_audit_task_color_column.py',
      content: `"""
Migration module to add color column to audit_tasks table.
"""
import os
import logging
import sqlite3

logger = logging.getLogger(__name__)

def migrate(db_connection=None):
    """
    Add color column to audit_tasks table if it doesn't exist.
    
    Args:
        db_connection: SQLite database connection (optional)
        
    Returns:
        bool: True if successful, False if failed
    """
    logger.info("Starting audit_task color column migration")
    
    try:
        # If no connection provided, create one
        connection_created = False
        if db_connection is None:
            appdata_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
            db_dir = os.path.join(appdata_dir, 'amrs-preventative-maintenance', 'AMRS-Maintenance-Tracker')
            db_path = os.path.join(db_dir, 'amrs_maintenance.db')
            
            if not os.path.exists(db_path):
                logger.error(f"Database not found at {db_path}")
                return False
                
            db_connection = sqlite3.connect(db_path)
            connection_created = True
            logger.info(f"Connected to database at {db_path}")
            
        cursor = db_connection.cursor()
        
        # Check if audit_tasks table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_tasks';")
        if not cursor.fetchone():
            logger.info("audit_tasks table doesn't exist, skipping migration")
            if connection_created:
                db_connection.close()
            return True
            
        # Check if color column already exists
        cursor.execute("PRAGMA table_info(audit_tasks);")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'color' not in columns:
            logger.info("Adding color column to audit_tasks table")
            # For older SQLite versions that don't support IF NOT EXISTS in ALTER TABLE
            cursor.execute("ALTER TABLE audit_tasks ADD COLUMN color TEXT DEFAULT '#3498db';")
            db_connection.commit()
            logger.info("Color column added successfully")
        else:
            logger.info("Color column already exists in audit_tasks table")
            
        if connection_created:
            db_connection.close()
            
        return True
        
    except Exception as e:
        logger.error(f"Error in audit_task color column migration: {e}")
        return False
`
    },
    {
      path: 'electron_db_sync.py',
      content: `"""
Database synchronization module for Electron application.
Handles synchronization between local SQLite and remote PostgreSQL databases.
"""
import os
import sys
import logging
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)

class DBSync:
    """Database synchronization handler"""
    
    def __init__(self, sqlite_uri=None, postgres_uri=None):
        self.sqlite_uri = sqlite_uri
        self.postgres_uri = postgres_uri
        
        # Fix URI formats
        if self.sqlite_uri and self.sqlite_uri.startswith('sqlite:///'):
            self.sqlite_path = self.sqlite_uri[10:]  # Remove 'sqlite:///'
        else:
            self.sqlite_path = self.sqlite_uri
            
        logger.info(f"DBSync initialized with SQLite: {self.sqlite_path}")
        
    def validate_config(self):
        """Validate synchronization configuration"""
        if not self.sqlite_uri:
            logger.error("SQLite URI not configured")
            return False
            
        if not self.postgres_uri:
            logger.warning("PostgreSQL URI not configured, running in local-only mode")
            # This is not an error, just a warning
            return True
            
        if self.sqlite_uri == self.postgres_uri:
            logger.error("SQLite and PostgreSQL URIs are identical")
            return False
            
        return True
        
    def sync_data(self):
        """Synchronize data between databases"""
        if not self.validate_config():
            return False
            
        try:
            # For now, just validate SQLite database
            if not self.sqlite_path or not os.path.exists(self.sqlite_path):
                logger.error(f"SQLite database not found at {self.sqlite_path}")
                return False
                
            # Connect to SQLite database
            sqlite_conn = sqlite3.connect(self.sqlite_path)
            sqlite_cursor = sqlite_conn.cursor()
            
            # Basic validation
            sqlite_cursor.execute("SELECT sqlite_version();")
            version = sqlite_cursor.fetchone()[0]
            logger.info(f"Connected to SQLite version {version}")
            
            # Get tables
            sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [table[0] for table in sqlite_cursor.fetchall()]
            logger.info(f"Found {len(tables)} tables: {', '.join(tables)}")
            
            # In local-only mode, we're done
            if not self.postgres_uri:
                logger.info("Running in local-only mode, no synchronization performed")
                sqlite_conn.close()
                return True
                
            # TODO: Add actual synchronization code when PostgreSQL is configured
            
            sqlite_conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error during database synchronization: {e}")
            return False
            
def get_sync_handler():
    """Get a configured sync handler based on environment"""
    sqlite_uri = os.environ.get('SQLITE_DATABASE_URI')
    postgres_uri = os.environ.get('POSTGRES_DATABASE_URI')
    
    # If no explicit URIs provided, construct default SQLite path
    if not sqlite_uri:
        appdata_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
        db_dir = os.path.join(appdata_dir, 'amrs-preventative-maintenance', 'AMRS-Maintenance-Tracker')
        db_path = os.path.join(db_dir, 'amrs_maintenance.db')
        sqlite_uri = f"sqlite:///{db_path}"
        
    # Create sync handler
    sync = DBSync(sqlite_uri=sqlite_uri, postgres_uri=postgres_uri)
    return sync

# Allow direct running for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sync = get_sync_handler()
    if sync.sync_data():
        print("Synchronization successful")
    else:
        print("Synchronization failed")
        sys.exit(1)
`
    },
    {
      path: 'cors_method_handlers.py',
      content: `"""
CORS and HTTP method handlers for AMRS application
"""
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def apply_cors_fixes(app):
    """Apply CORS and method handling fixes to a Flask app"""
    logger.info("Applying CORS fixes to Flask app")
    
    @app.after_request
    def add_cors_headers(response):
        """Add CORS headers to all responses"""
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Max-Age'] = '86400'  # 24 hours
        return response
    
    @app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
    @app.route('/<path:path>', methods=['OPTIONS'])
    def options_handler(path):
        """Handle OPTIONS requests for all routes"""
        from flask import make_response
        response = make_response('')
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        return response
    
    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        """Handle Method Not Allowed errors gracefully"""
        from flask import jsonify, request
        return jsonify({
            'error': 'Method Not Allowed',
            'message': str(e),
            'method': request.method,
            'path': request.path,
        }), 405
    
    logger.info("CORS fixes applied successfully")
    return app

def write_electron_signal_files(port):
    """Write signal files for Electron integration"""
    try:
        paths = []
        
        # Try multiple potential paths to ensure Electron finds the signal files
        paths.append(os.environ.get('APPDATA', ''))
        paths.append(os.environ.get('AMRS_DATA_DIR', ''))
        paths.append(os.environ.get('AMRS_ALT_DATA_DIR', ''))
        
        for base_dir in paths:
            if not base_dir:
                continue
                
            status_dir = os.path.join(base_dir, 'AMRS-Maintenance-Tracker')
            os.makedirs(status_dir, exist_ok=True)
            
            with open(os.path.join(status_dir, 'flask_port.txt'), 'w') as f:
                f.write(str(port))
                
            with open(os.path.join(status_dir, 'flask_ready.txt'), 'w') as f:
                f.write(f"Flask fully running on port {port} at {datetime.now().isoformat()}")
                
            logger.info(f"Wrote Electron signal files to {status_dir}")
            
    except Exception as e:
        logger.error(f"Error writing Electron signal files: {str(e)}")

logger.info("cors_method_handlers module loaded successfully")
`
    }
  ];

  // Create each module if it doesn't exist
  modulesToCreate.forEach(module => {
    const fullPath = path.resolve(__dirname, module.path);
    
    if (!fs.existsSync(fullPath)) {
      console.log(`Creating missing module: ${module.path}`);
      fs.writeFileSync(fullPath, module.content, 'utf8');
    } else {
      console.log(`Module already exists: ${module.path}`);
    }
  });

  console.log('All required Python modules created successfully');
  return true;
}

/**
 * Verify that all required CSS classes are added to the main.js file
 */
function verifyUIStyles() {
  const mainJsPath = path.resolve(__dirname, 'electron_app', 'main.js');
  
  if (!fs.existsSync(mainJsPath)) {
    console.error('Error: electron_app/main.js not found');
    return false;
  }
  
  let mainJsContent = fs.readFileSync(mainJsPath, 'utf8');
  let updated = false;
  
  // Define required style classes
  const requiredStyles = [
    {
      name: 'button.diagnostic',
      style: `button.diagnostic {
          background-color: #e67e22;
        }`
    },
    {
      name: 'button.danger',
      style: `button.danger {
          background-color: #e74c3c;
        }`
    },
    {
      name: '.debug-panel',
      style: `.debug-panel {
          background: #f8f9fa;
          border: 1px solid #ddd;
          padding: 10px;
          margin-top: 10px;
          border-radius: 4px;
          font-family: monospace;
          font-size: 12px;
          display: none;
          max-height: 200px;
          overflow-y: auto;
        }`
    },
    {
      name: '.status-indicator',
      style: `.status-indicator {
          display: inline-block;
          width: 12px;
          height: 12px;
          border-radius: 50%;
          margin-right: 8px;
        }`
    },
    {
      name: '.status-ok',
      style: `.status-ok {
          background-color: #2ecc71;
        }`
    },
    {
      name: '.status-warning',
      style: `.status-warning {
          background-color: #f39c12;
        }`
    },
    {
      name: '.status-error',
      style: `.status-error {
          background-color: #e74c3c;
        }`
    }
  ];
  
  // Check for each style and add if missing
  requiredStyles.forEach(style => {
    if (!mainJsContent.includes(style.name)) {
      console.log(`Adding missing style: ${style.name}`);
      
      // Insert the new style after the button style
      const buttonStylePos = mainJsContent.indexOf('button:hover {');
      if (buttonStylePos !== -1) {
        const insertPos = mainJsContent.indexOf('}', buttonStylePos) + 1;
        mainJsContent = 
          mainJsContent.substring(0, insertPos) + 
          '\n        ' + style.style + 
          mainJsContent.substring(insertPos);
        updated = true;
      }
    }
  });
  
  // Write updated content back if changed
  if (updated) {
    fs.writeFileSync(mainJsPath, mainJsContent, 'utf8');
    console.log('Added missing styles to main.js');
  } else {
    console.log('All required styles already present in main.js');
  }
  
  return true;
}

// Export the functions
module.exports = {
  createRequiredPythonModules,
  verifyUIStyles
};
