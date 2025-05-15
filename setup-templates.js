/**
 * This script helps set up your templates directory structure
 * Run with: node setup-templates.js
 */
const fs = require('fs');
const path = require('path');

const ROOT_DIR = __dirname;
const SOURCE_TEMPLATES = path.join(ROOT_DIR, 'templates'); // Adjust this path to your actual templates folder
const TARGET_DIR = path.join(ROOT_DIR, 'electron_app', 'templates');

// Ensure target directories exist
function createDirs() {
  const dirs = [
    TARGET_DIR,
    path.join(TARGET_DIR, 'css'),
    path.join(TARGET_DIR, 'js'),
    path.join(TARGET_DIR, 'images'),
    path.join(TARGET_DIR, 'fonts')
  ];
  
  dirs.forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
      console.log(`Created directory: ${dir}`);
    }
  });
}

// Check if source templates directory exists
function checkSourceDir() {
  if (!fs.existsSync(SOURCE_TEMPLATES)) {
    console.error(`Source templates directory not found: ${SOURCE_TEMPLATES}`);
    console.log('Please create this directory with your template files or adjust the path in this script.');
    return false;
  }
  
  return true;
}

// Main function
function setup() {
  console.log('Setting up templates directory structure...');
  
  if (!checkSourceDir()) {
    return;
  }
  
  createDirs();
  console.log('Template directory structure created.');
  console.log('');
  console.log('Next steps:');
  console.log('1. Make sure your HTML templates are in the templates directory');
  console.log('   - login.html, dashboard.html, etc.');
  console.log('2. Make sure your static assets are in:');
  console.log('   - templates/static/css');
  console.log('   - templates/static/js');
  console.log('   - templates/static/images');
  console.log('   - templates/static/fonts');
  console.log('3. Run "npm run bundle-templates" to process and bundle the templates');
  console.log('');
}

// Run the setup
setup();
