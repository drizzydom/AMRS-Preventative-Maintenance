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
- **Analytics and Reporting**: Generate visual reports and trends for maintenance activities
- **Scheduled Maintenance Reminders**: Notifications for upcoming and overdue maintenance
- **Localization**: Multi-language support for global users
- **Accessibility Features**: High contrast mode, keyboard navigation, and screen reader support

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

## Advanced Features

### Analytics and Reporting

- Generate visual reports for maintenance trends and system health
- View maintenance statistics by part, machine, or site
- Export reports in CSV or JSON format

### Scheduled Maintenance Reminders

- Set up recurring maintenance schedules for parts
- Receive notifications for upcoming and overdue maintenance
- Customize reminder intervals and notification preferences

### Localization and Accessibility

- Multi-language support with easy language switching
- High contrast mode for improved visibility
- Full keyboard navigation and screen reader compatibility

## Building from Source

To build the Windows client from source:

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

### Connection Issues
- Verify the server URL is correct
- Check that the server is running and accessible
- If behind a proxy, ensure proper network configuration

### Sync Problems
- Check the log files in `%USERPROFILE%\.amrs\logs` (installed version) or `logs` folder (portable version)
- Try using "Force Sync" when connected
- Restart the application if sync issues persist

### Performance Issues
- Ensure your device meets the minimum system requirements
- Optimize the database using the built-in tools
- Reduce the amount of data stored offline by adjusting data retention settings

## Log File Locations

- Installed version: `%USERPROFILE%\.amrs\logs\MaintenanceTrackerClient.log`
- Portable version: `logs\MaintenanceTrackerClient.log` (relative to executable)

## Data Storage

- Installed version: User settings and data in `%USERPROFILE%\.amrs\`
- Portable version: Data stored in `data\` folder next to the executable
