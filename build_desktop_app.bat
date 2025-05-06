@echo off
REM === AMRS Preventative Maintenance Desktop Build Script ===

cd /d "%~dp0"

REM Step 0: Clean up previous build artifacts and node_modules
if exist electron_app\dist rmdir /S /Q electron_app\dist
if exist electron_app\node_modules rmdir /S /Q electron_app\node_modules
if exist electron_app\static rmdir /S /Q electron_app\static
if exist electron_app\templates rmdir /S /Q electron_app\templates
if exist electron_app\app.py del /Q electron_app\app.py
if exist electron_app\requirements.txt del /Q electron_app\requirements.txt
if exist electron_app\models.py del /Q electron_app\models.py
if exist electron_app\db_config.py del /Q electron_app\db_config.py
if exist electron_app\auto_migrate.py del /Q electron_app\auto_migrate.py
if exist electron_app\expand_user_fields.py del /Q electron_app\expand_user_fields.py
if exist electron_app\cache_config.py del /Q electron_app\cache_config.py
if exist electron_app\fix_audit_history_v2.py del /Q electron_app\fix_audit_history_v2.py
if exist electron_app\fix_audit_history.py del /Q electron_app\fix_audit_history.py
if exist electron_app\simple_healthcheck.py del /Q electron_app\simple_healthcheck.py
if exist electron_app\app_bootstrap.py del /Q electron_app\app_bootstrap.py
if exist electron_app\modules rmdir /S /Q electron_app\modules
if exist electron_app\app rmdir /S /Q electron_app\app

REM Step 1: Check for Node.js and npm
where npm >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Node.js/npm not found. Please install Node.js and try again.
    pause
    exit /b 1
)

REM Step 2: Check for Python and venv
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python and try again.
    pause
    exit /b 1
)

REM Step 3: Activate Python venv and install requirements
if exist venv_py310\Scripts\activate.bat (
    call venv_py310\Scripts\activate.bat
    goto :venv_activated
)
if exist venv_py39\Scripts\activate.bat (
    call venv_py39\Scripts\activate.bat
    goto :venv_activated
)
echo [ERROR] No Python virtual environment found (venv_py310 or venv_py39).
pause
exit /b 1

:venv_activated
echo [INFO] Installing Python dependencies...
pip install -r requirements.txt

REM Step 4: Prepare electron_app with backend files (no need for static/templates)
if not exist electron_app (
    mkdir electron_app
)

REM Copy backend files (keep originals in root)
copy /Y app.py electron_app\app.py
copy /Y requirements.txt electron_app\requirements.txt
copy /Y models.py electron_app\models.py
copy /Y db_config.py electron_app\db_config.py
copy /Y auto_migrate.py electron_app\auto_migrate.py
copy /Y expand_user_fields.py electron_app\expand_user_fields.py
copy /Y cache_config.py electron_app\cache_config.py
copy /Y fix_audit_history_v2.py electron_app\fix_audit_history_v2.py
copy /Y fix_audit_history.py electron_app\fix_audit_history.py
copy /Y simple_healthcheck.py electron_app\simple_healthcheck.py
copy /Y app_bootstrap.py electron_app\app_bootstrap.py
xcopy /E /I /Y modules electron_app\modules
xcopy /E /I /Y app electron_app\app

REM Step 5: Install Node dependencies for Electron
cd electron_app
if not exist node_modules (
    echo [INFO] Installing Node dependencies...
    npm install
) else (
    echo [INFO] Node dependencies already installed.
)
cd ..

REM Step 6: Build the Electron app
cd electron_app
echo [INFO] Building Electron app...
npm run dist
cd ..

REM Step 7: Done
echo [SUCCESS] Build complete! The installer is in electron_app\dist\
pause