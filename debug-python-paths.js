const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const { app } = require('electron');

// Function to check if a file exists
function checkFile(filePath) {
  try {
    return fs.existsSync(filePath) ? 'Exists' : 'Missing';
  } catch (err) {
    return `Error checking: ${err.message}`;
  }
}

// Function to run a process and capture output
function runProcess(command, args = []) {
  return new Promise((resolve) => {
    console.log(`Running: ${command} ${args.join(' ')}`);
    
    const proc = spawn(command, args, {
      stdio: 'pipe',
      shell: true
    });
    
    let output = '';
    let error = '';
    
    proc.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    proc.stderr.on('data', (data) => {
      error += data.toString();
    });
    
    proc.on('close', (code) => {
      resolve({
        code,
        output,
        error
      });
    });
  });
}

async function debugPaths() {
  const resourcesPath = process.resourcesPath;
  const pythonPath = path.join(resourcesPath, 'venv', 'Scripts', 'python.exe');
  const flaskScript = path.join(resourcesPath, 'app.py');
  
  console.log('Python Paths Diagnostics');
  console.log('=======================');
  console.log('Resources Path:', resourcesPath);
  console.log('Python Executable:', pythonPath, '-', checkFile(pythonPath));
  console.log('Flask Script:', flaskScript, '-', checkFile(flaskScript));
  
  // List resources directory
  console.log('\nResources Directory Content:');
  try {
    const files = fs.readdirSync(resourcesPath);
    files.forEach(file => {
      console.log(`- ${file}`);
    });
  } catch (err) {
    console.error('Error reading resources directory:', err.message);
  }
  
  // List venv directory if it exists
  const venvPath = path.join(resourcesPath, 'venv');
  if (fs.existsSync(venvPath)) {
    console.log('\nVenv Directory Exists. Content:');
    try {
      const files = fs.readdirSync(venvPath);
      files.forEach(file => {
        console.log(`- ${file}`);
      });
    } catch (err) {
      console.error('Error reading venv directory:', err.message);
    }
  } else {
    console.log('\nVenv directory is missing!');
  }
  
  // Try to run the Python interpreter
  console.log('\nTrying to run Python:');
  if (fs.existsSync(pythonPath)) {
    const pythonResult = await runProcess(pythonPath, ['-V']);
    console.log('Python Version Output:', pythonResult.output);
    console.log('Python Version Error:', pythonResult.error);
    console.log('Exit Code:', pythonResult.code);
    
    // Try to import Flask
    console.log('\nChecking Flask installation:');
    const flaskResult = await runProcess(pythonPath, ['-c', 'import flask; print(flask.__version__)']);
    console.log('Flask Check Output:', flaskResult.output);
    console.log('Flask Check Error:', flaskResult.error);
    console.log('Exit Code:', flaskResult.code);
  } else {
    console.log('Python executable not found, skipping tests');
  }
  
  // Save this output to a log file
  const logContent = `
Python Paths Diagnostics
=======================
Resources Path: ${resourcesPath}
Python Executable: ${pythonPath} - ${checkFile(pythonPath)}
Flask Script: ${flaskScript} - ${checkFile(flaskScript)}
  `;
  
  fs.writeFileSync(path.join(process.cwd(), 'python-paths-debug.log'), logContent);
  console.log('\nLog saved to python-paths-debug.log');
}

// Run the debug function
debugPaths().catch(console.error);
