# AMRS Preventative Maintenance System

A comprehensive desktop and web application for tracking and managing preventative maintenance for AMRS equipment. This system provides both online and offline functionality through a Python-based desktop application with a Flask backend.

<p align="center">
  <img src="static/img/logo.png" alt="AMRS Maintenance Tracker Logo" width="200"/>
</p>

## Table of Contents
- [Overview](#overview)
- [Repository Structure](#repository-structure)
- [System Requirements](#system-requirements)
- [Development Setup](#development-setup)
- [Building and Running the Windows Client](#building-and-running-the-windows-client)
- [Features](#features)
- [Advanced Features](#advanced-features)
- [Architecture](#architecture)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Audit Reminder System](#audit-reminder-system)
- [License and Legal](#license-and-legal)

## Overview

AMRS Preventative Maintenance System combines a Flask web application with a Python-based desktop client to provide:

- Tracking of equipment maintenance schedules
- Recording of maintenance activities
- Visual indicators for overdue maintenance
- Offline functionality with automatic syncing
- Analytics and reporting for maintenance trends
- Scheduled maintenance reminders
- Localization and accessibility features
- Diagnostics and system health monitoring
- Full offline/online synchronization
- Standalone desktop experience (no web browser required)

## Repository Structure

```
AMRS-Preventative-Maintenance/
├── app.py                     # Main Flask application entry point
├── models.py                  # Database models using SQLAlchemy
├── windows_client/            # Windows client application
│   ├── build.py               # Build script for the Windows client
│   ├── requirements.txt       # Python dependencies for the client
│   ├── docs/                  # Documentation for the client
│   ├── analytics/             # Analytics and reporting modules
│   ├── scheduler.py           # Scheduled maintenance reminders
│   ├── localization.py        # Localization support
│   └── ...                    # Other client modules
├── static/                    # Static web assets (CSS, JS, images)
├── templates/                 # HTML templates for Flask
├── requirements.txt           # Python dependencies for the server
└── instance/                  # Instance-specific data (DB)
```

## System Requirements

### Prerequisites

- **Python 3.10+** - Backend server runtime and Windows client
- **SQLite** - Database (included with Python)
- **Windows 10/11** - Primary target OS for the desktop client

## Development Setup

### Python Environment

1. **Create virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install Python dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

## Building and Running the Windows Client

1. Navigate to the `windows_client` directory:
   ```bash
   cd windows_client
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Build the application:
   ```bash
   python build.py
   ```
   - For a portable build, add `--portable`.
   - For an installer, add `--installer`.
4. The executable will be available in the `dist` folder.
5. Run the app by launching `MaintenanceTracker.exe` (or the generated executable).

### Usage Highlights
- On launch, a splash screen will show database synchronization status.
- A pop-up bubble will indicate online/offline status.
- The app works fully offline, with automatic sync when reconnected.
- All features are available offline, including analytics and reporting.
- The app runs as a standalone desktop application (not in a web browser).

## Features

- **Offline Operation**: Continue working without an internet connection
- **Automatic Sync**: Data synchronizes when connectivity is restored
- **Splash Screen**: Shows sync status at launch
- **Pop-up Status**: Online/offline status bubble
- **Background Synchronization**: Syncs in the background
- **Secure Credential Storage**: Safely store login information
- **Local Data Caching**: Store maintenance data locally
- **Portable Mode**: Run without installation from any storage media
- **Visual Indicators**: Clear status for maintenance items
- **System Tray Integration**: Minimize to tray for background operation
- **Dashboard View**: At-a-glance overview
- **Analytics and Reporting**: Visual reports and trends
- **Diagnostics**: System health and performance monitoring
- **Scheduled Maintenance Reminders**: Notifications for upcoming/overdue maintenance
- **Localization**: Multi-language support
- **Accessibility**: High contrast mode, keyboard navigation, screen reader support

## Advanced Features

### Offline/Online Synchronization
- The app detects network changes and syncs data automatically.
- All changes made offline are queued and sent to the server when online.

### Analytics and Diagnostics
- Built-in analytics dashboard for maintenance trends and system health.
- Diagnostics tools for performance and error reporting.

### Accessibility & Localization
- High contrast and accessible UI.
- Keyboard navigation and screen reader compatibility.
- Language switching and multi-language support.

### Notifications & Reminders
- System tray notifications for status and reminders.
- Scheduled and on-demand maintenance reminders.

### Security
- Secure credential storage using keyring.
- Encrypted local database (optional).

## Architecture

### Key Components

- **Flask Application**: Handles database operations and business logic
- **Windows Client**: Provides a native desktop experience with offline support
- **Analytics Module**: Generates visual reports and trends
- **Scheduler**: Manages recurring maintenance reminders
- **Localization**: Supports multiple languages for global users

## Testing

### Python Unit Tests

```bash
python -m unittest discover tests
```

## Troubleshooting

### Database Issues

- Run database migrations if schema changes are required:
  ```bash
  python manage.py db upgrade
  ```

### Build Problems

- Ensure all dependencies are installed:
  ```bash
  pip install -r requirements.txt
  ```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests to ensure functionality
5. Submit a pull request

## Audit Reminder System

The AMRS Preventative Maintenance System supports automated audit reminder emails for incomplete audit tasks. This helps ensure compliance and timely completion of required audits.

### How It Works
- At the end of each day, the system checks for audit tasks that have not been completed for each machine.
- Users assigned to the relevant site and with audit reminders enabled in their notification preferences will receive an email reminder for each incomplete audit task.
- The reminder email includes the site, machine, audit task name, and interval.

### Enabling Audit Reminders
- Each user can enable or disable audit reminders in their notification preferences (see your profile page in the web app).
- Site administrators can ensure that site notification settings are enabled for audit reminders to be sent.

### Running the Notification Scheduler

To send audit reminders automatically, schedule the following command to run daily (e.g., at 5:00 PM):

```
python notification_scheduler.py audit
```

#### Example: macOS launchd (Cron Alternative)

1. Create a file at `~/Library/LaunchAgents/com.amrs.auditreminder.plist` with the following contents:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.amrs.auditreminder</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/dominicmoriello/Documents/GitHub/AMRS-Preventative-Maintenance/notification_scheduler.py</string>
        <string>audit</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>17</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/amrs_auditreminder.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/amrs_auditreminder.err</string>
</dict>
</plist>
```

2. Load the job:

```
launchctl load ~/Library/LaunchAgents/com.amrs.auditreminder.plist
```

### Manual Run
You can also run reminders manually at any time:

```
python notification_scheduler.py audit
```

### Template
The reminder email uses `templates/email/audit_reminder.html`.

---

For more information, see the user profile notification preferences and the [notification_scheduler.py](notification_scheduler.py) script.

## License and Legal

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
