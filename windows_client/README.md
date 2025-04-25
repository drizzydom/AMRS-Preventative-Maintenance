# AMRS Maintenance Tracker Windows Client

The Windows client application for the AMRS Preventative Maintenance System, designed for technicians and maintenance personnel to track and record maintenance activities with full offline support.

## Features

- **Offline Operation**: Work without an internet connection
- **Automatic & Background Sync**: Data synchronizes when connectivity is restored
- **Secure Credential Storage**: Credentials stored securely for quick access
- **Local Data Caching**: Maintenance data stored locally for offline access
- **Portable Mode**: Run without installation from any storage media
- **Visual Indicators**: Clear status for maintenance items
- **System Tray Integration**: Minimize to tray for background operation
- **Dashboard View**: At-a-glance overview
- **Analytics & Reporting**: Visual reports and trends
- **Scheduled Maintenance Reminders**: Notifications for upcoming/overdue maintenance
- **Localization**: Multi-language support
- **Accessibility**: High contrast mode, keyboard navigation, screen reader support

## Installation

### Portable Application
1. Download the latest portable package from the [releases page](https://github.com/yourusername/AMRS-Preventative-Maintenance/releases)
2. Extract the ZIP file to any location (e.g., USB drive, desktop, etc.)
3. Run `MaintenanceTracker.exe` directly
4. The application will create a `data` folder in the same directory for portable data storage

### Standard Installation
1. Download the installer from the [releases page](https://github.com/yourusername/AMRS-Preventative-Maintenance/releases)
2. Run the installer and follow the prompts
3. The application will be accessible from the Start Menu and Desktop

## Configuration

On first run, provide:
- **Server URL**: Address of your AMRS server (e.g., `http://server-address:9000`)
- **Username and Password**: Your login credentials
- Optionally, check "Remember my credentials" for automatic login

## Advanced Features

- **Analytics & Reporting**: Generate and export reports (CSV/JSON)
- **Scheduled Maintenance Reminders**: Set up recurring schedules, receive notifications, customize intervals
- **Localization & Accessibility**: Multi-language, high contrast, keyboard navigation, screen reader support

## Building from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/AMRS-Preventative-Maintenance.git
   cd AMRS-Preventative-Maintenance/windows_client
   ```
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Build the application:
   ```bash
   python build.py
   ```
4. The executable will be available in the `dist` folder.

## Troubleshooting

- **Connection Issues**: Verify server URL, check server status, network configuration
- **Sync Problems**: Check log files, try "Force Sync", restart the app
- **Performance**: Optimize database, reduce offline data, check system requirements

### Log File Locations
- Installed: `%USERPROFILE%\.amrs\logs\MaintenanceTrackerClient.log`
- Portable: `logs\MaintenanceTrackerClient.log` (relative to executable)

### Data Storage
- Installed: `%USERPROFILE%\.amrs\`
- Portable: `data\` folder next to the executable

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.
