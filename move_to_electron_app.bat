@echo off
REM Move backend files and folders into electron_app

REM Create electron_app if it doesn't exist
if not exist "electron_app" (
    mkdir "electron_app"
)

REM List of files to move
set FILES=app.py app-launcher.py flask-launcher.py models.py config.py auto_migrate.py requirements.txt requirements-windows.txt requirements-render.txt wsgi.py cache_config.py db_config.py simple_healthcheck.py excel_importer.py notification_scheduler.py api_endpoints.py expand_user_fields.py

REM Move each file if it exists
for %%F in (%FILES%) do (
    if exist "%%F" (
        move /Y "%%F" "electron_app\"
    )
)

REM List of folders to move
set FOLDERS=static templates modules instance venv_py39_electron

REM Move each folder if it exists
for %%D in (%FOLDERS%) do (
    if exist "%%D" (
        move /Y "%%D" "electron_app\"
    )
)

echo All necessary files and folders have been moved to electron_app.
pause
