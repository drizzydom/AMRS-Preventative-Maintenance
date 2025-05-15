/**
 * Electron Debug Launcher
 * This is a standalone diagnostic tool to debug Electron startup issues,
 * particularly when the app appears in Task Manager but no window shows.
 */
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

console.log('Starting Electron with debugging...');

// Find the electron executable
const electronPath = require('electron');
const appPath = path.join(__dirname);

console.log(`Electron path: ${electronPath}`);
console.log(`App path: ${appPath}`);

// Set environment variables for better debugging
const env = {
  ...process.env,
  ELECTRON_ENABLE_LOGGING: '1',
  ELECTRON_ENABLE_STACK_DUMPING: '1',
  ELECTRON_DEBUG: '1',
  FORCE_SHOW_WINDOW: '1', // Custom flag for our app
  NODE_ENV: 'development'
};

// Launch electron with full stdout/stderr capture
console.log('Launching electron...');
const electron = spawn(electronPath, [appPath], { env });

electron.stdout.on('data', (data) => {
  console.log(`ELECTRON: ${data.toString().trim()}`);
});

electron.stderr.on('data', (data) => {
  console.error(`ELECTRON ERROR: ${data.toString().trim()}`);
});

electron.on('close', (code) => {
  console.log(`Electron process exited with code ${code}`);
});

electron.on('error', (err) => {
  console.error(`Failed to start electron: ${err.message}`);
});

// Monitor for window creation - if electron is running but no window appears
setTimeout(() => {
  console.log('Checking if Electron process is still running...');
  if (!electron.killed) {
    console.log('Electron is still running but may not have opened a window.');
    console.log('You may need to check Task Manager and end the process manually.');
  }
}, 20000); // Check after 20 seconds
