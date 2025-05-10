# AMRS Maintenance Tracker - Desktop Application

A standalone desktop version of the AMRS Maintenance Tracker application. Provides the same functionality as the web application in a native desktop environment, with full offline support and a consistent user interface.

## Features

- **Electron-based Windows application** with Flask backend
- **Works offline** with automatic data synchronization
- **Secure storage** with SQLCipher database encryption
- **Identical UI** to the web application
- **Simplified installation** and portable options

## Building the Application

### Prerequisites
- Python 3.9+ (recommended)
- Node.js 16+ and npm
- Windows 10 or newer

### Build Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/AMRS-Preventative-Maintenance.git
   cd AMRS-Preventative-Maintenance
   ```
2. Set up the Python environment:
   ```bash
   python setup_env.py
   ```
3. Set up the Electron environment:
   ```bash
   cd electron_app
   npm install
   cd ..
   ```
4. Run the build script:
   ```bash
   build_windows_app.bat
   ```
   or using Node.js directly:
   ```bash
   node build_electron_app.js
   ```
5. The built application will be available in the `dist/electron` directory.

## Usage

### Installation

1. Download the NSIS installer (`AMRS-Maintenance-Tracker-Setup-x.x.x.exe`) or the portable version (`AMRS-Maintenance-Tracker-Portable-x.x.x.exe`)
2. Install or extract the application
3. Run the application
4. Log in with your AMRS Maintenance Tracker credentials

### Offline Mode

- The application automatically detects when you're offline
- All changes made while offline are stored locally
- When you reconnect, click "Sync Now" to synchronize changes with the server
- Status indicators show current connection and sync status

### Database Security

- Local data is encrypted using SQLCipher
- Your login password is used as the encryption key
- You can change your database password in Settings > Database Settings

## Development

- `electron_app/main.js`: Main Electron application logic
- `electron_app/preload.js`: Bridge between Electron and web UI
- `electron_app/app.py`: Flask application for Electron
- `app-launcher.py`: Script to launch the appropriate Flask app
- `offline_adapter.py`: Adapter for offline database operations
- `sync_api.py`: API endpoints for data synchronization
- `hybrid_dao.py`: Data access layer supporting online and offline modes

## Offline Support

- SQLCipher encrypted database for secure data storage
- Complete offline functionality identical to online version
- Bidirectional synchronization with conflict resolution
- Role-based permissions enforced in offline mode
- Visual indicators for connection status and pending changes

## Troubleshooting

### Sync Issues
- Check the Offline Status page for detailed sync information
- Verify your internet connection
- Try restarting the application if sync fails repeatedly

### Database Issues
- If you encounter database errors, verify your password is correct
- For persistent issues, you can reset the database encryption by uninstalling and reinstalling the application

### Logs
- Electron logs: `%APPDATA%\AMRS Maintenance Tracker\logs\main.log`
- Flask logs: `%APPDATA%\AMRS Maintenance Tracker\flask-log.txt`

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
