# AMRS Maintenance Tracker - Desktop Application User Guide

This guide provides instructions for building, installing, and using the AMRS Maintenance Tracker desktop application.

## Table of Contents

1. [Building the Application](#building-the-application)
2. [Installing the Application](#installing-the-application)
3. [Using the Application](#using-the-application)
4. [Working Offline](#working-offline)
5. [Troubleshooting](#troubleshooting)
6. [Advanced Configuration](#advanced-configuration)

## Building the Application

### Prerequisites

- Windows 10 or newer
- Python 3.7 or newer
- Administrator rights (for installation of dependencies)
- Internet connection (for downloading dependencies)

### Build Steps

1. Open a command prompt with administrator privileges
2. Navigate to the project directory:
   ```
   cd c:\Users\Dominic\Documents\GitHub\AMRS-Preventative-Maintenance
   ```

3. Run the build script:
   ```
   python build_desktop_app.py
   ```

4. Wait for the build process to complete. This may take several minutes as it downloads and installs all necessary dependencies.

5. Once complete, the application will be available in:
   ```
   c:\Users\Dominic\Documents\GitHub\AMRS-Preventative-Maintenance\dist\AMRSMaintenanceTracker\
   ```

### Build Options

The build script supports several options:

- `--debug`: Build a debug version with console window for troubleshooting
- `--skip-deps`: Skip installing dependencies (use if you've already installed them)
- `--server-url URL`: Pre-configure a specific server URL
- `--portable`: Create a portable version that stores all data in its own directory
- `--verbose` or `-v`: Show more detailed output during the build

Example with options:
```
python build_desktop_app.py --debug --server-url http://your-server:9000
```

## Installing the Application

### Regular Installation

1. After building, you can copy the entire `dist\AMRSMaintenanceTracker` directory to any location on your computer.

2. Create a shortcut to `AMRSMaintenanceTracker.exe` on your desktop or start menu.

3. Run the application by double-clicking the executable or shortcut.

### Portable Mode

If you built with the `--portable` option, the application will store all its data within the application directory, making it suitable for use on USB drives or shared environments.

1. Copy the entire `dist\AMRSMaintenanceTracker` directory to your USB drive or other portable storage.

2. Run `AMRSMaintenanceTracker.exe` directly from that location.

## Using the Application

### First Run

1. Launch the application by running `AMRSMaintenanceTracker.exe`.

2. The application will start a local server and open the Maintenance Tracker interface in a Chromium browser window.

3. If this is the first time running the application, you'll be prompted to log in:
   - Default username: `admin`
   - Default password: `admin`

4. **IMPORTANT**: For security reasons, immediately change the default password after logging in for the first time.

### Basic Navigation

The desktop application provides the same interface as the web version, with these key sections:

- **Dashboard**: Overview of all maintenance items, showing overdue and upcoming tasks
- **Sites**: Manage sites, machines, and parts
- **Maintenance**: Record maintenance activities and view history
- **Admin**: User management, backups, and system settings (admin users only)

### Keyboard Shortcuts

- `Ctrl+R`: Refresh the current page
- `F5`: Refresh the current page
- `Ctrl+F`: Find on the current page
- `Alt+Left`: Go back to previous page
- `Alt+Right`: Go forward

## Working Offline

The desktop application provides offline capabilities, allowing you to continue working when internet connectivity is limited or unavailable.

### How Offline Mode Works

1. **Automatic Detection**: The application automatically detects when you're offline.

2. **Data Caching**: While online, the application caches data from the API endpoints you've accessed.

3. **Offline Actions**: When offline, you can still:
   - View previously accessed sites, machines, and parts
   - Record maintenance activities
   - Create new parts or machines

4. **Synchronization**: When you regain connectivity, the application automatically synchronizes your offline changes with the server.

### Using Offline Mode

1. **Prepare for Offline Use**: Before going offline, navigate to the pages you anticipate needing to ensure their data is cached.

2. **Working Offline**: Use the application as normal. A notification will appear in the application header when in offline mode.

3. **Coming Back Online**: When internet connectivity is restored, the application will automatically synchronize your changes. A notification will appear indicating synchronization is in progress.

## Troubleshooting

### Application Won't Start

1. Check the logs:
   - Application logs: `%USERPROFILE%\.amrs-maintenance\desktop_app.log`
   - CEF logs: `%USERPROFILE%\.amrs-maintenance\cef_debug.log`

2. Try running in debug mode:
   - Create a shortcut to the executable
   - Edit the shortcut properties and add `--debug` at the end of the target field
   - Run the application using this shortcut
   - Check the console window for error messages

### Connection Issues

1. Ensure your network connection is active.

2. Check if a firewall is blocking the application.

3. If you're using a pre-configured server URL, verify that the server is online and accessible.

4. Try rebuilding the application with the `--server-url` option to specify a different server.

### Database Errors

1. If you encounter database errors, try resetting the database:
   - Close the application
   - Delete or rename the `%USERPROFILE%\.amrs-maintenance\offline_data.db` file
   - Restart the application

2. If errors persist, check the logs for specific error messages.

### Sync Issues

If changes made while offline aren't synchronizing:

1. Manually trigger a sync by refreshing the page.

2. Check the application logs for sync-related errors.

3. If necessary, you can reset the offline queue by:
   - Close the application
   - Open `%USERPROFILE%\.amrs-maintenance\offline_data.db` using a SQLite browser
   - Delete all rows from the `pending_operations` table
   - Restart the application

## Advanced Configuration

### Config File

After building, you can modify the config file to customize the application:

Path: `dist\AMRSMaintenanceTracker\app_config.json`

Options:
```json
{
  "app_name": "AMRS Maintenance Tracker",
  "app_version": "1.0.0",
  "server_url": "http://your-server:9000",
  "offline_mode": true,
  "debug": false
}
```

### Command Line Options

The desktop application supports several command line options:

- `--debug`: Run in debug mode with additional logging
- `--port PORT`: Specify a custom port for the local server

Example:
```
AMRSMaintenanceTracker.exe --debug --port 8080
```

### Updating the Application

To update to a new version:

1. Build the new version using the build script.
2. Close the currently running instance of the application.
3. Replace the old application files with the newly built ones.
4. Your data will be preserved as it's stored separately in the user's profile directory.
