# AMRS Maintenance Tracker - Windows Application

This standalone Windows application connects to the AMRS Preventative Maintenance system running on Render.

## Features

- **Completely Standalone**: All dependencies are bundled in the executable
- **No Browser Required**: Opens in its own application window
- **Offline Support**: Works when you're not connected to the internet by using cached content
- **Auto-Reconnect**: Automatically reconnects when internet is restored
- **Embedded Browser**: Full web application functionality in a native window

## Installation

1. Download the latest `AMRSMaintenanceTracker.exe` from the releases page
2. No installation required - just double-click to run!

## Usage

### Starting the Application

1. Double-click `AMRSMaintenanceTracker.exe`
2. The application will start and automatically connect to the AMRS server
3. If prompted, enter your login credentials

### Working Offline

The application will automatically cache pages you visit for offline use. If your connection is lost:

1. You'll see "Offline" in the status indicator
2. You can still access previously visited pages
3. Any maintenance records created while offline will be synchronized when you reconnect

### Keyboard Shortcuts

- **F5**: Refresh current page
- **Ctrl+H**: Go to home page
- **Alt+Left**: Back
- **Alt+Right**: Forward
- **Alt+F4**: Exit application

## Troubleshooting

### Application Won't Start

If the application fails to start:

1. Make sure you're running it on Windows 10 or newer
2. Try right-clicking and selecting "Run as Administrator"
3. Check that your antivirus isn't blocking the application
4. Look for a log file in `%USERPROFILE%\.amrs-maintenance\app.log`

### Connection Issues

If you see "Offline" status:

1. Check your internet connection
2. Verify the server is running at: https://amrs-preventative-maintenance.onrender.com
3. Try clicking the "Refresh" button

## Building from Source

If you need to rebuild the application:

1. Clone the repository
2. Install Python 3.8 or newer
3. Run `python build_windows_app.py`
4. The executable will be created in the `dist` folder
