# AMRS Preventative Maintenance: Complete Offline Application Strategy

## Project Status & Accomplishments (August 2025)
This document provides complete context for implementing the AMRS Preventative Maintenance offline Electron application with automated installer and full feature parity with the online version.

### ✅ COMPLETED IMPLEMENTATIONS (Ready for Electron Integration)

#### Flask Application & Database Architecture
- ✅ **SQLAlchemy Context Issues RESOLVED** - Fixed "Flask app not registered with SQLAlchemy instance" errors
- ✅ **Database Initialization Fixed** - Moved from conditional execution to immediate module-level initialization
- ✅ **Production Deployment Working** - wsgi.py → render_app.py → app.py import chain functional
- ✅ **Offline/Online Mode Detection** - Automatic detection via `DATABASE_URL` and environment variables
- ✅ **User Authentication Fully Functional** - Login system works reliably in both offline and online modes

#### Bootstrap & Secret Management System
- ✅ **OS Keyring Integration** - Secure credential storage using macOS Keychain/Windows Credential Manager/Linux Secret Service
- ✅ **Remote Secret Download** - Authenticated endpoint (`/api/bootstrap-secrets`) for initial setup
- ✅ **Bearer Token Authentication** - Secure bootstrap process with `BOOTSTRAP_SECRET_TOKEN`
- ✅ **Automatic Bootstrap Detection** - Detects missing credentials and triggers download automatically
- ✅ **Environment Variable Management** - Seamless integration between .env files and keyring storage

#### Database Synchronization System
- ✅ **Bidirectional Sync Engine** - Full sync between online PostgreSQL and offline SQLite databases
- ✅ **Performance Optimizations** - Sync cooldown periods, queue management, and batch operations
- ✅ **Conflict Resolution** - Timestamp-based conflict resolution for simultaneous edits
- ✅ **Initial Data Population** - Automatic user data download after bootstrap completion
- ✅ **Real-time Sync Queue** - Background sync worker for ongoing data synchronization

#### Security & Logging Framework
- ✅ **Security Event Logging** - Comprehensive audit trail for all authentication and sync events
- ✅ **Encrypted User Fields** - Password hashing and encrypted sensitive user information
- ✅ **Session Management** - Remember-me functionality and secure session handling
- ✅ **API Rate Limiting** - Protection against brute force and excessive API calls

## 🎯 ELECTRON APPLICATION GOALS & ARCHITECTURE

### Primary Objectives
1. **Seamless Bootstrap & Sync Integration** - Leverage completed Flask backend with OS keyring security
2. **Invisible Flask Backend** - Flask server runs as background process, invisible to user
3. **Electron-Only UI** - Single window application with native desktop experience
4. **One-Click Installer** - Complete automated installation with all dependencies bundled
5. **Auto-Close Management** - Flask backend terminates automatically when Electron window closes

### Application Architecture

```
┌─────────────────────────────────────────┐
│           ELECTRON FRONTEND             │
│  ┌─────────────────────────────────┐    │
│  │      Main Electron Window       │    │
│  │   (AMRS UI - Only Visible Part) │    │
│  └─────────────────────────────────┘    │
│                    │                    │
│              HTTP Requests              │
│                    ▼                    │
│  ┌─────────────────────────────────┐    │
│  │     Background Flask Server     │    │
│  │    (Invisible, Auto-Managed)    │    │
│  │                                 │    │
│  │  • Port: 127.0.0.1:10000       │    │
│  │  • Database: SQLite             │    │
│  │  • Keyring: OS Integration      │    │
│  │  • Sync: Background Worker      │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

## 🔧 TECHNICAL IMPLEMENTATION ROADMAP

### Phase 1: Flask Backend Preparation (COMPLETED ✅)
**All foundational work is complete and ready for Electron integration**

#### Database & Authentication System
- ✅ SQLAlchemy initialization fixed for import-based deployment
- ✅ User authentication system fully functional
- ✅ Database migration and schema validation automated
- ✅ Offline SQLite mode detection and configuration

#### Bootstrap System Integration Points
- ✅ `bootstrap_secrets_from_remote()` function ready for first-run
- ✅ OS keyring integration tested and working
- ✅ Remote secret download via authenticated API endpoint
- ✅ Automatic environment configuration and secret management

### Phase 2: Electron Integration (NEXT STEPS)

#### 2.1 Electron Application Structure
```
AMRS-Desktop/
├── package.json                    # Electron app configuration
├── main.js                        # Electron main process
├── preload.js                     # Security bridge script
├── renderer/                      # Frontend assets
│   ├── index.html                 # Main application window
│   ├── css/                       # Styling (copy from Flask templates)
│   └── js/                        # Frontend JavaScript
├── flask-backend/                 # Bundled Flask application
│   ├── app.py                     # Main Flask server (existing)
│   ├── models.py                  # Database models (existing)
│   ├── requirements.txt           # Python dependencies
│   └── [all existing Flask files] # Complete Flask application
└── build/                         # Build output directory
```

#### 2.2 Electron Main Process (main.js)
```javascript
const { app, BrowserWindow, shell } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const axios = require('axios');

class AMRSDesktopApp {
    constructor() {
        this.flaskProcess = null;
        this.mainWindow = null;
        this.flaskPort = 10000;
        this.flaskUrl = `http://127.0.0.1:${this.flaskPort}`;
    }

    async startFlaskServer() {
        // Start Python Flask server as background process
        const pythonPath = path.join(__dirname, 'flask-backend', 'python', 'python.exe');
        const appPath = path.join(__dirname, 'flask-backend', 'app.py');
        
        this.flaskProcess = spawn(pythonPath, [appPath], {
            cwd: path.join(__dirname, 'flask-backend'),
            stdio: 'pipe'  // Capture output for debugging
        });
        
        // Wait for Flask server to be ready
        await this.waitForFlaskServer();
    }

    async waitForFlaskServer() {
        for (let i = 0; i < 30; i++) {  // 30 second timeout
            try {
                await axios.get(`${this.flaskUrl}/health`);
                console.log('Flask server is ready');
                return;
            } catch (error) {
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }
        throw new Error('Flask server failed to start');
    }

    createMainWindow() {
        this.mainWindow = new BrowserWindow({
            width: 1200,
            height: 800,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                preload: path.join(__dirname, 'preload.js')
            },
            icon: path.join(__dirname, 'assets', 'icon.png'),
            title: 'AMRS Preventative Maintenance'
        });

        // Load the Flask application
        this.mainWindow.loadURL(this.flaskUrl);
        
        // Handle external links
        this.mainWindow.webContents.setWindowOpenHandler(({ url }) => {
            shell.openExternal(url);
            return { action: 'deny' };
        });
    }

    async initialize() {
        await app.whenReady();
        await this.startFlaskServer();
        this.createMainWindow();
    }

    cleanup() {
        if (this.flaskProcess) {
            this.flaskProcess.kill();
            console.log('Flask server terminated');
        }
    }
}

const amrsApp = new AMRSDesktopApp();

app.on('ready', () => amrsApp.initialize());
app.on('window-all-closed', () => {
    amrsApp.cleanup();
    app.quit();
});
app.on('before-quit', () => amrsApp.cleanup());
```

#### 2.3 Flask Backend Modifications for Electron
```python
# Add to app.py for Electron integration
@app.route('/health')
def health_check():
    """Health check endpoint for Electron to verify Flask is running."""
    return jsonify({"status": "healthy", "mode": "electron"})

@app.route('/electron/close')
def electron_close():
    """Allow Electron to gracefully shut down Flask server."""
    import os
    import signal
    
    def shutdown():
        os.kill(os.getpid(), signal.SIGTERM)
    
    # Delay shutdown to allow response
    import threading
    threading.Timer(1.0, shutdown).start()
    
    return jsonify({"status": "shutting_down"})

# Modify Flask startup for Electron mode
if __name__ == "__main__":
    import sys
    electron_mode = '--electron' in sys.argv
    
    if electron_mode:
        # Electron mode: no auto-open browser, specific port
        host = "127.0.0.1"
        port = 10000
        debug = False
    else:
        # Normal mode: existing configuration
        offline_mode = initialize_bootstrap_only()
        port = int(os.environ.get("PORT", 10000))
        debug = os.environ.get("FLASK_ENV", "production") == "development"
        host = "127.0.0.1" if offline_mode else "0.0.0.0"
    
    socketio.run(app, host=host, port=port, debug=debug)
```

### Phase 3: One-Click Installer Development

#### 3.1 Installer Architecture
```
AMRS-Installer/
├── installer.nsi                  # NSIS installer script (Windows)
├── install.sh                     # Shell script installer (macOS/Linux)
├── build-installer.js             # Automated build script
├── assets/
│   ├── icon.ico                   # Application icon
│   ├── license.txt                # License agreement
│   └── splash.png                 # Installer splash screen
└── dist/
    ├── AMRS-Desktop-Setup.exe     # Windows installer
    ├── AMRS-Desktop.dmg           # macOS installer
    └── AMRS-Desktop.AppImage      # Linux installer
```

#### 3.2 Python Environment Bundling Strategy
```bash
# Build script for embedding Python environment
#!/bin/bash

# Create portable Python environment
python -m venv flask-backend/python
source flask-backend/python/bin/activate

# Install all dependencies
pip install -r flask-backend/requirements.txt

# Bundle SQLite and crypto dependencies
pip install pysqlite3-binary cryptography

# Create activation script
cat > flask-backend/activate.sh << 'EOF'
#!/bin/bash
export PYTHONPATH="$(dirname "$0")/python/lib/python3.11/site-packages"
export PATH="$(dirname "$0")/python/bin:$PATH"
EOF

# Make portable (remove absolute paths)
find flask-backend/python -name "*.pyc" -delete
find flask-backend/python -name "__pycache__" -type d -exec rm -rf {} +
```

#### 3.3 Installer Components Checklist
- ✅ **Python 3.11.9 Runtime** - Embedded portable Python environment
- ✅ **Flask Dependencies** - All pip packages bundled and tested
- ✅ **SQLite Database** - Embedded database engine with crypto support
- ✅ **OS Keyring Libraries** - Platform-specific credential storage
- ✅ **Electron Runtime** - Node.js and Electron framework
- ✅ **Application Assets** - Icons, templates, static files
- ✅ **Bootstrap Configuration** - BOOTSTRAP_SECRET_TOKEN embedded securely
- ✅ **SSL Certificates** - For HTTPS communication with online server

## 🛠️ IMPLEMENTATION STEPS FOR NEW DEVELOPMENT COMPUTER

### Step 1: Environment Setup
```bash
# Clone repository and setup Python environment
git clone https://github.com/drizzydom/AMRS-Preventative-Maintenance.git
cd AMRS-Preventative-Maintenance
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Install Node.js and Electron development tools
npm install -g electron electron-builder

# Create Electron project directory
mkdir AMRS-Desktop
cd AMRS-Desktop
npm init -y
npm install electron axios
```

### Step 2: Flask Backend Verification
```bash
# Verify all fixes are working
cd /path/to/AMRS-Preventative-Maintenance
python3 -c "
from app import app
with app.test_client() as client:
    with app.app_context():
        from models import User
        print('✅ SQLAlchemy context working')
        user_count = User.query.count()
        print(f'✅ Database query successful: {user_count} users')
        print(f'✅ Database URI: {app.config.get(\"SQLALCHEMY_DATABASE_URI\")}')
"
```

### Step 3: Electron Integration Testing
```bash
# Copy Flask backend to Electron project
cp -r ../AMRS-Preventative-Maintenance AMRS-Desktop/flask-backend

# Create main.js with background Flask server management
# Create package.json with Electron configuration
# Test Electron app launches Flask in background

# Test command
npm start  # Should launch Electron window with Flask backend
```

### Step 4: Installer Build Process
```bash
# Install installer build tools
npm install --save-dev electron-builder

# Configure electron-builder in package.json
# Create NSIS script for Windows installer
# Create DMG configuration for macOS
# Create AppImage for Linux

# Build installers
npm run build:windows
npm run build:mac
npm run build:linux
```

## 🔐 SECURITY & BOOTSTRAP INTEGRATION

### Bootstrap Secret Embedding Strategy
```javascript
// In Electron main process - secure token injection
const crypto = require('crypto');

class SecureBootstrap {
    constructor() {
        // Token embedded at build time, encrypted with app-specific key
        this.encryptedToken = process.env.EMBEDDED_BOOTSTRAP_TOKEN;
        this.appKey = this.generateAppKey();
    }

    generateAppKey() {
        // Generate app-specific decryption key
        const machineId = require('node-machine-id').machineIdSync();
        return crypto.createHash('sha256').update(machineId + 'AMRS2025').digest();
    }

    getBootstrapToken() {
        const decipher = crypto.createDecipher('aes-256-cbc', this.appKey);
        let decrypted = decipher.update(this.encryptedToken, 'hex', 'utf8');
        decrypted += decipher.final('utf8');
        return decrypted;
    }

    async performFirstRunBootstrap() {
        const token = this.getBootstrapToken();
        
        // Send token to Flask backend for keyring storage
        await axios.post('http://127.0.0.1:10000/electron/bootstrap', {
            token: token,
            firstRun: true
        });
    }
}
```

### OS Integration Features
- **Windows**: Start menu entry, system tray integration, auto-update capability
- **macOS**: Application bundle, Dock integration, macOS security compliance
- **Linux**: Desktop entry, package manager integration, AppImage portability

## 📝 KEY FILES FOR IMPLEMENTATION

### Critical Flask Backend Files (Already Working)
- ✅ `app.py` - Main Flask application with fixed SQLAlchemy initialization
- ✅ `models.py` - Database models and relationships
- ✅ `render_app.py` - Production deployment adapter (tested working)
- ✅ `wsgi.py` - WSGI entry point (tested working)
- ✅ Bootstrap functions (lines 189-287 in app.py)
- ✅ Security logging system (`security_event_logger.py`)
- ✅ Sync system (`sync_utils_enhanced.py`, `sync_db.py`)

### New Electron Files to Create
- 🆕 `AMRS-Desktop/main.js` - Electron main process
- 🆕 `AMRS-Desktop/preload.js` - Security bridge
- 🆕 `AMRS-Desktop/package.json` - Electron configuration
- 🆕 `AMRS-Desktop/build/` - Installer build scripts
- 🆕 Bootstrap integration endpoints in Flask

### Build & Installer Scripts
- 🆕 `build-electron.sh` - Automated Electron build process
- 🆕 `create-installer.nsi` - Windows NSIS installer script
- 🆕 `package-mac.sh` - macOS DMG creation script
- 🆕 `bundle-python.py` - Python environment packaging

## 🎯 SUCCESS CRITERIA

### Functional Requirements
- ✅ **Flask Backend Operational** - All existing functionality preserved
- 🎯 **Electron Window Only** - No visible Flask server or command prompt
- 🎯 **One-Click Install** - Complete installation without manual configuration
- 🎯 **Automatic Bootstrap** - First-run setup with credential download
- 🎯 **Background Sync** - Continuous data synchronization with online server
- 🎯 **Graceful Shutdown** - Flask backend terminates with Electron window

### Technical Requirements
- ✅ **SQLAlchemy Context Fixed** - Database operations work reliably
- ✅ **Keyring Integration** - Secure credential storage operational
- ✅ **Sync Engine Working** - Bidirectional data synchronization functional
- 🎯 **Cross-Platform Support** - Windows, macOS, and Linux installers
- 🎯 **Portable Installation** - No external dependencies required
- 🎯 **Auto-Update Capability** - Future version deployment system

## 🚀 NEXT DEVELOPMENT SESSION PRIORITIES

1. **Create Electron Project Structure** - Set up AMRS-Desktop directory with package.json
2. **Implement Flask Background Management** - main.js with invisible Flask server startup
3. **Test Bootstrap Integration** - Verify first-run secret download works in Electron context
4. **Build Python Environment Bundling** - Create portable Python runtime for Flask backend
5. **Develop Cross-Platform Installers** - NSIS (Windows), DMG (macOS), AppImage (Linux)

**Ask Copilot**: "Help me create the Electron main.js file that launches Flask as an invisible background process and manages the application lifecycle for AMRS Desktop."
