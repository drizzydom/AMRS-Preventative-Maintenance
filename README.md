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
- [Building the Windows Client](#building-the-windows-client)
- [Architecture](#architecture)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
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

### Building the Windows Client

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

4. The executable will be available in the `dist` folder.

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

## License and Legal

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
