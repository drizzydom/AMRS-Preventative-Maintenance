@echo off
echo ===================================================
echo Setting up build environment for Electron packaging
echo ===================================================

REM Install Node.js dependencies including electron-builder
echo Installing npm dependencies...
npm install --save-dev electron electron-builder

REM Run the package-venv script if it exists
if exist package-venv.bat (
    echo Setting up Python virtual environment...
    call package-venv.bat
) else (
    echo Warning: package-venv.bat not found.
    echo Please create the Python virtual environment manually.
)

echo ===================================================
echo Setup complete! Now you can build your application.
echo Run: npm run dist
echo ===================================================
pause
