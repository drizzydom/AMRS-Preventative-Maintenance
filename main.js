const { app, BrowserWindow, shell, Menu, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const net = require('net');
const os = require('os');
const { autoUpdater } = require('electron-updater');
const { ipcMain } = require('electron');

// --- Electron Updater Integration ---
// Flag to track if we've already checked for updates
let hasCheckedForUpdates = false;
// Track if update check was triggered manually
let manualUpdateCheck = false;

const UPDATE_FEED_URL = 'https://f005.backblazeb2.com/file/amrs-pm-updates/';

// Function to safely check for updates
function checkForUpdatesWhenReady() {
    if (hasCheckedForUpdates && !manualUpdateCheck) {
        writeLog(`[AutoUpdate] Already checked for updates, skipping duplicate check`);
        return;
    }
    writeLog(`[AutoUpdate] Attempting to check for updates...`);
    writeLog(`[AutoUpdate] Feed URL: ${UPDATE_FEED_URL}`);
    writeLog(`[AutoUpdate] Current version: ${app.getVersion()}`);
    autoUpdater.setFeedURL({ url: UPDATE_FEED_URL });
    autoUpdater.checkForUpdatesAndNotify();
}

autoUpdater.on('checking-for-update', () => {
    writeLog(`[AutoUpdate] Checking for updates...`);
    writeLog(`[AutoUpdate] Making request to: ${UPDATE_FEED_URL}latest.yml`);
});

autoUpdater.on('update-not-available', (info) => {
    writeLog(`[AutoUpdate] Update not available - current version is latest`);
    writeLog(`[AutoUpdate] Response info: ${JSON.stringify(info, null, 2)}`);
    if (manualUpdateCheck && mainWindow) {
        dialog.showMessageBox(mainWindow, {
            type: 'info',
            title: 'No Updates Available',
            message: 'Your application is already up to date.',
            buttons: ['OK']
        });
    }
    manualUpdateCheck = false;
});

autoUpdater.on('update-available', (info) => {
    writeLog(`[AutoUpdate] Update available: ${info.version}`);
    writeLog(`[AutoUpdate] Update info: ${JSON.stringify(info, null, 2)}`);
    if (mainWindow) {
        dialog.showMessageBox(mainWindow, {
            type: 'info',
            title: 'Update Available',
            message: `A new version (${info.version}) is available and will be downloaded automatically.`,
            buttons: ['OK']
        });
    }
});

autoUpdater.on('update-downloaded', (info) => {
    writeLog(`[AutoUpdate] Update downloaded: ${info.version}`);
    writeLog(`[AutoUpdate] Download info: ${JSON.stringify(info, null, 2)}`);
    if (mainWindow) {
        dialog.showMessageBox(mainWindow, {
            type: 'info',
            title: 'Update Ready',
            message: `Update ${info.version} has been downloaded. The application will now restart to install the update.`,
            buttons: ['Restart Now']
        }).then(() => {
            autoUpdater.quitAndInstall();
        });
    } else {
        autoUpdater.quitAndInstall();
    }
});

autoUpdater.on('error', (err) => {
    writeLog(`[AutoUpdate] Error: ${err == null ? 'unknown' : err.message}`);
    writeLog(`[AutoUpdate] Error stack: ${err ? err.stack : 'No stack trace'}`);
    writeLog(`[AutoUpdate] Error details: ${JSON.stringify(err, null, 2)}`);
    
    // Try to get more specific error information
    if (err && err.code) {
        writeLog(`[AutoUpdate] Error code: ${err.code}`);
    }
    if (err && err.errno) {
        writeLog(`[AutoUpdate] Error errno: ${err.errno}`);
    }
    
    if (mainWindow) {
        dialog.showMessageBox(mainWindow, {
            type: 'warning',
            title: 'Update Check Failed',
            message: `Failed to check for updates: ${err ? err.message : 'Unknown error'}. Check the logs for more details.`,
            buttons: ['OK']
        });
    }
});

let mainWindow;
let splashWindow;
let flaskProcess;
const FLASK_PORT = 10000;

// Set up logging
const LOG_FILE = path.join(os.tmpdir(), 'amrs-maintenance-tracker.log');
const logMessages = [];

function writeLog(message) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}`;
    
    // Keep in memory for debug window
    logMessages.push(logMessage);
    if (logMessages.length > 1000) {
        logMessages.shift(); // Keep only last 1000 messages
    }
    
    // Write to console (for development)
    console.log(message);
    
    // Write to file (for production debugging)
    try {
        fs.appendFileSync(LOG_FILE, logMessage + '\n');
    } catch (error) {
        console.error('Failed to write to log file:', error.message);
    }
}

// Initialize log file
try {
    fs.writeFileSync(LOG_FILE, `=== AMRS Maintenance Tracker Log Started ===\n`);
    writeLog(`Log file created at: ${LOG_FILE}`);
    writeLog(`Platform: ${process.platform} ${process.arch}`);
    writeLog(`Electron version: ${process.versions.electron}`);
    writeLog(`Node version: ${process.versions.node}`);
    writeLog(`App version: ${app.getVersion()}`);
} catch (error) {
    console.error('Failed to initialize log file:', error.message);
}

// Function to check if port is available
function isPortFree(port) {
    return new Promise((resolve) => {
        const server = net.createServer();
        server.listen(port, () => {
            server.once('close', () => resolve(true));
            server.close();
        });
        server.on('error', () => resolve(false));
    });
}

// Function to wait for Flask to start
function waitForFlask(port, timeout = 60000) {
    return new Promise((resolve, reject) => {
        const startTime = Date.now();
        let progressInterval;
        let lastProgress = 0;
        writeLog(`[Flask Wait] Starting Flask connection wait with ${timeout}ms timeout`);
        // Start progress updates for Flask startup
        progressInterval = setInterval(() => {
            const elapsed = Date.now() - startTime;
            const timeoutProgress = Math.min(elapsed / timeout, 0.95); // Never reach 100% via timeout
            let adjustedProgress = 95 + (timeoutProgress * 4);
            // Make progress more granular by using smaller increments
            adjustedProgress = Math.max(lastProgress, adjustedProgress);
            lastProgress = adjustedProgress;
            writeLog(`[Flask Wait] Progress update: elapsed=${elapsed}ms, progress=${adjustedProgress.toFixed(1)}%`);
            if (elapsed < 2000) {
                updateSplashStatus('Starting web server...', adjustedProgress);
            } else if (elapsed < 6000) {
                updateSplashStatus('Loading security keyring...', adjustedProgress);
            } else if (elapsed < 12000) {
                updateSplashStatus('Initializing database...', adjustedProgress);
            } else if (elapsed < 18000) {
                updateSplashStatus('Setting up application...', adjustedProgress);
            } else {
                updateSplashStatus('Finalizing startup...', adjustedProgress);
            }
        }, 250); // Update every 250ms for smoother progress
        
        function check() {
            const socket = new net.Socket();
            socket.setTimeout(1000);
            
            socket.on('connect', () => {
                socket.destroy();
                writeLog(`[Flask Wait] Flask connection successful after ${Date.now() - startTime}ms`);
                if (progressInterval) {
                    clearInterval(progressInterval);
                    writeLog(`[Flask Wait] Progress interval cleared`);
                }
                resolve();
            });
            
            socket.on('error', () => {
                if (Date.now() - startTime > timeout) {
                    if (progressInterval) {
                        clearInterval(progressInterval);
                    }
                    writeLog(`[Flask Wait] Flask startup timeout after ${timeout}ms`);
                    reject(new Error('Flask startup timeout'));
                } else {
                    setTimeout(check, 500);
                }
            });
            
            socket.on('timeout', () => {
                socket.destroy();
                if (Date.now() - startTime > timeout) {
                    if (progressInterval) {
                        clearInterval(progressInterval);
                    }
                    writeLog(`[Flask Wait] Flask startup timeout (socket timeout) after ${timeout}ms`);
                    reject(new Error('Flask startup timeout'));
                } else {
                    setTimeout(check, 500);
                }
            });
            
            socket.connect(port, '127.0.0.1');
        }
        
        check();
    });
}

// Function to create splash screen
function createSplashScreen() {
    splashWindow = new BrowserWindow({
        width: 480,
        height: 340,
        frame: false,
        alwaysOnTop: true,
        transparent: true,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'splash-preload.js')
        }
    });

    // Create splash screen HTML content with dynamic version
    const splashHTML = `
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
                color: white;
                border-radius: 10px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }
            .logo {
                font-size: 28px;
                font-weight: bold;
                margin-bottom: 15px;
                text-align: center;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }
            .version {
                font-size: 12px;
                opacity: 0.8;
                margin-bottom: 25px;
                text-align: center;
            }
            .loading-container {
                width: 320px;
                text-align: center;
            }
            .loading-bar {
                width: 100%;
                height: 6px;
                background: rgba(255,255,255,0.2);
                border-radius: 3px;
                overflow: hidden;
                margin: 20px 0;
                box-shadow: inset 0 1px 3px rgba(0,0,0,0.2);
            }
            .loading-progress {
                height: 100%;
                background: linear-gradient(90deg, #4CAF50, #45a049, #66BB6A);
                border-radius: 3px;
                transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
                width: 0%;
                position: relative;
                box-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
            }
            .loading-progress::after {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
                animation: shimmer 2s infinite;
            }
            @keyframes shimmer {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(100%); }
            }
            .status-text {
                font-size: 15px;
                opacity: 0.95;
                margin-top: 15px;
                min-height: 22px;
                font-weight: 500;
                transition: all 0.3s ease;
            }
            .progress-percent {
                font-size: 13px;
                opacity: 0.8;
                margin-top: 8px;
                font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
            }
            .spinner {
                border: 3px solid rgba(255,255,255,0.3);
                border-radius: 50%;
                border-top: 3px solid white;
                width: 24px;
                height: 24px;
                animation: spin 1s linear infinite;
                margin: 15px auto;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .info-text {
                font-size: 11px;
                opacity: 0.7;
                margin-top: 20px;
                max-width: 300px;
                line-height: 1.4;
                text-align: center;
            }
            .status-icon {
                display: inline-block;
                margin-right: 8px;
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
        </style>
    </head>
    <body>
        <div class="logo">🔧 AMRS Maintenance Tracker</div>
        <div class="version">Version ${require('electron').app.getVersion()}</div>
        <div class="loading-container">
            <div class="spinner"></div>
            <div class="loading-bar">
                <div class="loading-progress" id="progress"></div>
            </div>
            <div class="status-text" id="status"><span class="status-icon">⚙️</span>Initializing application...</div>
            <div class="progress-percent" id="percent">0%</div>
            <div class="info-text" id="info">Setting up your maintenance tracking system...</div>
        </div>
        <script>
            const statusMessages = {
                'Checking Python dependencies...': { icon: '🔍', info: 'Verifying required components are available...' },
                'Dependencies verified ✓': { icon: '✅', info: 'All required components found!' },
                'Installing required dependencies...': { icon: '📦', info: 'Downloading and installing packages...' },
                'Installing application dependencies...': { icon: '⬇️', info: 'This may take a few moments on first run...' },
                'Downloading packages...': { icon: '📡', info: 'Fetching latest package versions...' },
                'Installing packages...': { icon: '⚙️', info: 'Setting up application environment...' },
                'Dependencies installed successfully ✓': { icon: '✅', info: 'Installation completed successfully!' },
                'Starting Flask backend...': { icon: '🚀', info: 'Launching web server...' },
                'Starting web server...': { icon: '🌐', info: 'Initializing server components...' },
                '🔐 Loading security keyring...': { icon: '🔐', info: 'This is the slowest step and may take 10-20 seconds...' },
                '🔐 Loading security keyring (this may take 15+ seconds)...': { icon: '🔐', info: 'Please wait while we access your secure credentials...' },
                '🔐 Security keyring loaded successfully': { icon: '✅', info: 'Secure credentials accessed successfully!' },
                '🔑 Loading application credentials...': { icon: '🔑', info: 'Retrieving stored configuration settings...' },
                '✅ All credentials loaded successfully': { icon: '✅', info: 'All security credentials loaded!' },
                '🗄️ Database connection established': { icon: '🗄️', info: 'Connected to maintenance database...' },
                '✅ Database schema validated': { icon: '✅', info: 'Database structure verified and ready...' },
                '🔄 Database migration completed': { icon: '🔄', info: 'Database updates applied successfully...' },
                '🔧 Database tables configured': { icon: '🔧', info: 'All database tables ready for use...' },
                '🎉 Application configured successfully': { icon: '🎉', info: 'All systems initialized and ready!' },
                '🌐 Web server started successfully': { icon: '🌐', info: 'Server is running and accepting connections...' },
                '⚙️ Initializing system components...': { icon: '⚙️', info: 'Setting up core application systems...' },
                '🔄 Preparing application...': { icon: '🔄', info: 'Finalizing application startup...' },
                'Initializing database...': { icon: '🗄️', info: 'Setting up data storage and security...' },
                'Setting up application...': { icon: '⚙️', info: 'Configuring application settings...' },
                'Finalizing startup...': { icon: '🎯', info: 'Almost ready to begin!' },
                'Application ready! ✓': { icon: '🎉', info: 'Welcome to AMRS Maintenance Tracker!' }
            };
            
            // Use the exposed electronAPI instead of require('electron')
            window.electronAPI.onSplashStatus((event, data) => {
                const statusEl = document.getElementById('status');
                const progressEl = document.getElementById('progress');
                const percentEl = document.getElementById('percent');
                const infoEl = document.getElementById('info');
                
                // Update progress bar and percentage
                progressEl.style.width = data.progress + '%';
                percentEl.textContent = Math.round(data.progress) + '%';
                
                // Update status message with icon
                const messageInfo = statusMessages[data.message];
                if (messageInfo) {
                    statusEl.innerHTML = \`<span class="status-icon">\${messageInfo.icon}</span>\${data.message}\`;
                    infoEl.textContent = messageInfo.info;
                } else {
                    statusEl.innerHTML = \`<span class="status-icon">⚙️</span>\${data.message}\`;
                    infoEl.textContent = 'Processing...';
                }
                
                // Add completion animation
                if (data.progress >= 100) {
                    setTimeout(() => {
                        document.querySelector('.spinner').style.display = 'none';
                        statusEl.style.color = '#4CAF50';
                        progressEl.style.background = 'linear-gradient(90deg, #4CAF50, #66BB6A)';
                    }, 500);
                }
            });
        </script>
    </body>
    </html>
    `;

    splashWindow.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(splashHTML));
    
    splashWindow.on('closed', () => {
        splashWindow = null;
    });

    return splashWindow;
}

// Function to update splash screen status
function updateSplashStatus(message, progress = 0) {
    writeLog(`[Splash] ${message} (${progress}%)`);
    if (splashWindow && !splashWindow.isDestroyed()) {
        try {
            splashWindow.webContents.send('splash-status', { message, progress });
            writeLog(`[Splash] Status update sent successfully: ${message} ${progress}%`);
        } catch (error) {
            writeLog(`[Splash] Error sending status update: ${error.message}`);
        }
    } else {
        writeLog(`[Splash] Cannot send status update - splash window not available`);
    }
}

// Function to close splash screen
function closeSplashScreen() {
    if (splashWindow && !splashWindow.isDestroyed()) {
        splashWindow.close();
        splashWindow = null;
    }
}

// Function to check if Python dependencies are installed
async function checkPythonDependencies(pythonPath) {
    updateSplashStatus('Checking Python dependencies...', 20);
    return new Promise((resolve) => {
        try {
            const checkProcess = spawn(pythonPath, ['-c', 'import flask; import sqlalchemy; print("Dependencies OK")'], {
                stdio: ['pipe', 'pipe', 'pipe']
            });
            
            let output = '';
            let errorOutput = '';
            
            checkProcess.stdout.on('data', (data) => {
                output += data.toString();
            });
            
            checkProcess.stderr.on('data', (data) => {
                errorOutput += data.toString();
            });
            
            checkProcess.on('close', (code) => {
                const success = code === 0 && output.includes('Dependencies OK');
                writeLog(`[Electron] Dependencies check: ${success ? 'PASSED' : 'FAILED'} (code: ${code})`);
                
                if (success) {
                    updateSplashStatus('Dependencies verified ✓', 30);
                } else {
                    updateSplashStatus('Installing required dependencies...', 25);
                }
                
                if (errorOutput) {
                    writeLog(`[Electron] Dependencies check stderr: ${errorOutput.trim()}`);
                }
                
                resolve(success);
            });
            
            checkProcess.on('error', (error) => {
                writeLog(`[Electron] Dependencies check error: ${error.message}`);
                if (process.platform === 'win32') {
                    writeLog(`[Electron] Windows error detected - this may indicate missing Visual C++ Runtime`);
                }
                updateSplashStatus('Installing required dependencies...', 25);
                resolve(false);
            });
        } catch (error) {
            writeLog(`[Electron] Dependencies check exception: ${error.message}`);
            updateSplashStatus('Installing required dependencies...', 25);
            resolve(false);
        }
    });
}

// Function to detect Windows version and show appropriate error messages
function getWindowsCompatibilityMessage(errorCode) {
    if (process.platform !== 'win32') return null;
    
    const os = require('os');
    const release = os.release();
    
    writeLog(`[Windows] OS Release: ${release}`);
    
    // Handle general Windows compatibility issues
    if (errorCode === 3221225781) {
        return {
            title: 'Windows Compatibility Issue',
            message: `This application requires Visual C++ Runtime libraries.

Please try:
1. Download and install Microsoft Visual C++ Redistributable for Visual Studio 2015-2022
2. Restart your computer
3. Try running the application again

If the issue persists, you may need to install Python 3.9 or higher manually and ensure all dependencies are installed.`
        };
    }
    
    return null;
}

// Function to show error dialog for Windows compatibility issues
function showWindowsCompatibilityError(errorInfo) {
    const { dialog } = require('electron');
    
    if (mainWindow && !mainWindow.isDestroyed()) {
        dialog.showMessageBox(mainWindow, {
            type: 'error',
            title: errorInfo.title,
            message: errorInfo.message,
            buttons: ['OK', 'Open Microsoft Download Center'],
            defaultId: 0
        }).then((result) => {
            if (result.response === 1) {
                require('electron').shell.openExternal('https://docs.microsoft.com/en-US/cpp/windows/latest-supported-vc-redist');
            }
        });
    }
}

// Function to install Python dependencies
async function installPythonDependencies(pythonPath) {
    updateSplashStatus('Installing Python dependencies (this may take a few minutes)...', 30);
    return new Promise((resolve) => {
        try {
            // Check if we're in a packaged app
            const isPackaged = !process.defaultApp;
            
            let requirementsPath = path.join(__dirname, 'requirements.txt');
            if (isPackaged) {
                // Try multiple possible locations for requirements.txt in packaged app
                const possiblePaths = [
                    path.join(process.resourcesPath, 'app.asar.unpacked', 'requirements.txt'),
                    path.join(process.resourcesPath, 'requirements.txt'),
                    path.join(__dirname, '..', 'requirements.txt'),
                    path.join(__dirname, 'requirements.txt')
                ];
                
                for (const testPath of possiblePaths) {
                    writeLog(`[Electron] Checking requirements.txt at: ${testPath}`);
                    if (fs.existsSync(testPath)) {
                        requirementsPath = testPath;
                        writeLog(`[Electron] Found requirements.txt at: ${testPath}`);
                        break;
                    }
                }
            }
            
            if (!fs.existsSync(requirementsPath)) {
                writeLog(`[Electron] Requirements file not found at: ${requirementsPath}`);
                updateSplashStatus('Error: Requirements file not found', 30);
                resolve(false);
                return;
            }
            
            writeLog(`[Electron] Installing dependencies from: ${requirementsPath}`);
            const installProcess = spawn(pythonPath, ['-m', 'pip', 'install', '--upgrade', 'pip'], {
                stdio: ['pipe', 'pipe', 'pipe']
            });
            
            let pipErrorOutput = '';
            installProcess.stderr.on('data', (data) => {
                pipErrorOutput += data.toString();
            });
            
            installProcess.on('close', (pipCode) => {
                if (pipCode === 0) {
                    updateSplashStatus('Installing application dependencies...', 40);
                    
                    const mainInstall = spawn(pythonPath, ['-m', 'pip', 'install', '-r', requirementsPath], {
                        stdio: ['pipe', 'pipe', 'pipe']
                    });
                    
                    let installProgress = 40;
                    mainInstall.stdout.on('data', (data) => {
                        const output = data.toString();
                        writeLog(`[Pip] ${output.trim()}`);
                        
                        // Update progress based on installation output
                        if (output.includes('Collecting')) {
                            installProgress = Math.min(installProgress + 2, 70);
                            updateSplashStatus('Downloading packages...', installProgress);
                        } else if (output.includes('Installing')) {
                            installProgress = Math.min(installProgress + 3, 85);
                            updateSplashStatus('Installing packages...', installProgress);
                        }
                    });
                    
                    mainInstall.stderr.on('data', (data) => {
                        writeLog(`[Pip Error] ${data.toString().trim()}`);
                    });
                    
                    mainInstall.on('close', (code) => {
                        const success = code === 0;
                        if (success) {
                            updateSplashStatus('Dependencies installed successfully ✓', 90);
                        } else {
                            updateSplashStatus('Failed to install dependencies', 30);
                            
                            // Check for Windows compatibility issues
                            const compatError = getWindowsCompatibilityMessage(code);
                            if (compatError) {
                                setTimeout(() => {
                                    showWindowsCompatibilityError(compatError);
                                }, 2000);
                            }
                        }
                        writeLog(`[Electron] Dependency installation ${success ? 'COMPLETED' : 'FAILED'} (code: ${code})`);
                        resolve(success);
                    });
                    
                    mainInstall.on('error', (error) => {
                        writeLog(`[Electron] Dependency installation error: ${error.message}`);
                        updateSplashStatus('Installation error occurred', 30);
                        
                        // Check for Windows compatibility issues
                        const compatError = getWindowsCompatibilityMessage(error.code || error.errno);
                        if (compatError) {
                            setTimeout(() => {
                                showWindowsCompatibilityError(compatError);
                            }, 2000);
                        }
                        
                        resolve(false);
                    });
                } else {
                    writeLog(`[Electron] Pip upgrade failed with code: ${pipCode}`);
                    if (pipErrorOutput) {
                        writeLog(`[Electron] Pip upgrade stderr: ${pipErrorOutput.trim()}`);
                    }
                    
                    updateSplashStatus('Failed to upgrade pip', 30);
                    
                    // Check for Windows compatibility issues even in pip upgrade failure
                    const compatError = getWindowsCompatibilityMessage(pipCode);
                    if (compatError) {
                        setTimeout(() => {
                            showWindowsCompatibilityError(compatError);
                        }, 2000);
                    }
                    
                    resolve(false);
                }
            });
            
            installProcess.on('error', (error) => {
                writeLog(`[Electron] Pip upgrade error: ${error.message}`);
                updateSplashStatus('Failed to upgrade pip', 30);
                resolve(false);
            });
        } catch (error) {
            writeLog(`[Electron] Dependency installation exception: ${error.message}`);
            updateSplashStatus('Installation exception occurred', 30);
            resolve(false);
        }
    });
}

// Function to start Flask backend
async function startFlaskServer() {
    updateSplashStatus('Starting Flask backend...', 10);
    writeLog('[Electron] Starting Flask backend...');
    
    // Check if port is available
    const portFree = await isPortFree(FLASK_PORT);
    if (!portFree) {
        writeLog(`[Electron] Port ${FLASK_PORT} is already in use`);
        updateSplashStatus('Port 10000 is already in use', 10);
        return false;
    }
    
    updateSplashStatus('Locating Python environment...', 15);
    
    // Determine Python executable path based on packaging
    let pythonPath;
    let resourcesPath;
    
    // Check if we're in a packaged app
    const isPackaged = !process.defaultApp;
    
    if (isPackaged) {
        // In packaged app, resources are in app.asar.unpacked/resources
        resourcesPath = path.join(process.resourcesPath, 'python');
        writeLog(`[Electron] Packaged app detected, resources path: ${process.resourcesPath}`);
        writeLog(`[Electron] Expected Python path: ${resourcesPath}`);
        
        // Check if the resources directory exists
        writeLog(`[Electron] Checking if resources directory exists: ${fs.existsSync(process.resourcesPath)}`);
        if (fs.existsSync(process.resourcesPath)) {
            const resourceContents = fs.readdirSync(process.resourcesPath);
            writeLog(`[Electron] Resources directory contents: ${JSON.stringify(resourceContents)}`);
        }
    } else {
        // In development, use local python folder
        resourcesPath = path.join(__dirname, 'python');
        writeLog('[Electron] Development mode, using local python folder');
    }
    
    if (process.platform === 'win32') {
        pythonPath = path.join(resourcesPath, 'python.exe');
    } else if (process.platform === 'darwin') {
        // On macOS, try multiple possible Python executable names
        const possiblePythonPaths = [
            path.join(resourcesPath, 'bin', 'python3.11'),  // Try direct binary first
            path.join(resourcesPath, 'bin', 'python3'),
            path.join(resourcesPath, 'bin', 'python'),
            path.join(resourcesPath, 'python3.11'),
            path.join(resourcesPath, 'python3'),
            path.join(resourcesPath, 'python')
        ];
        
        writeLog(`[Electron] Testing ${possiblePythonPaths.length} possible Python paths on macOS...`);
        for (const testPath of possiblePythonPaths) {
            writeLog(`[Electron] Testing Python path: ${testPath} - exists: ${fs.existsSync(testPath)}`);
            if (fs.existsSync(testPath)) {
                // Also check if it's executable
                try {
                    const stats = fs.statSync(testPath);
                    const isExecutable = !!(stats.mode & parseInt('111', 8));
                    writeLog(`[Electron] Python at ${testPath} - executable: ${isExecutable}`);
                    if (isExecutable) {
                        pythonPath = testPath;
                        writeLog(`[Electron] Found macOS Python at: ${testPath}`);
                        break;
                    }
                } catch (error) {
                    writeLog(`[Electron] Error checking Python at ${testPath}: ${error.message}`);
                }
            }
        }
        
        // If still not found, default to the expected path
        if (!pythonPath) {
            pythonPath = path.join(resourcesPath, 'bin', 'python');
            writeLog(`[Electron] No executable Python found, defaulting to: ${pythonPath}`);
        }
    } else {
        pythonPath = path.join(resourcesPath, 'bin', 'python');
    }
    
    writeLog(`[Electron] Looking for Python at: ${pythonPath}`);
    
    // Fallback to system Python if bundled doesn't exist
    if (!fs.existsSync(pythonPath)) {
        writeLog('[Electron] Bundled Python not found, checking alternative paths...');
        
        // Try alternative paths for packaged app
        if (isPackaged) {
            const altPaths = [
                path.join(process.resourcesPath, 'app.asar.unpacked', 'python', process.platform === 'win32' ? 'python.exe' : 'bin/python'),
                path.join(__dirname, '..', 'python', process.platform === 'win32' ? 'python.exe' : 'bin/python'),
                path.join(__dirname, 'resources', 'python', process.platform === 'win32' ? 'python.exe' : 'bin/python')
            ];
            
            for (const altPath of altPaths) {
                writeLog(`[Electron] Trying alternative path: ${altPath}`);
                writeLog(`[Electron] Alternative path exists: ${fs.existsSync(altPath)}`);
                
                // Check parent directory
                const parentDir = path.dirname(altPath);
                if (fs.existsSync(parentDir)) {
                    const contents = fs.readdirSync(parentDir);
                    writeLog(`[Electron] Contents of ${parentDir}: ${JSON.stringify(contents)}`);
                }
                
                if (fs.existsSync(altPath)) {
                    pythonPath = altPath;
                    writeLog(`[Electron] Found Python at alternative path: ${altPath}`);
                    break;
                }
            }
        }
        
        // Final fallback to system Python
        if (!fs.existsSync(pythonPath)) {
            writeLog('[Electron] No bundled Python found, using system Python');
            // Try different Python executable names
            const systemPythonOptions = [
                'python',
                'python3',
                'python.exe',
                'python3.exe',
                'py', // Python Launcher for Windows
                'py.exe'
            ];
            
            // Test each option to see if it works
            for (const pythonCmd of systemPythonOptions) {
                writeLog(`[Electron] Testing system Python command: ${pythonCmd}`);
                try {
                    const testResult = require('child_process').execSync(`${pythonCmd} --version`, { 
                        encoding: 'utf8', 
                        timeout: 5000,
                        stdio: ['pipe', 'pipe', 'pipe']
                    });
                    writeLog(`[Electron] Found working Python: ${pythonCmd} - ${testResult.trim()}`);
                    pythonPath = pythonCmd;
                    break;
                } catch (error) {
                    writeLog(`[Electron] Python command ${pythonCmd} failed: ${error.message}`);
                }
            }
            
            // If still no Python found, set a fallback but it will likely fail
            if (!pythonPath || pythonPath === path.join(resourcesPath, process.platform === 'win32' ? 'python.exe' : 'bin/python')) {
                writeLog('[Electron] WARNING: No working Python installation found!');
                pythonPath = process.platform === 'win32' ? 'python.exe' : 'python';
            }
        }
    } else {
        writeLog('[Electron] Using bundled Python');
    }
    
    // Determine app.py path
    let appScript;
    if (isPackaged) {
        appScript = path.join(process.resourcesPath, 'app.asar.unpacked', 'app.py');
        if (!fs.existsSync(appScript)) {
            appScript = path.join(__dirname, '..', 'app.py');
        }
        if (!fs.existsSync(appScript)) {
            appScript = path.join(__dirname, 'app.py');
        }
    } else {
        appScript = path.join(__dirname, 'app.py');
    }
    
    writeLog(`[Electron] Looking for app.py at: ${appScript}`);
    
    if (!fs.existsSync(appScript)) {
        writeLog(`[Electron] ERROR: app.py not found at: ${appScript}`);
        return false;
    }
    
    // Check if Python dependencies are installed
    const dependenciesInstalled = await checkPythonDependencies(pythonPath);
    if (!dependenciesInstalled && fs.existsSync(pythonPath)) {
        writeLog(`[Electron] Python dependencies missing, attempting auto-install...`);
        const installed = await installPythonDependencies(pythonPath);
        if (!installed) {
            writeLog(`[Electron] Failed to auto-install dependencies`);
            return false;
        }
    }
    
    // Set environment variables for Flask
    const env = {
        ...process.env,
        FLASK_ENV: 'production',
        FLASK_DEBUG: 'false',
        FLASK_RUN_HOST: '127.0.0.1',
        FLASK_RUN_PORT: FLASK_PORT.toString(),
        PORT: FLASK_PORT.toString(),
        SECRET_KEY: require('crypto').randomBytes(32).toString('hex'),
        PYTHONPATH: __dirname,
        PYTHONUNBUFFERED: '1'  // Ensure immediate output
    };
    
    writeLog(`[Electron] Starting Python process...`);
    writeLog(`[Electron] Command: ${pythonPath} ${JSON.stringify([appScript])}`);
    
    // Final verification before spawn
    writeLog(`[Electron] Final Python path verification:`);
    writeLog(`[Electron] - pythonPath: ${pythonPath}`);
    writeLog(`[Electron] - exists: ${fs.existsSync(pythonPath)}`);
    if (fs.existsSync(pythonPath)) {
        try {
            const stats = fs.statSync(pythonPath);
            writeLog(`[Electron] - is file: ${stats.isFile()}`);
            writeLog(`[Electron] - is symlink: ${stats.isSymbolicLink()}`);
            writeLog(`[Electron] - mode: ${stats.mode.toString(8)}`);
            writeLog(`[Electron] - executable: ${!!(stats.mode & parseInt('111', 8))}`);
            
            if (stats.isSymbolicLink()) {
                const realPath = fs.realpathSync(pythonPath);
                writeLog(`[Electron] - symlink target: ${realPath}`);
                writeLog(`[Electron] - target exists: ${fs.existsSync(realPath)}`);
            }
        } catch (error) {
            writeLog(`[Electron] - stat error: ${error.message}`);
        }
    }
    writeLog(`[Electron] - appScript: ${appScript}`);
    writeLog(`[Electron] - appScript exists: ${fs.existsSync(appScript)}`);
    
    try {
        // Resolve symlinks before spawning to avoid ENOTDIR errors
        let resolvedPythonPath = pythonPath;
        try {
            if (fs.existsSync(pythonPath)) {
                // Try to resolve as symlink first
                try {
                    const linkTarget = fs.readlinkSync(pythonPath);
                    if (linkTarget) {
                        // It's a symlink, resolve the full path
                        if (path.isAbsolute(linkTarget)) {
                            resolvedPythonPath = linkTarget;
                        } else {
                            resolvedPythonPath = path.resolve(path.dirname(pythonPath), linkTarget);
                        }
                        writeLog(`[Electron] Resolved symlink from ${pythonPath} to ${resolvedPythonPath}`);
                        writeLog(`[Electron] Resolved path exists: ${fs.existsSync(resolvedPythonPath)}`);
                    }
                } catch (readlinkError) {
                    // Not a symlink or readlink failed, try realpath
                    try {
                        const realPath = fs.realpathSync(pythonPath);
                        if (realPath !== pythonPath) {
                            resolvedPythonPath = realPath;
                            writeLog(`[Electron] Resolved real path from ${pythonPath} to ${resolvedPythonPath}`);
                        }
                    } catch (realpathError) {
                        writeLog(`[Electron] Both readlink and realpath failed, using original path`);
                    }
                }
            }
        } catch (symlinkError) {
            writeLog(`[Electron] Error resolving symlink: ${symlinkError.message}`);
        }
        
        writeLog(`[Electron] Spawn configuration:`);
        writeLog(`[Electron] - resolved Python path: ${resolvedPythonPath}`);
        writeLog(`[Electron] - app script: ${appScript}`);
        writeLog(`[Electron] - working directory: ${path.dirname(appScript)}`);
        writeLog(`[Electron] - working directory exists: ${fs.existsSync(path.dirname(appScript))}`);
        
        flaskProcess = spawn(resolvedPythonPath, [appScript], {
            env,
            cwd: path.dirname(appScript),  // Use the app.py directory as working directory
            stdio: ['pipe', 'pipe', 'pipe'],
            detached: false
        });
        
        writeLog(`[Electron] Flask process spawned with PID: ${flaskProcess.pid}`);
        
        // Enhanced Flask log monitoring with progress tracking
        let lastProgressUpdate = Date.now();
        let currentEstimatedProgress = 30;
        let keyringPhaseStarted = false;
        let keyringItemsLoaded = 0;
        let progressEstimator;
        
        // Start intelligent progress estimation for quiet periods
        progressEstimator = setInterval(() => {
            const timeSinceLastUpdate = Date.now() - lastProgressUpdate;
            
            // If no specific progress for 3+ seconds and we're still below 88%, increment gradually
            if (timeSinceLastUpdate > 3000 && currentEstimatedProgress < 88) {
                currentEstimatedProgress += 1;
                if (keyringPhaseStarted && currentEstimatedProgress < 55) {
                    updateSplashStatus('🔐 Loading security keyring (this may take 15+ seconds)...', currentEstimatedProgress);
                } else if (currentEstimatedProgress < 70) {
                    updateSplashStatus('⚙️ Initializing system components...', currentEstimatedProgress);
                } else {
                    updateSplashStatus('🔄 Preparing application...', currentEstimatedProgress);
                }
                lastProgressUpdate = Date.now();
            }
        }, 2000);
        
        flaskProcess.stdout.on('data', (data) => {
            const logLine = data.toString().trim();
            writeLog(`[Flask] ${logLine}`);
            
            // Parse Flask initialization phases for granular progress tracking
            if (logLine.includes('[ENCRYPTION] ✅ Loaded encryption key from keyring')) {
                currentEstimatedProgress = 40;
                updateSplashStatus('🔐 Security keyring loaded successfully', currentEstimatedProgress);
                lastProgressUpdate = Date.now();
                keyringPhaseStarted = false;
            } else if (logLine.includes('[BOOTSTRAP ENV] ✅ Loaded') && logLine.includes('from keyring')) {
                keyringItemsLoaded++;
                const keyringProgress = Math.min(42 + (keyringItemsLoaded * 2), 54);
                currentEstimatedProgress = keyringProgress;
                updateSplashStatus(`🔑 Loading credentials (${keyringItemsLoaded}/7)...`, currentEstimatedProgress);
                lastProgressUpdate = Date.now();
            } else if (logLine.includes('✅ Loaded 7 environment variables from keyring')) {
                currentEstimatedProgress = 55;
                updateSplashStatus('✅ All credentials loaded successfully', currentEstimatedProgress);
                lastProgressUpdate = Date.now();
            } else if (logLine.includes('[SocketIO] Successfully initialized')) {
                currentEstimatedProgress = 58;
                updateSplashStatus('🔌 Real-time communication initialized', currentEstimatedProgress);
                lastProgressUpdate = Date.now();
            } else if (logLine.includes('[AMRS] Database initialized successfully')) {
                currentEstimatedProgress = 62;
                updateSplashStatus('🗄️ Database connection established', currentEstimatedProgress);
                lastProgressUpdate = Date.now();
            } else if (logLine.includes('[AMRS] ✅ Schema validation completed')) {
                currentEstimatedProgress = 68;
                updateSplashStatus('✅ Database schema validated', currentEstimatedProgress);
                lastProgressUpdate = Date.now();
            } else if (logLine.includes('[AUTO_MIGRATE] Auto-migration complete')) {
                currentEstimatedProgress = 75;
                updateSplashStatus('🔄 Database migration completed', currentEstimatedProgress);
                lastProgressUpdate = Date.now();
            } else if (logLine.includes('[AMRS] Database tables ensured')) {
                currentEstimatedProgress = 78;
                updateSplashStatus('🔧 Database tables configured', currentEstimatedProgress);
                lastProgressUpdate = Date.now();
            } else if (logLine.includes('[SYNC] Enhanced background sync worker started')) {
                currentEstimatedProgress = 82;
                updateSplashStatus('🔄 Synchronization system started', currentEstimatedProgress);
                lastProgressUpdate = Date.now();
            } else if (logLine.includes('🎉 OFFLINE APPLICATION READY!')) {
                currentEstimatedProgress = 85;
                updateSplashStatus('🎉 Application configured successfully', currentEstimatedProgress);
                lastProgressUpdate = Date.now();
            } else if (logLine.includes('Running on http://127.0.0.1:10000')) {
                currentEstimatedProgress = 92;
                updateSplashStatus('🌐 Web server started successfully', currentEstimatedProgress);
                lastProgressUpdate = Date.now();
                // Clear the progress estimator since we're almost done
                if (progressEstimator) {
                    clearInterval(progressEstimator);
                }
                
                // Flask server is ready - schedule update check for after app is fully initialized
                setTimeout(() => {
                    writeLog('[AutoUpdate] Flask server ready, scheduling update check...');
                    checkForUpdatesWhenReady();
                }, 5000); // Wait 5 seconds for full app initialization
            } else if ((logLine.includes('Loading security keyring') || logLine.includes('keyring')) && !keyringPhaseStarted) {
                keyringPhaseStarted = true;
                currentEstimatedProgress = 35;
                updateSplashStatus('🔐 Loading security keyring...', currentEstimatedProgress);
                lastProgressUpdate = Date.now();
            } else if (logLine.includes('[DATETIME PATCH] ✅ SQLAlchemy datetime parsing patch applied')) {
                currentEstimatedProgress = 32;
                updateSplashStatus('🔧 Database compatibility configured', currentEstimatedProgress);
                lastProgressUpdate = Date.now();
            } else if (logLine.includes('[BOOT] Using secure database')) {
                currentEstimatedProgress = 34;
                updateSplashStatus('🔒 Secure database located', currentEstimatedProgress);
                lastProgressUpdate = Date.now();
            }
        });
        
        flaskProcess.stderr.on('data', (data) => {
            const logLine = data.toString().trim();
            writeLog(`[Flask Error] ${logLine}`);
            
            // Also parse stderr for any important progress indicators
            if (logLine.includes('INFO:auto_migrate:') && logLine.includes('Auto-migration complete')) {
                currentEstimatedProgress = 75;
                updateSplashStatus('🔄 Database migration completed', currentEstimatedProgress);
                lastProgressUpdate = Date.now();
            }
        });
        
        flaskProcess.on('error', (error) => {
            writeLog(`[Flask Process Error] ${error.message}`);
            if (progressEstimator) {
                clearInterval(progressEstimator);
            }
        });
        
        flaskProcess.on('exit', (code, signal) => {
            writeLog(`[Flask] Process exited with code ${code}, signal ${signal}`);
            flaskProcess = null;
            if (progressEstimator) {
                clearInterval(progressEstimator);
            }
        });
        
        // Wait for Flask to start
        writeLog('[Electron] Waiting for Flask to start...');
        await waitForFlask(FLASK_PORT);
        updateSplashStatus('Application ready! ✓', 100);
        writeLog('[Electron] Flask backend started successfully');
        return true;
        
    } catch (error) {
        writeLog(`[Electron] Failed to start Flask: ${error.message}`);
        writeLog(`[Electron] Error details: ${JSON.stringify(error)}`);
        return false;
    }
}

// Function to stop Flask server
function stopFlaskServer() {
    if (flaskProcess) {
        console.log('[Electron] Stopping Flask backend...');
        flaskProcess.kill('SIGTERM');
        
        // Force kill after 5 seconds if still running
        setTimeout(() => {
            if (flaskProcess && !flaskProcess.killed) {
                console.log('[Electron] Force killing Flask process...');
                flaskProcess.kill('SIGKILL');
            }
        }, 5000);
        
        flaskProcess = null;
    }
}

// Create the main application window
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 800,
        minHeight: 600,
        show: false, // Don't show until ready
        icon: path.join(__dirname, 'assets', 'icon.png'), // Add your app icon
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            enableRemoteModule: false,
            webSecurity: true
        },
        titleBarStyle: 'default',
        autoHideMenuBar: false
    });
    
    // Load the Flask application
    mainWindow.loadURL(`http://127.0.0.1:${FLASK_PORT}`);
    
    // Show window when ready to prevent visual flash
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
        console.log('[Electron] Main window displayed');
    });
    
    // Handle window closed
    mainWindow.on('closed', () => {
        mainWindow = null;
        stopFlaskServer();
    });
    
    // Handle external links
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        shell.openExternal(url);
        return { action: 'deny' };
    });
    
    // Prevent navigation away from the app
    mainWindow.webContents.on('will-navigate', (event, navigationUrl) => {
        const parsedUrl = new URL(navigationUrl);
        const currentUrl = new URL(mainWindow.webContents.getURL());
        
        if (parsedUrl.origin !== currentUrl.origin) {
            event.preventDefault();
            shell.openExternal(navigationUrl);
        }
    });
    
    // Development: Open DevTools (remove in production)
    if (process.env.NODE_ENV === 'development') {
        mainWindow.webContents.openDevTools();
    }
}

// Create application menu with debugging options
function createMenu() {
    const template = [
        {
            label: 'File',
            submenu: [
                {
                    label: 'Quit',
                    accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
                    click: () => {
                        app.quit();
                    }
                }
            ]
        },
        {
            label: 'Help',
            submenu: [
                {
                    label: 'Show Debug Info',
                    click: async () => {
                        const debugInfo = [
                            `Platform: ${process.platform}`,
                            `Electron Version: ${process.versions.electron}`,
                            `Node Version: ${process.versions.node}`,
                            `Working Directory: ${process.cwd()}`,
                            `App Directory: ${__dirname}`,
                            `Flask Process: ${flaskProcess ? `Running (PID: ${flaskProcess.pid})` : 'Not running'}`,
                            `Flask Port: ${FLASK_PORT}`,
                            `Log File: ${LOG_FILE}`
                        ].join('\n');
                        
                        await dialog.showMessageBox(mainWindow, {
                            type: 'info',
                            title: 'Debug Information',
                            message: 'AMRS Maintenance Tracker Debug Info',
                            detail: debugInfo,
                            buttons: ['OK']
                        });
                    }
                },
                {
                    label: 'Show Application Logs',
                    click: async () => {
                        const recentLogs = logMessages.slice(-50).join('\n'); // Show last 50 messages
                        await dialog.showMessageBox(mainWindow, {
                            type: 'info',
                            title: 'Application Logs',
                            message: 'Recent application logs (last 50 messages)',
                            detail: recentLogs || 'No logs available',
                            buttons: ['OK', 'Open Log File']
                        }).then((result) => {
                            if (result.response === 1) { // Open Log File button
                                shell.showItemInFolder(LOG_FILE);
                            }
                        });
                    }
                },
                {
                    label: 'Open Log File Location',
                    click: () => {
                        shell.showItemInFolder(LOG_FILE);
                    }
                },
                {
                    label: 'Restart Flask Backend',
                    click: async () => {
                        writeLog('[Menu] Restarting Flask backend...');
                        stopFlaskServer();
                        
                        setTimeout(async () => {
                            const started = await startFlaskServer();
                            if (started) {
                                mainWindow.reload();
                            } else {
                                await dialog.showErrorBox('Restart Failed', 'Could not restart the Flask backend. Check Help → Show Application Logs for details.');
                            }
                        }, 2000);
                    }
                },
                {
                    label: 'Open Developer Tools',
                    click: () => {
                        if (mainWindow) {
                            mainWindow.webContents.openDevTools();
                        }
                    }
                }
            ]
        }
    ];
    
    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
}

// --- Add Developer Menu for Manual Update Check ---
function createDeveloperMenu() {
    const template = [
        {
            label: 'Developer',
            submenu: [
                {
                    label: 'Check for Updates',
                    click: () => {
                        writeLog('[DevMenu] Manual update check triggered');
                        if (hasCheckedForUpdates) {
                            // Reset the flag to allow manual checks
                            hasCheckedForUpdates = false;
                            writeLog('[DevMenu] Reset auto-update flag for manual check');
                        }
                        autoUpdater.checkForUpdatesAndNotify();
                    }
                },
                {
                    label: 'Toggle DevTools',
                    click: () => {
                        if (mainWindow) mainWindow.webContents.toggleDevTools();
                    }
                }
            ]
        }
    ];
    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
}

// Configure autoUpdater
writeLog('[AutoUpdate] Configuring autoUpdater...');
autoUpdater.setFeedURL({
    provider: 'generic',
    url: 'https://f005.backblazeb2.com/file/amrs-pm-updates/', // Friendly Backblaze B2 URL
    channel: 'latest'  // Explicitly specify the channel
});

// Set autoUpdater options for better debugging
autoUpdater.autoDownload = true; // Automatically download updates
autoUpdater.autoInstallOnAppQuit = true; // Install on quit

writeLog(`[AutoUpdate] Feed URL set to: https://f005.backblazeb2.com/file/amrs-pm-updates/`);
writeLog(`[AutoUpdate] Channel: latest`);
writeLog(`[AutoUpdate] autoDownload: ${autoUpdater.autoDownload}`);
writeLog(`[AutoUpdate] autoInstallOnAppQuit: ${autoUpdater.autoInstallOnAppQuit}`);

// Enhanced logging and debugging for auto-updater
autoUpdater.logger = {
    info: (msg) => writeLog(`[AutoUpdate] ${msg}`),
    warn: (msg) => writeLog(`[AutoUpdate WARNING] ${msg}`),
    error: (msg) => writeLog(`[AutoUpdate ERROR] ${msg}`),
    debug: (msg) => writeLog(`[AutoUpdate DEBUG] ${msg}`)
};

// App event handlers
app.whenReady().then(async () => {
    writeLog('[Electron] App ready, initializing application...');
    
    // Create developer menu immediately
    createDeveloperMenu();
    
    // Create splash screen first
    createSplashScreen();
    updateSplashStatus('Initializing application...', 5);
    
    // Small delay to show initial message
            setTimeout(() => {
                // Start periodic update checks every 30 minutes
                writeLog('[AutoUpdate] Starting periodic update checks (every 30 minutes)');
                setInterval(() => {
                    writeLog('[AutoUpdate] Periodic update check triggered');
                    checkForUpdatesWhenReady();
                }, 1800000); // 30 minutes in ms
            }, 10000); // Start periodic checks 10s after main window is shown
    writeLog(`[Electron] Current working directory: ${process.cwd()}`);
    writeLog(`[Electron] __dirname: ${__dirname}`);
    writeLog(`[Electron] Platform: ${process.platform}`);
    writeLog(`[Electron] Environment: ${process.env.NODE_ENV || 'production'}`);
    
    const flaskStarted = await startFlaskServer();
    if (flaskStarted) {
        setTimeout(() => {
            closeSplashScreen();
            createWindow();
            
            // Note: Update check is now triggered from Flask server ready event
            writeLog('[Electron] Main window created, update check will happen automatically when Flask confirms ready');
            
        }, 1500); // Slightly longer delay to show "Application ready!" message
    } else {
        writeLog('[Electron] Failed to start Flask backend');
        closeSplashScreen(); // Close splash screen before showing error
        
        // Check for Windows compatibility issues before showing generic error
        const compatError = getWindowsCompatibilityMessage(3221225781);
        if (compatError && process.platform === 'win32') {
            writeLog('[Electron] Windows compatibility issue detected during Flask startup');
            showWindowsCompatibilityError(compatError);
            app.quit();
            return;
        }
        
        // Show error dialog instead of silently quitting
        const { dialog } = require('electron');
        const result = await dialog.showMessageBox({
            type: 'error',
            title: 'AMRS Maintenance Tracker - Startup Error',
            message: 'Failed to start the application backend.',
            detail: 'The Flask server could not be started. This may be due to:\n\n' +
                   '• Missing Python dependencies\n' +
                   '• Port 10000 already in use\n' +
                   '• Antivirus software blocking the application\n' +
                   '• Insufficient permissions\n' +
                   (process.platform === 'win32' ? '• Missing Visual C++ Runtime (Windows)\n' : '') +
                   '\n' +
                   `Detailed logs are available at:\n${LOG_FILE}\n\n` +
                   'You can also check logs via Help → Show Application Logs after startup.',
            buttons: ['View Logs', 'Retry', 'Exit'],
            defaultId: 1
        });
        
        if (result.response === 0) { // View Logs
            shell.showItemInFolder(LOG_FILE);
            setTimeout(() => app.quit(), 1000);
        } else if (result.response === 1) { // Retry
            createSplashScreen(); // Recreate splash for retry
            updateSplashStatus('Retrying startup...', 0);
            writeLog('[Electron] Retrying Flask startup...');
            setTimeout(async () => {
                const retryStarted = await startFlaskServer();
                if (retryStarted) {
                    setTimeout(() => {
                        closeSplashScreen();
                        createWindow();
                    }, 1000);
                } else {
                    closeSplashScreen();
                    app.quit();
                }
            }, 2000);
        } else {
            closeSplashScreen();
            app.quit();
        }
    }
});

app.on('window-all-closed', () => {
    console.log('[Electron] All windows closed');
    stopFlaskServer();
    app.quit();
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

app.on('before-quit', () => {
    console.log('[Electron] App quitting, stopping Flask...');
    stopFlaskServer();
});

// Handle app termination
process.on('SIGINT', () => {
    console.log('[Electron] Received SIGINT, shutting down...');
    stopFlaskServer();
    app.quit();
});

process.on('SIGTERM', () => {
    console.log('[Electron] Received SIGTERM, shutting down...');
    stopFlaskServer();
    app.quit();
});

// IPC for renderer-triggered update check
ipcMain.on('check-for-updates', () => {
    writeLog('[IPC] Renderer requested update check');
    manualUpdateCheck = true;
    hasCheckedForUpdates = false; // Allow manual check even after auto check
    checkForUpdatesWhenReady();
});
