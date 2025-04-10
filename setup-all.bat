@echo off
echo ===================================================
echo Complete Setup for AMRS Maintenance Tracker
echo ===================================================

echo Step 1: Clean node_modules (if exists)
if exist node_modules (
  echo Removing old node_modules...
  rmdir /s /q node_modules
)

echo Step 2: Installing Node.js dependencies...
call npm install
call npm install --save electron-log electron-updater

echo Step 3: Setting up Python environment...
if exist package-venv.bat (
  echo Running Python environment setup...
  call package-venv.bat
) else (
  echo WARNING: package-venv.bat not found, skipping Python setup
)

echo Step 4: Creating required directories...
if not exist electron_app\icons mkdir electron_app\icons
if not exist modules mkdir modules
echo # Python package > modules\__init__.py

echo Step 5: Checking for application icon...
if not exist electron_app\icons\app.png (
  echo Downloading placeholder icon...
  powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/electron/electron/main/default_app/icon.png' -OutFile 'electron_app\icons\app.png'"
)

echo ===================================================
echo Setup complete!
echo ===================================================
echo You can now:
echo  - Run 'npm start' to test the application
echo  - Run 'npm run dist' to build the installer
echo ===================================================
pause
