# AMRS Maintenance Tracker - Windows WebView2 Application

This document explains how to use the WebView2-based Windows native application for AMRS Maintenance Tracker.

## Overview

Instead of using Electron, this application uses Microsoft Edge WebView2 to create a native Windows application that hosts the Flask web application. This approach has several advantages:

- Smaller application size (no need to bundle a complete Chromium browser)
- Better system integration as a native Windows application
- Better performance with lower memory usage
- Leverages the WebView2 component already installed on Windows 10/11

## How It Works

The application architecture consists of:

1. **webview_app.py** - The main application entry point that creates a native Windows window using PyWebView
2. **app_bootstrap.py** - A bootstrap script that starts the Flask server and extracts necessary resources in packaged mode
3. **build_windows_app.py** - A build script that uses PyInstaller to create a standalone Windows executable

When run, the application:

1. Starts the Flask server in the background
2. Creates a native Windows window using WebView2
3. Loads the Flask web application in the WebView2 control

## Requirements

- Windows 10 or 11 with WebView2 Runtime installed
- Python 3.8 or higher (for development only, not needed for end-users)
- Required Python packages (listed in requirements-windows.txt)

## Development Setup

1. Install Python 3.8 or higher
2. Install the required packages:
   ```
   pip install -r requirements-windows.txt
   ```
3. Run the application in development mode:
   ```
   python webview_app.py
   ```

## Building a Standalone Executable

### Using the Batch File (Recommended)

1. Double-click `build_windows_app.bat` to build the application
2. The executable will be created in the `dist` folder

### Manual Build

1. Install PyInstaller and other required packages:
   ```
   pip install pyinstaller pywebview requests
   pip install -r requirements-windows.txt
   ```
2. Run the build script:
   ```
   python build_windows_app.py
   ```
3. Optional build arguments:
   - `--debug` to build a debug version with console output
   - `--onedir` to build as a directory instead of a single file
   - `--no-clean` to skip cleaning build directories before building

## Distribution

The standalone executable can be distributed to users who have WebView2 Runtime installed. The WebView2 Runtime is included with Windows 11 and recent updates of Windows 10, but for older systems, users may need to install it separately.

Microsoft Edge WebView2 Runtime download: https://developer.microsoft.com/en-us/microsoft-edge/webview2/

## Troubleshooting

If you encounter issues with the WebView2 application:

1. Ensure the WebView2 Runtime is installed
2. Check if the Flask server is starting correctly (with `--debug` flag)
3. Verify network connectivity if the application makes external API calls
4. Check for any firewall or security software blocking the local Flask server