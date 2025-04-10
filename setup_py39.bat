@echo off
echo Setting up Python 3.9 environment for AMRS Maintenance Tracker
echo.

REM Check if Python 3.9 is installed
if exist "C:\Program Files\Python39\python.exe" (
    echo Found Python 3.9
) else (
    echo Python 3.9 not found. Please download and install it from:
    echo https://www.python.org/downloads/release/python-3913/
    echo Make sure to check 'Add Python to PATH' during installation
    echo After installation, run this script again.
    pause
    exit /b
)

echo Creating Python 3.9 virtual environment...
"C:\Program Files\Python39\python.exe" -m venv venv_py39

echo Installing required packages...
call venv_py39\Scripts\activate.bat
pip install cefpython3==66.1 flask==2.2.5 flask_sqlalchemy==3.0.5 flask_login==0.6.2 pyinstaller==6.0.0

echo.
echo Environment setup complete!
echo.
echo To activate this environment in the future, run:
echo venv_py39\Scripts\activate.bat
echo.
echo To build the application, run:
echo python build_cef_app.py
echo.

pause
