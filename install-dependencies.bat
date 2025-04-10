@echo off
echo ===================================================
echo Installing required Node.js dependencies
echo ===================================================

echo Installing electron-updater...
npm install --save electron-updater

echo Installing other dependencies...
npm install

echo ===================================================
echo Dependencies installed successfully
echo ===================================================
pause
