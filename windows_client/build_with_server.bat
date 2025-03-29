@echo off
echo AMRS Maintenance Tracker Builder
echo ===============================
echo:

if "%~1"=="" (
    echo Please specify a server URL:
    echo Example: build_with_server.bat http://yourserver.com:9000
    exit /b 1
)

echo Building application with server URL: %1
python build.py --server-url %1

echo:
echo Build complete!
pause
