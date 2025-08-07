# AMRS Maintenance Tracker - Windows Installation

## One-Click Installation

This installer includes everything needed to run the AMRS Maintenance Tracker:

- **AMRS-Maintenance-Tracker-Win10-Setup-1.0.0.exe** (130MB)  
  - For Windows 10, 11, and Server 2016+
  - Uses Electron 28.3.3 with modern features

## What's Included

✅ **Complete Python Environment** - No need to install Python separately
✅ **All Python Dependencies** - Flask, SQLAlchemy, and all required packages
✅ **Application Files** - Complete AMRS Maintenance Tracker application
✅ **Automatic Setup** - Dependencies are installed automatically on first run
✅ **Logging & Debugging** - Built-in log viewing and troubleshooting tools

## Installation Process

1. **Download** the appropriate installer for your Windows version
2. **Run the installer** as Administrator (recommended)
3. **Launch the application** from the Start Menu or Desktop shortcut
4. **First run** will automatically install Python dependencies (may take 2-3 minutes)
5. **Application ready** - Access via http://localhost:10000 or the app window

## Troubleshooting

If you encounter any issues:

1. **View Logs**: Help → Show Application Logs
2. **Check Debug Info**: Help → Show Debug Info  
3. **Manual Dependencies**: Run `install-dependencies.bat` in the installation folder
4. **Log File Location**: `%TEMP%\amrs-maintenance-tracker.log`

## System Requirements

- **Windows 10** or later
- **2GB RAM** minimum, 4GB recommended
- **500MB disk space** for installation
- **Internet connection** for first-time dependency installation

## Support

For technical support or issues, check the application logs first, then contact your system administrator.
