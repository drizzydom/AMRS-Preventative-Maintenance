const fs = require('fs');
const path = require('path');

// Files to verify exist
const requiredFiles = [
  'app.py',
  'app-launcher.py',
  'static',
  'templates',
  'modules'
];

// Check if we're in development or production mode
const isPackaged = !process.env.ELECTRON_IS_DEV;
const basePath = isPackaged ? process.resourcesPath : __dirname;

console.log('Running file verification script');
console.log(`Base path: ${basePath}`);
console.log(`App is packaged: ${isPackaged}`);

// Verify files exist
let missingFiles = [];
for (const file of requiredFiles) {
  const filePath = path.join(basePath, file);
  console.log(`Checking ${filePath}`);
  
  if (fs.existsSync(filePath)) {
    console.log(`✅ Found: ${file}`);
  } else {
    console.log(`❌ Missing: ${file}`);
    missingFiles.push(file);
  }
}

// List contents of base directory
console.log('\nDirectory contents:');
try {
  const files = fs.readdirSync(basePath);
  files.forEach(file => {
    console.log(`- ${file}`);
  });
} catch (err) {
  console.error('Error reading directory:', err);
}

// Save verification results
const results = {
  timestamp: new Date().toISOString(),
  basePath,
  isPackaged,
  missingFiles,
  allRequired: missingFiles.length === 0
};

fs.writeFileSync(
  path.join(isPackaged ? process.cwd() : __dirname, 'file-verification.json'),
  JSON.stringify(results, null, 2)
);

console.log(`\nVerification complete. Missing files: ${missingFiles.length}`);
