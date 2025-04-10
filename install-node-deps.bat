@echo off
echo ===================================================
echo Installing Node.js dependencies
echo ===================================================

echo Installing electron-log...
npm install --save electron-log

echo Installing other dependencies...
npm install

echo ===================================================
echo Dependencies installed successfully!
echo ===================================================
echo Run 'npm start' to test the application
echo Run 'npm run dist' to build the installer
echo ===================================================
pause
