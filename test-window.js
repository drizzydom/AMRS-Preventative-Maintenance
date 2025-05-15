/**
 * Simple Electron window test script
 * Run with: node test-window.js
 */
const { app, BrowserWindow } = require('electron');

console.log('Starting basic Electron window test...');

// Create a window when Electron has initialized
app.whenReady().then(() => {
  console.log('Electron is ready, creating window...');
  
  const window = new BrowserWindow({
    width: 800,
    height: 600,
    show: true, // Show immediately 
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });
  
  // Load a simple HTML page
  window.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(`
    <html>
    <head><title>Window Test</title></head>
    <body>
      <h1>Electron Window Test Successful</h1>
      <p>If you can see this, Electron can create windows correctly.</p>
    </body>
    </html>
  `));
  
  console.log('Window created and content loaded');
  
  window.on('ready-to-show', () => {
    console.log('Window is ready to show');
  });
  
  window.on('closed', () => {
    console.log('Window was closed');
  });
});

// Handle window-all-closed event
app.on('window-all-closed', () => {
  console.log('All windows closed, quitting app');
  app.quit();
});

console.log('Electron startup initiated');
