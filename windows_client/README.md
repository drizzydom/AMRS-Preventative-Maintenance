# Maintenance Tracker Windows Client

This is the Windows desktop client for the Maintenance Tracker application. It provides a native interface for users to interact with the maintenance system.

## Features

- Login with your existing Maintenance Tracker credentials
- View dashboard with maintenance statistics
- View and filter parts by status (overdue, due soon, ok)
- Record maintenance for parts
- Works offline with local data caching
- Minimizes to system tray for easy access

## Requirements

- Windows 10 or newer
- Internet connection (for syncing with the server)

## Installation

### Option 1: Installer

1. Download `MaintenanceTrackerSetup.exe` from the releases page
2. Run the installer and follow the prompts
3. Launch the application from the Start Menu or desktop shortcut

### Option 2: Portable Version

1. Download `MaintenanceTracker_Portable_1.0.0.zip` from the releases page
2. Extract the ZIP file to any location
3. Run `MaintenanceTracker.exe`

## Configuration

On first run, you'll need to configure the connection to your Maintenance Tracker server:

1. Enter the server URL (e.g., `http://localhost:9000` or your server's domain)
2. Enter your username and password
3. Click Login

Your connection settings will be saved for future use.

## Building from Source

If you want to build the application yourself:

1. Install Python 3.10 or newer
2. Clone the repository
3. Navigate to the `windows_client` directory
4. Install requirements: `pip install -r requirements.txt`
5. Run the application: `python main.py`

### Building the Executable

1. Install PyInstaller: `pip install pyinstaller`
2. Run the build script: `python build.py`
3. The executable and installer will be created in the `dist` folder

## Troubleshooting

- **Connection Issues**: Ensure the server URL is correct and the server is running
- **Login Failures**: Verify your username and password
- **Application Crashes**: Check the log file in `%APPDATA%\MaintenanceTrackerClient\logs.txt`

## License

This software is proprietary and confidential.
