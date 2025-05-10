const builder = require('electron-builder');
const path = require('path');
const fs = require('fs');

// Get package.json version
const packageJson = require('./electron_app/package.json');

// Configuration for electron-builder
builder.build({
  config: {
    appId: 'com.amrs.maintenance-tracker',
    productName: 'AMRS Maintenance Tracker',
    copyright: 'Copyright © 2025 AMRS',
    
    // Windows specific configuration
    win: {
      target: [
        {
          target: 'nsis',
          arch: ['x64']
        },
        {
          target: 'portable',
          arch: ['x64']
        }
      ],
      icon: path.join(__dirname, 'electron_app', 'icons', 'app.ico'),
      publisherName: 'AMRS',
    },
    
    // NSIS installer options
    nsis: {
      oneClick: false,
      allowToChangeInstallationDirectory: true,
      createDesktopShortcut: true,
      createStartMenuShortcut: true,
      shortcutName: 'AMRS Maintenance Tracker',
      uninstallDisplayName: 'AMRS Maintenance Tracker',
      artifactName: 'AMRS-Maintenance-Tracker-Setup-${version}.${ext}'
    },
    
    // Portable configuration
    portable: {
      artifactName: 'AMRS-Maintenance-Tracker-Portable-${version}.${ext}'
    },
    
    // Application files
    files: [
      'electron_app/**/*',
      'static/**/*',
      'templates/**/*',
      'app-launcher.py',
      'offline_adapter.py',
      'hybrid_dao.py',
      'sync_api.py',
      '!**/*.pyc',
      '!**/__pycache__/**',
      '!**/node_modules/**',
      '!build/**',
      '!dist/**'
    ],
    
    // Python environment
    extraResources: [
      {
        from: 'venv_py39',
        to: 'venv',
        filter: ['**/*', '!**/*.pyc', '!**/__pycache__/**']
      }
    ],
    
    // Build configuration
    directories: {
      output: 'dist/electron',
      app: './'
    },
    
    // Auto-update configuration for future releases
    publish: null, // Set to null to disable auto-updates for now
  }
})
.then((result) => {
  console.log('Build completed!');
  console.log(result);
})
.catch((error) => {
  console.error('Build failed:', error);
  process.exit(1);
});
