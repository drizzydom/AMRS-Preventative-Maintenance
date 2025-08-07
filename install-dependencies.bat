@echo off
echo Installing Python dependencies for AMRS Maintenance Tracker...
echo This may take a few minutes...
echo.

set PYTHON_DIR=%~dp0python
set PYTHON_EXE=%PYTHON_DIR%\python.exe
set REQUIREMENTS_FILE=%~dp0requirements.txt

if not exist "%PYTHON_EXE%" (
    echo ERROR: Python executable not found at %PYTHON_EXE%
    pause
    exit /b 1
)

if not exist "%REQUIREMENTS_FILE%" (
    echo ERROR: Requirements file not found at %REQUIREMENTS_FILE%
    pause
    exit /b 1
)

echo Using Python at: %PYTHON_EXE%
echo Installing from: %REQUIREMENTS_FILE%
echo.

"%PYTHON_EXE%" -m pip install --upgrade pip
"%PYTHON_EXE%" -m pip install -r "%REQUIREMENTS_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ Dependencies installed successfully!
    echo You can now run the AMRS Maintenance Tracker application.
) else (
    echo.
    echo ✗ Failed to install dependencies.
    echo Please check your internet connection and try again.
)

echo.
pause
