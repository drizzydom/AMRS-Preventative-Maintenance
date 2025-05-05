@echo off
REM Copy backend files and folders into electron_app

REM Create electron_app if it doesn't exist
if not exist "electron_app" (
    mkdir "electron_app"
)

REM List of files to copy
set FILES=app.py models.py config.py auto_migrate.py requirements.txt requirements-windows.txt wsgi.py cache_config.py db_config.py simple_healthcheck.py excel_importer.py notification_scheduler.py api_endpoints.py expand_user_fields.py

REM Copy each file if it exists
for %%F in (%FILES%) do (
    if exist "%%F" (
        copy /Y "%%F" "electron_app\"
    )
)

REM List of folders to copy
set FOLDERS=static templates modules instance venv_py39_electron

REM Copy each folder if it exists
for %%D in (%FOLDERS%) do (
    if exist "%%D" (
        xcopy /E /I /Y "%%D" "electron_app\%%D"
    )
)

echo All necessary files and folders have been copied to electron_app.
pause
