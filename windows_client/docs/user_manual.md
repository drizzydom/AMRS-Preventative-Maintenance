# AMRS Maintenance Tracker - User Manual

## Overview

AMRS Maintenance Tracker is a desktop application that helps maintenance technicians track and manage preventative maintenance tasks. The application works both online and offline, synchronizing data when an internet connection is available.

## Installation

### System Requirements

- Windows 10 or later
- 4GB RAM (8GB recommended)
- 500MB free disk space
- .NET Framework 4.7.2 or later
- Internet connection for synchronization

### Installation Options

#### Standard Installation

1. Download the installer (`MaintenanceTracker-Setup.exe`) from the provided source
2. Run the installer and follow the on-screen instructions
3. The application will be installed in your Programs directory and shortcuts will be created on your desktop and start menu

#### Portable Installation

1. Download the portable zip archive (`MaintenanceTrackerPortable.zip`)
2. Extract the archive to any location (e.g., a USB drive)
3. Run `MaintenanceTracker.exe` from the extracted folder

## First-Time Setup

When you first launch the application:

1. The pre-login synchronization screen will appear
2. Enter your server URL if not already configured
3. Enter your username and password provided by your administrator
4. Click "Login"
5. The application will synchronize initial data from the server

## Main Interface

### Dashboard

The dashboard provides an overview of:

- Upcoming maintenance tasks
- Overdue maintenance items
- Recent activities
- Synchronization status

### Navigation

The main navigation menu allows access to:

- **Sites**: View and manage maintenance sites
- **Machines**: View and manage equipment at each site
- **Parts**: View and manage parts that require maintenance
- **Maintenance History**: View completed maintenance activities
- **Reports**: Generate and export reports
- **Settings**: Configure application preferences

## Working Offline

AMRS Maintenance Tracker is designed to work seamlessly offline:

1. Any changes made while offline are stored locally on your device
2. When connectivity is restored, the application will automatically synchronize with the server
3. The sync status indicator shows the current synchronization state
4. You can manually force synchronization by clicking the "Force Sync" button

## Synchronization

### Status Indicators

The application displays synchronization status in the bottom panel:

- 🟢 **Online**: Connected to server, data is in sync
- 🟡 **Syncing**: Currently synchronizing data with server
- 🔴 **Offline**: Not connected to server, changes stored locally

### Manual Synchronization

To manually trigger synchronization:

1. Click the "Force Sync" button in the sync status panel
2. The application will attempt to connect to the server and sync all pending changes
3. A progress bar will display the sync progress
4. Upon completion, a summary of the sync results will be shown

### Conflict Resolution

When both the server and client have changes to the same data, conflicts may occur:

1. The application will resolve conflicts based on your configuration preference:
   - **Server Wins**: The server's version is always used
   - **Client Wins**: Your local changes are preserved
   - **Newest Wins**: The most recently updated version is used
   - **Ask Me**: You'll be prompted to choose which version to keep

2. To change the conflict resolution strategy, go to Settings > Synchronization

## Data Security

### Local Database Encryption

By default, all offline data is encrypted to protect sensitive information:

1. The encryption uses industry-standard algorithms
2. Each installation has a unique encryption key
3. Encrypted data cannot be accessed by unauthorized users or applications

### Authentication

The application supports secure authentication:

1. User credentials are stored securely in the system keyring
2. Authentication tokens automatically refresh when needed
3. Option to automatically log out after a period of inactivity

## Reports

### Available Reports

The application supports various report types:

1. **Synchronization History**: Records of all sync activities
2. **Failed Operations**: Details about operations that couldn't sync
3. **Performance Metrics**: Application performance statistics
4. **Maintenance Reports**: Scheduled and completed maintenance activities

### Generating Reports

To generate a report:

1. Navigate to the Reports section
2. Select the desired report type
3. Set the date range and other parameters
4. Choose the output format (CSV or JSON)
5. Click "Generate Report"
6. Save or open the generated report file

## Preferences

To customize application settings:

1. Navigate to Settings > Preferences
2. Adjust settings in the following categories:
   - **General**: Application behavior and server connection
   - **Synchronization**: Sync frequency and conflict resolution
   - **Display**: Theme and visual preferences
   - **Advanced**: Logging, diagnostics, and security options
3. Click "Save" to apply your changes

## Troubleshooting

### Connection Issues

If you experience connection problems:

1. Check your internet connection
2. Verify the server URL in Settings > General
3. Confirm with your administrator that the server is running
4. Check if your authentication has expired and re-login if necessary

### Synchronization Problems

If synchronization fails:

1. Check the failed operations in the Sync Status Dashboard
2. Review the application logs for error details
3. Try a manual sync using the "Force Sync" button
4. If problems persist, use the "Generate Diagnostics Report" option and contact support

### Performance Issues

If the application runs slowly:

1. Ensure your device meets the minimum system requirements
2. Check available disk space
3. Clear the application cache in Settings > Advanced
4. Consider reducing the amount of data stored offline by adjusting data retention settings

## Getting Help

For additional assistance:

- Click the Help button (?) in any screen for context-sensitive help
- Review the FAQ section in the Help menu
- Contact your system administrator
- Email support at support@amrs-maintenance.com
