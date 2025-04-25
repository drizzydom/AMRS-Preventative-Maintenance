# AMRS Maintenance Tracker - Desktop Application

A standalone desktop version of the AMRS Maintenance Tracker application. Provides the same functionality as the web application in a native desktop environment, with full offline support and a consistent user interface.

## Features

- Full desktop application (CEF Python/Chromium Embedded Framework)
- Runs on Windows 10/11
- Works offline with automatic data synchronization
- Identical UI to the web application
- Simplified installation and portable options

## Building the Application

### Prerequisites
- Python 3.10+ (recommended)
- Administrator access (to install dependencies)
- Windows 10 or newer

### Build Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/AMRS-Preventative-Maintenance.git
   cd AMRS-Preventative-Maintenance
   ```
2. Run the build script:
   ```bash
   python build_desktop_app.py
   ```
3. The built application will be available in the `dist/AMRSMaintenanceTracker` directory.
4. For a debug build:
   ```bash
   python build_desktop_app.py --debug
   ```
5. To skip reinstalling dependencies:
   ```bash
   python build_desktop_app.py --skip-deps
   ```

## Usage

- Run `AMRSMaintenanceTracker.exe` from the build directory.
- The application starts a local server and opens the interface in a Chromium browser window.
- Log in with your credentials.
- Works offline by caching data locally; synchronizes when reconnected.

## Development

- `desktop_app.py`: Main entry point for the desktop application
- `build_desktop_app.py`: Script to build the desktop application
- `app.py`: Flask backend for API and web interface

## Offline Support

- Local SQLite database for data storage
- Caching of resources and API responses
- Automatic synchronization when network is detected

## Troubleshooting

- Logs: `%USERPROFILE%\.amrs-maintenance\desktop_app.log`
- CEF issues: `%USERPROFILE%\.amrs-maintenance\cef_debug.log`
- Ensure all dependencies are installed if the app fails to start

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
