@echo off
echo ===================================================
echo Installing Electron Builder
echo ===================================================

REM Install electron-builder as a dev dependency
echo Installing electron-builder...
npm install --save-dev electron-builder

echo ===================================================
echo Installation complete!
echo Now you can run: npm run dist
echo ===================================================
pause
