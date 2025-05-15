/**
 * AMRS Preventative Maintenance Desktop App Builder
 * 
 * This script builds the Electron application by:
 * 1. Setting up Python environment
 * 2. Installing Python dependencies
 * 3. Preparing resources
 * 4. Building the Electron app
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

// Configuration
const config = {
    pythonVersion: '3.9',
    venvName: 'venv',
    electronDir: 'electron_app',
    pythonFiles: [
        'app.py',
        'app-launcher.py',
        'models.py',
        'auto_migrate.py',
        'electron_config.py',
        'electron_db_setup.py',
        'electron_db_sync.py',
        'electron_api.py',
        'electron_sqlite_setup.py',
        'offline_adapter.py',
        'python_env_debug.py',
        'install_dependencies.py',
        'simple_flask_launcher.py',
        'config_checker.py',
        'requirements.txt'
    ],
    resourceDirs: [
        'static',
        'templates'
    ]
};

// Utility functions
function log(message) {
    console.log(`[BUILD] ${message}`);
}

function execCommand(command, options = {}) {
    log(`Running: ${command}`);
    try {
        execSync(command, {
            stdio: 'inherit',
            ...options
        });
        return true;
    } catch (error) {
        log(`Command failed: ${command}`);
        log(error.message);
        return false;
    }
}

function createDirectoryIfNotExists(dir) {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
        log(`Created directory: ${dir}`);
    }
}

function copyFile(src, dest) {
    try {
        fs.copyFileSync(src, dest);
        log(`Copied ${src} to ${dest}`);
        return true;
    } catch (error) {
        log(`Failed to copy ${src} to ${dest}: ${error.message}`);
        return false;
    }
}

function copyDirectory(src, dest) {
    createDirectoryIfNotExists(dest);
    
    const entries = fs.readdirSync(src, { withFileTypes: true });
    
    for (const entry of entries) {
        const srcPath = path.join(src, entry.name);
        const destPath = path.join(dest, entry.name);
        
        if (entry.isDirectory()) {
            if (entry.name !== '__pycache__' && entry.name !== 'node_modules') {
                copyDirectory(srcPath, destPath);
            }
        } else {
            if (!entry.name.endsWith('.pyc')) {
                copyFile(srcPath, destPath);
            }
        }
    }
}

// Build steps
function setupPythonEnvironment() {
    log('Setting up Python environment...');
    
    // Check Python version
    try {
        const pythonVersionOutput = execSync('python --version').toString();
        log(`Found Python: ${pythonVersionOutput.trim()}`);
    } catch (error) {
        log('Python not found or not in PATH. Please make sure Python is installed.');
        process.exit(1);
    }
    
    // Create virtual environment if it doesn't exist
    if (!fs.existsSync(config.venvName)) {
        log(`Creating virtual environment: ${config.venvName}`);
        if (!execCommand(`python -m venv ${config.venvName}`)) {
            log('Failed to create virtual environment. Exiting...');
            process.exit(1);
        }
    } else {
        log(`Using existing virtual environment: ${config.venvName}`);
    }
    
    // Install requirements in the virtual environment
    const pipCommand = os.platform() === 'win32' 
        ? `${config.venvName}\\Scripts\\pip` 
        : `${config.venvName}/bin/pip`;
    
    log('Installing Python dependencies...');
    // Update pip first
    execCommand(`"${pipCommand}" install --upgrade pip`);
    // Now install requirements
    if (!execCommand(`"${pipCommand}" install -r requirements.txt`)) {
        log('Failed to install Python dependencies. Exiting...');
        process.exit(1);
    }
    
    log('Python environment setup complete.');
}

function prepareResourceFiles() {
    log('Preparing resource files...');
    
    // Create a resources directory where all Python files will be copied
    const resourcesDir = path.join('resources');
    createDirectoryIfNotExists(resourcesDir);
    
    // Copy Python files
    for (const file of config.pythonFiles) {
        if (fs.existsSync(file)) {
            copyFile(file, path.join(resourcesDir, file));
        } else {
            log(`Warning: File ${file} not found.`);
        }
    }
    
    // Copy resource directories
    for (const dir of config.resourceDirs) {
        if (fs.existsSync(dir)) {
            copyDirectory(dir, path.join(resourcesDir, dir));
        } else {
            log(`Warning: Directory ${dir} not found.`);
        }
    }
    
    // Copy modules folder if it exists
    if (fs.existsSync('modules')) {
        copyDirectory('modules', path.join(resourcesDir, 'modules'));
    }
    
    // Create a site-packages directory in resources and copy packages directly
    const sitePackagesDir = path.join(resourcesDir, 'site-packages');
    createDirectoryIfNotExists(sitePackagesDir);
    
    // Copy key packages from the venv site-packages to our site-packages
    const venvSitePackages = os.platform() === 'win32' 
        ? path.join(config.venvName, 'Lib', 'site-packages')
        : path.join(config.venvName, 'lib', 'python3.9', 'site-packages');
    
    if (fs.existsSync(venvSitePackages)) {
        log('Copying key packages from virtual environment...');
        
        // List of packages to copy directly
        const packagesToInclude = [
            'flask', 
            'werkzeug',
            'jinja2',
            'sqlalchemy',
            'pandas',
            'numpy',
            'markupsafe',
            'click',
            'itsdangerous',
            'flask_login',
            'flask_sqlalchemy',
            'flask_mail',
            'dotenv',
            'cryptography'
        ];
        
        const entries = fs.readdirSync(venvSitePackages, { withFileTypes: true });
        
        for (const entry of entries) {
            const entryName = entry.name.toLowerCase();
            const shouldInclude = packagesToInclude.some(pkg => 
                entryName === pkg || 
                entryName.startsWith(pkg + '-') || 
                entryName.startsWith(pkg + '_')
            );
            
            if (shouldInclude) {
                const srcPath = path.join(venvSitePackages, entry.name);
                const destPath = path.join(sitePackagesDir, entry.name);
                
                if (entry.isDirectory()) {
                    log(`Copying package: ${entry.name}`);
                    copyDirectory(srcPath, destPath);
                } else if (entry.name.endsWith('.py') || entry.name.endsWith('.pyd') || entry.name.endsWith('.dll')) {
                    log(`Copying module: ${entry.name}`);
                    copyFile(srcPath, destPath);
                }
            }
        }
    } else {
        log('Warning: Virtual environment site-packages not found.');
    }
    
    // Copy the virtual environment
    if (fs.existsSync(config.venvName)) {
        log('Copying Python virtual environment (this may take a while)...');
        
        // Create venv directory in resources
        const resourceVenvDir = path.join(resourcesDir, config.venvName);
        createDirectoryIfNotExists(resourceVenvDir);
        
        // Copy the Scripts/bin directory
        const scriptsDir = os.platform() === 'win32' ? 'Scripts' : 'bin';
        if (fs.existsSync(path.join(config.venvName, scriptsDir))) {
            copyDirectory(
                path.join(config.venvName, scriptsDir), 
                path.join(resourceVenvDir, scriptsDir)
            );
        }
        
        // Copy the Lib directory (for Windows) or lib directory (for Unix)
        const libDir = os.platform() === 'win32' ? 'Lib' : 'lib';
        if (fs.existsSync(path.join(config.venvName, libDir))) {
            copyDirectory(
                path.join(config.venvName, libDir),
                path.join(resourceVenvDir, libDir)
            );
        }
        
        // Copy pyvenv.cfg
        if (fs.existsSync(path.join(config.venvName, 'pyvenv.cfg'))) {
            copyFile(
                path.join(config.venvName, 'pyvenv.cfg'),
                path.join(resourceVenvDir, 'pyvenv.cfg')
            );
        }
        
        log('Virtual environment copied successfully.');
    } else {
        log('Warning: Virtual environment not found.');
    }
    
    log('Resource files prepared.');
}

function updatePackageJson() {
    log('Updating package.json for build...');
    
    const packageJsonPath = path.join(process.cwd(), 'package.json');
    if (!fs.existsSync(packageJsonPath)) {
        log('package.json not found. Make sure you are in the project root directory.');
        return false;
    }
    
    try {
        const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
        
        // Ensure extraResources includes all our Python files and directories
        packageJson.build = packageJson.build || {};
        packageJson.build.extraResources = packageJson.build.extraResources || [];
        
        // Clear existing extraResources and add our new ones
        packageJson.build.extraResources = [
            {
                "from": "resources",
                "to": ".",
                "filter": [
                    "**/*",
                    "!**/__pycache__/**",
                    "!**/*.pyc"
                ]
            }
        ];
        
        // Write back to package.json
        fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
        log('package.json updated successfully.');
        return true;
    } catch (error) {
        log(`Failed to update package.json: ${error.message}`);
        return false;
    }
}

function buildElectronApp() {
    log('Building Electron app...');
    
    // Install electron-builder if not already installed
    if (!execCommand('npm list electron-builder --depth=0')) {
        log('Installing electron-builder...');
        execCommand('npm install --save-dev electron-builder');
    }
    
    // Build the app
    if (!execCommand('npm run dist')) {
        log('Failed to build Electron app. Check the errors above.');
        process.exit(1);
    }
    
    log('Electron app built successfully!');
}

function cleanup() {
    log('Cleaning up...');
    
    // Remove temporary resources directory
    if (fs.existsSync('resources')) {
        try {
            fs.rmSync('resources', { recursive: true, force: true });
            log('Removed resources directory.');
        } catch (error) {
            log(`Failed to remove resources directory: ${error.message}`);
        }
    }
    
    log('Cleanup complete.');
}

// Main function
function main() {
    log('Starting build process...');
    
    // Check that we're in the correct directory
    if (!fs.existsSync('app.py') || !fs.existsSync('package.json')) {
        log('Error: Not in the project root directory. Please run this script from the project root.');
        process.exit(1);
    }
    
    try {
        setupPythonEnvironment();
        prepareResourceFiles();
        updatePackageJson();
        buildElectronApp();
        cleanup();
        
        log('Build process completed successfully!');
        log('Your application can be found in the dist/ directory.');
    } catch (error) {
        log(`Build failed: ${error.message}`);
        process.exit(1);
    }
}

// Run the main function
main();