@echo off
REM ========================================
REM Build AMRS Maintenance Tracker Windows App
REM ========================================

echo Building AMRS Maintenance Tracker Windows Application
echo.

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Ensure PyInstaller is installed
python -m pip install -q --upgrade pip
python -m pip install -q --upgrade pyinstaller pywebview requests

REM Install required packages
echo Installing required packages...
python -m pip install -q -r requirements-windows.txt

REM Build the application
echo Building Windows Application...
python build_windows_app.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo Look in the dist folder for the executable.
echo.
pause