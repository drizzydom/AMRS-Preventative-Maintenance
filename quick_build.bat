@echo off
echo ====================================================
echo   AMRS Maintenance Tracker - Quick Build Script
echo ====================================================
echo.
echo This script will build the desktop application with default settings.
echo.
echo Press CTRL+C to cancel or any key to continue...
pause > nul

echo.
echo Installing required dependencies...
python -m pip install cefpython3==66.1 flask==2.2.5 flask_sqlalchemy==3.0.5 flask_login==0.6.2 pyinstaller==6.0.0

echo.
echo Building application...
python build_desktop_app.py --portable

echo.
if %ERRORLEVEL% EQU 0 (
    echo Build completed successfully!
    echo.
    echo The application is located in the dist\AMRSMaintenanceTracker directory
) else (
    echo Build failed. Check the output above for errors.
)

echo.
echo Press any key to exit...
pause > nul
