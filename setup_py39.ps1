
# PowerShell script to help set up Python 3.9 environment
Write-Host "Setting up Python 3.9 environment for AMRS Maintenance Tracker" -ForegroundColor Cyan

# Check if Python 3.9 is installed
$py39Path = "C:\Program Files\Python39\python.exe"
$py39Installed = Test-Path $py39Path

if (-not $py39Installed) {
    Write-Host "Python 3.9 not found. Please download and install it from:" -ForegroundColor Yellow
    Write-Host "https://www.python.org/downloads/release/python-3913/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    Write-Host "After installation, run this script again." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

# Create virtual environment
Write-Host "Creating Python 3.9 virtual environment..." -ForegroundColor Cyan
& $py39Path -m venv venv_py39

# Activate virtual environment and install packages
Write-Host "Installing required packages..." -ForegroundColor Cyan
& .\venv_py39\Scripts\Activate.ps1
pip install cefpython3==66.1 flask==2.2.5 flask_sqlalchemy==3.0.5 flask_login==0.6.2 pyinstaller==6.0.0

Write-Host "`nEnvironment setup complete!" -ForegroundColor Green
Write-Host "`nTo activate this environment in the future, run:" -ForegroundColor Cyan
Write-Host ".\venv_py39\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "`nTo build the application, run:" -ForegroundColor Cyan
Write-Host "python build_cef_app.py" -ForegroundColor White

Read-Host "`nPress Enter to exit"
