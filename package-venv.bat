@echo off
REM This script packages the Python virtual environment for distribution

echo ===================================================
echo Creating Python virtual environment for distribution
echo ===================================================

REM Create a slimmed-down version of the virtual environment
echo Installing virtualenv...
python -m pip install virtualenv

echo Creating distribution virtual environment...
python -m virtualenv --copies dist-venv

REM Activate the new virtual environment
echo Activating virtual environment...
call dist-venv\Scripts\activate.bat

REM Install required packages
echo Installing required packages...
pip install flask
pip install pandas
pip install openpyxl
pip install werkzeug==2.3.7
pip install jinja2==3.1.2
pip install itsdangerous==2.1.2
pip install click==8.1.7
pip install colorama==0.4.6
REM Add other required packages below as needed:
REM pip install package-name

REM Save the package list
pip freeze > requirements.txt
echo Package list saved to requirements.txt

REM Deactivate virtual environment
echo Deactivating virtual environment...
deactivate

REM Create icons directory if it doesn't exist
if not exist electron_app\icons mkdir electron_app\icons
echo Icons directory checked/created at electron_app\icons

REM Ensure we have an application icon
if not exist electron_app\icons\app.png (
    echo Creating a placeholder application icon...
    powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/electron/electron/main/default_app/icon.png' -OutFile 'electron_app\icons\app.png'"
    echo Icon downloaded to electron_app\icons\app.png
)

REM Create modules directory if it doesn't exist
if not exist modules mkdir modules
echo Modules directory checked/created at modules

REM Create an empty __init__.py in modules to make it a valid Python package
echo # Python package > modules\__init__.py
echo Created __init__.py in modules directory

REM Copy to the venv directory for building
echo Copying to build directory...
if exist venv rmdir /s /q venv
xcopy /E /I /Y dist-venv venv

echo ===================================================
echo Virtual environment prepared for packaging!
echo Next steps:
echo 1. Run: npm run dist
echo 2. Find your executable in the dist folder
echo ===================================================
pause
