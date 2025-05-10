@echo off
echo Building AMRS Maintenance Tracker Desktop Application

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: Node.js is not installed. Please install Node.js and try again.
    exit /b 1
)

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed. Please install Python and try again.
    exit /b 1
)

REM Check if the virtual environment exists
if not exist venv_py39\Scripts\python.exe (
    echo Error: Python virtual environment not found. Please run setup_env.py first.
    exit /b 1
)

REM Install Node.js dependencies if needed
echo Installing Node.js dependencies...
cd electron_app
call npm install
cd ..

REM Create app icons if needed
if not exist electron_app\icons\app.ico (
    echo Creating application icons...
    node create-app-icon.js
)

REM Build the application
echo Building application with electron-builder...
call node build_electron_app.js

if %ERRORLEVEL% neq 0 (
    echo Error: Build failed.
    exit /b 1
)

echo Build completed! The installer and portable versions can be found in the dist\electron folder.
echo.
echo NSIS Installer: dist\electron\AMRS-Maintenance-Tracker-Setup-*.exe
echo Portable: dist\electron\AMRS-Maintenance-Tracker-Portable-*.exe
echo.
pause
