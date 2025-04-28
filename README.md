# AMRS Preventative Maintenance System

A comprehensive desktop and web application for tracking and managing preventative maintenance for AMRS equipment. The system provides both online and offline functionality through a Python-based desktop application with a Flask backend.

<p align="center">
  <img src="static/img/logo.png" alt="AMRS Maintenance Tracker Logo" width="200"/>
</p>

## Table of Contents
- [Overview](#overview)
- [Repository Structure](#repository-structure)
- [System Requirements](#system-requirements)
- [Installation](#installation)
  - [Server](#server)
  - [Desktop Client](#desktop-client)
- [Features](#features)
- [Advanced Features](#advanced-features)
- [Architecture](#architecture)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [Recent Updates](#recent-updates)
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
- Automated notifications for overdue and upcoming maintenance
- Full offline/online synchronization
- Standalone desktop experience (no web browser required)

## Repository Structure

```
AMRS-Preventative-Maintenance/
├── app.py                     # Main Flask application entry point
├── models.py                  # Database models using SQLAlchemy
├── static/                    # Static web assets (CSS, JS, images)
│   ├── css/                   # Stylesheets  
│   ├── js/                    # JavaScript files
│   │   ├── dashboard.js       # Dashboard functionality
│   │   ├── ajax-loader.js     # Data synchronization
│   │   └── ...                # Other client-side scripts
│   └── img/                   # Images and icons
├── templates/                 # HTML templates for Flask
│   ├── admin/                 # Admin dashboard templates
│   ├── dashboard.html         # Main dashboard
│   ├── machines.html          # Machine management
│   └── ...                    # Other template files
├── server/                    # Server-specific components
├── notification_scheduler.py  # Automated maintenance reminders
├── config.py                  # Configuration settings
├── requirements.txt           # Python dependencies
└── instance/                  # Instance-specific data (DB)
```

## System Requirements

### Prerequisites

- **Python 3.10+** - Backend server runtime and desktop client
- **SQLite/PostgreSQL** - Database support
- **Modern Web Browser** - For web interface
- **Windows 10/11, macOS, or Linux** - Supported desktop platforms

## Installation

### Server

#### Docker Installation (Recommended)

```bash
docker-compose up -d
```

This will start the server on port 5000 by default.

#### Manual Installation

1. Ensure Python 3.10+ is installed
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure the database:
   ```bash
   python init_database.py
   ```
5. Create an admin user (follow the prompts):
   ```bash
   python app.py --create-admin
   ```
6. Start the server:
   ```bash
   python app.py
   ```

### Desktop Client

#### Standard Installation

1. Download the installer from the releases page
2. Run the installer and follow the on-screen instructions
3. The application will be installed in your Programs directory and shortcuts will be created

#### Building from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/AMRS-Preventative-Maintenance.git
   cd AMRS-Preventative-Maintenance
   ```
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Build the application:
   ```bash
   python build_desktop_app.py
   ```
4. The executable will be available in the `dist` folder.

## Features

- **Dashboard View**: At-a-glance overview of maintenance status
- **Site Management**: Organize machines by physical location
- **Machine Tracking**: Manage machine inventory with detailed information
- **Part Management**: Track individual parts requiring maintenance
- **Maintenance Recording**: Log maintenance activities with timestamps and notes
- **Status Indicators**: Clearly see overdue, due soon, and OK maintenance statuses
- **Filtering**: Filter by site, machine, and maintenance status
- **Site Overview**: Accordion view displaying machines per site
- **Notification System**: Email alerts for overdue maintenance
- **User Management**: Role-based permissions and access control
- **Offline Support**: Work without internet connectivity
- **Data Synchronization**: Automatic syncing when online

## Advanced Features

### Maintenance Status Tracking
- Color-coded visual indicators for maintenance status
- Automatic calculation of due dates based on maintenance frequency
- Sorting and filtering by status, date, and other criteria
- Detailed maintenance history for each part and machine

### Dashboard Analytics
- Summary statistics for overdue, due soon, and on-schedule maintenance
- Site-specific views and filters
- Expandable/collapsible machine parts for detailed inspection
- Mobile-responsive design for field technicians

### Notifications & Reminders
- Automated email notifications for overdue maintenance
- Configurable reminder thresholds per site
- Audit task reminder system
- User-configurable notification preferences

### Multi-Site Management
- Organize equipment by physical location
- Site-specific maintenance schedules and notification settings
- Role-based access control by site

## Architecture

### Key Components

- **Flask Application**: Handles database operations and business logic
- **SQLAlchemy ORM**: Database abstraction and model definitions
- **Bootstrap UI**: Responsive and mobile-friendly interface
- **JavaScript Modules**: Client-side interactivity and dynamic updates
- **Notification Scheduler**: Background process for sending automated reminders

## Usage

### Dashboard

The dashboard provides an at-a-glance view of your maintenance status:

1. **Summary Statistics**: Total counts of overdue, due soon, OK, and total parts.
2. **Overdue & Due Soon Panels**: Quick access to parts requiring attention.
3. **Site Overview**: Expandable view of sites, machines, and their parts.
4. **Filtering**: Filter by site using the dropdown at the top.
5. **Part Details**: Expand machine rows to see individual parts and their status.

### Recording Maintenance

1. Navigate to a part that needs maintenance
2. Click the "Record" button next to the part
3. Enter maintenance details and notes
4. Submit to update the maintenance record and reset the due date

### Managing Sites, Machines, and Parts

Admin users can:
1. Add, edit, and delete sites
2. Add machines to sites
3. Add parts to machines with specific maintenance schedules
4. Configure notification thresholds and preferences

## Troubleshooting

### Common Issues

#### Database Issues
- Run database migrations if schema changes are required:
  ```bash
  python auto_migrate.py
  ```

#### Dashboard Display Problems
- If machine statuses are not displaying correctly, refresh the page
- Check browser console for JavaScript errors
- Clear browser cache if styles or scripts appear outdated

#### Email Notifications Not Sending
- Verify email configuration in config.py
- Check notification_scheduler.py logs
- Ensure user email addresses and notification preferences are set correctly

### Log Files
- Application logs: `instance/app.log`
- Database issues: Check SQLite errors in the application log
- Email errors: Check SMTP settings in config.py

## Recent Updates

### Dashboard Enhancements (April 2025)
- **Fixed machine status display**: Corrected an issue where machines would incorrectly display "All OK" status when they had overdue or due soon parts
- **Improved site filtering**: Now properly updates machine statuses when filtering by site
- **Enhanced status indicators**: Better visual distinction between overdue, due soon, and OK status

### Audit Reminder System (March 2025)
- Added automated email reminders for incomplete audit tasks
- Configurable notification preferences per user
- Daily scheduled reminders

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

```bash
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
        <string>/path/to/AMRS-Preventative-Maintenance/notification_scheduler.py</string>
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

```bash
launchctl load ~/Library/LaunchAgents/com.amrs.auditreminder.plist
```

### Manual Run
You can also run reminders manually at any time:

```bash
python notification_scheduler.py audit
```

### Template
The reminder email uses `templates/email/audit_reminder.html`.

## License and Legal

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
