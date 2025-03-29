# AMRS Maintenance Tracker Windows Client

The Windows client application for the AMRS Preventative Maintenance System, designed for technicians and maintenance personnel to track and record maintenance activities with full offline support.

## Features

- **Offline Operation**: Continue working without an internet connection
- **Background Synchronization**: Automatically sync data when connectivity is restored
- **Secure Credential Storage**: Safely store login information for quick access
- **Local Data Caching**: Store maintenance data locally for offline access
- **Portable Mode**: Run without installation from any storage media
- **Visual Indicators**: Clear status indicators for maintenance items
- **System Tray Integration**: Minimize to system tray for continuous background operation
- **Dashboard View**: At-a-glance overview of maintenance status

## Installation Options

### Portable Application (No Installation Required)

1. Download the latest portable package from the [releases page](https://github.com/yourusername/AMRS-Preventative-Maintenance/releases)
2. Extract the ZIP file to any location (e.g., USB drive, desktop, etc.)
3. Run `MaintenanceTracker.exe` directly
4. The application will create a `data` folder in the same directory for portable data storage

### Standard Installation

1. Download the installer from the [releases page](https://github.com/yourusername/AMRS-Preventative-Maintenance/releases)
2. Run the installer and follow the prompts
3. The application will be accessible from the Start Menu and Desktop

## Configuration

On first run, you'll need to provide:
1. **Server URL**: The address of your AMRS server (e.g., `http://server-address:9000`)
2. **Username and Password**: Your login credentials
3. Optional: Check "Remember my credentials" for automatic login

## Usage Guide

### Dashboard

The dashboard provides a quick overview of:
- Overdue maintenance items
- Maintenance due soon
- Total parts in the system

### Maintenance Recording

1. Navigate to the "Maintenance" tab
2. Filter items by site, machine, or status
3. Select a part that needs maintenance
4. Click "Record Maintenance" or double-click the part
5. Enter maintenance notes and submit

### Offline Operation

When working offline:
1. An "OFFLINE MODE" indicator will appear in the status bar
2. All maintenance records are saved locally
3. When connection is restored, data will automatically sync with the server
4. Use "Force Sync" button to manually trigger synchronization

## Building from Source

To build the Windows client from source:

1. Clone the repository
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

3. For portable executable:
   ```bash
   python build.py
   ```

4. The executable will be available in the `dist` folder

## Troubleshooting

### Connection Issues
- Verify the server URL is correct
- Check that the server is running and accessible
- If behind a proxy, ensure proper network configuration

### Sync Problems
- Check the log files in `%USERPROFILE%\.amrs\logs` (installed version) or `logs` folder (portable version)
- Try using "Force Sync" when connected
- Restart the application if sync issues persist

## Log File Locations

- Installed version: `%USERPROFILE%\.amrs\logs\MaintenanceTrackerClient.log`
- Portable version: `logs\MaintenanceTrackerClient.log` (relative to executable)

## Data Storage

- Installed version: User settings and data in `%USERPROFILE%\.amrs\`
- Portable version: Data stored in `data\` folder next to the executable
