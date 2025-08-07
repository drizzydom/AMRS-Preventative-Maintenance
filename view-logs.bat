@echo off
echo.
echo AMRS Maintenance Tracker - Log Viewer
echo =====================================
echo.

set LOG_FILE=%TEMP%\amrs-maintenance-tracker.log

if exist "%LOG_FILE%" (
    echo Opening log file: %LOG_FILE%
    echo.
    start notepad.exe "%LOG_FILE%"
) else (
    echo Log file not found at: %LOG_FILE%
    echo.
    echo The application may not have been started yet, or logs may be in a different location.
    echo Try running the application first, then check this location again.
    echo.
)

echo.
echo Press any key to exit...
pause >nul
