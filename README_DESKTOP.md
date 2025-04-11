# AMRS Maintenance Tracker - Desktop Application

This is a standalone desktop version of the AMRS Maintenance Tracker application. It works both online and offline, providing the same functionality as the web application in a native desktop environment.

## Features

- Full desktop application built with CEF Python (Chromium Embedded Framework)
- Runs on Windows systems
- Works offline with data synchronization when back online
- Identical user interface to the web application
- Simplified installation process

## Building the Application

### Prerequisites

- Python 3.7 or newer
- Administrator access (to install dependencies)
- Windows 10 or newer

### Build Steps

1. Clone the repository:
   ```
   git clone https://github.com/your-username/AMRS-Preventative-Maintenance.git
   cd AMRS-Preventative-Maintenance
   ```

2. Run the build script:
   ```
   python build_desktop_app.py
   ```

3. The built application will be available in the `dist/AMRSMaintenanceTracker` directory.

4. To create a debug build with console:
   ```
   python build_desktop_app.py --debug
   ```

5. To skip reinstalling dependencies:
   ```
   python build_desktop_app.py --skip-deps
   ```

## Usage

1. Run the `AMRSMaintenanceTracker.exe` file from the build directory.
2. The application will start a local server and open the interface in a Chromium browser window.
3. Log in using your existing credentials.
4. The application will work offline by caching data locally.
5. When reconnected to the network, data will synchronize automatically.

## Development

- `desktop_app.py` - Main entry point for the desktop application
- `build_desktop_app.py` - Script to build the desktop application
- `app.py` - Flask application providing the backend API and web interface

## Offline Support

The application provides offline support through:
- Local SQLite database for data storage
- Caching of resources and API responses
- Automatic synchronization when network connection is detected

## Troubleshooting

- Check the logs in `%USERPROFILE%\.amrs-maintenance\desktop_app.log`
- For CEF-specific issues, check `%USERPROFILE%\.amrs-maintenance\cef_debug.log`
- If the application fails to start, ensure all dependencies are correctly installed

## License

See the LICENSE file for details.
