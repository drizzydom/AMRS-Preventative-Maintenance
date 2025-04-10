# AMRS Preventative Maintenance System

A comprehensive desktop and web application for tracking and managing preventative maintenance for AMRS equipment. This system provides both online and offline functionality through an Electron packaged desktop application with a Flask backend.

<p align="center">
  <img src="static/img/logo.png" alt="AMRS Maintenance Tracker Logo" width="200"/>
</p>

## Table of Contents

- [Overview](#overview)
- [Repository Structure](#repository-structure)
- [System Requirements](#system-requirements)
- [Development Setup](#development-setup)
  - [Python Environment](#python-environment)
  - [Node.js Environment](#nodejs-environment)
  - [Database Setup](#database-setup)
  - [Database Migrations](#database-migrations)
- [Running the Application](#running-the-application)
  - [Development Mode](#development-mode)
  - [Production Mode](#production-mode)
- [Building the Desktop Application](#building-the-desktop-application)
- [Architecture](#architecture)
- [Customization](#customization)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Overview

AMRS Preventative Maintenance System combines a Flask web application with an Electron desktop wrapper to provide:

- Tracking of equipment maintenance schedules
- Recording of maintenance activities
- Visual indicators for overdue maintenance
- Offline functionality with automatic syncing
- User management with role-based permissions
- Custom reporting capabilities

The system features dual-mode operation, working with both a local cache for offline use and connecting to a web server when online, with a visual indicator showing the current connection mode.

## Repository Structure

```
AMRS-Preventative-Maintenance/
├── app.py                     # Main Flask application entry point
├── models.py                  # Database models using SQLAlchemy
├── add_password_reset_columns.py # Database migration script for password reset
├── electron_app/             # Electron application files
│   ├── main.js               # Main Electron process
│   ├── preload.js            # Preload script for IPC
│   ├── icons/                # Application icons
│   └── utils/                # Electron utility modules
├── static/                    # Static web assets (CSS, JS, images)
├── templates/                 # HTML templates for Flask
├── modules/                   # Additional Python modules
├── package.json               # Node.js dependencies and scripts
├── package-venv.bat           # Script for creating Python virtual environment
├── flask-launcher.py          # Launcher script for Flask in packaged app
├── requirements.txt           # Python dependencies
└── instance/                  # Instance-specific data (DB)
```

## System Requirements

### Prerequisites

- **Python 3.9+** - Backend server runtime
- **Node.js 16+** - For Electron desktop application
- **SQLite** - Database (included with Python)
- **Git** - For version control
- **Windows 10/11** - Primary target OS for desktop application

### Space Requirements

- 200MB disk space for application
- Additional space for database growth (varies by usage)
- 2GB RAM minimum, 4GB recommended

## Development Setup

### Python Environment

1. **Create virtual environment**:

   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install Python dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

   Key dependencies include:
   - Flask
   - SQLAlchemy
   - pandas
   - openpyxl
   - Werkzeug
   - Jinja2

### Node.js Environment

1. **Install Node.js dependencies**:

   ```bash
   npm install
   ```

   Key dependencies include:
   - electron
   - electron-builder
   - electron-updater
   - electron-log

2. **Set up development tools**:

   ```bash
   npm install -g electron-packager
   ```

### Database Setup

1. **Initialize the database**:

   ```bash
   python -c "from app import db; db.create_all()"
   ```

2. **Run migration scripts if needed**:

   ```bash
   python add_password_reset_columns.py
   ```

### Database Migrations

The repository includes database migration scripts to handle schema changes:

#### Password Reset Migration

The `add_password_reset_columns.py` script adds password reset functionality columns to the User table:

```python
# Script to add password reset columns to the User table
# Run this script to fix the "no such column: user.reset_token" error

def add_password_reset_columns():
    """Add reset_token and reset_token_expiration columns to the user table."""
    # Path to the SQLite database
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'maintenance.db')
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return False
        
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(user)")
        columns = [col[1] for col in cursor.fetchall()]
        
        columns_added = False
        
        # Add reset_token column if it doesn't exist
        if 'reset_token' not in columns:
            print("Adding reset_token column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN reset_token VARCHAR(100)")
            columns_added = True
        else:
            print("reset_token column already exists")
            
        # Add reset_token_expiration if it doesn't exist
        if 'reset_token_expiration' not in columns:
            print("Adding reset_token_expiration column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN reset_token_expiration DATETIME")
            columns_added = True
        else:
            print("reset_token_expiration column already exists")
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        # Print status message
        if columns_added:
            print("Password reset columns added successfully!")
        else:
            print("No changes needed. Password reset columns already exist.")
        
        return True
    except Exception as e:
        print(f"Error adding password reset columns: {str(e)}")
        return False
```

To run this migration:

```bash
python add_password_reset_columns.py
```

This script should be run when you encounter errors related to missing password reset columns.

## Running the Application

### Development Mode

1. **Start Flask server**:

   ```bash
   python app.py
   ```

2. **Start Electron app in development mode**:

   ```bash
   npm start
   ```

### Production Mode

Use the packaged application or build it from source (see next section).

## Building the Desktop Application

### Build Process

1. **Create Python virtual environment for distribution**:

   ```bash
   package-venv.bat
   ```

   This script:
   - Creates a Python virtual environment
   - Installs required packages
   - Prepares the environment for packaging

2. **Build Electron application**:

   ```bash
   npm run dist
   ```

   This creates:
   - An installer in the `dist` folder
   - A portable version for distribution

### Customizing the Build

Edit `package.json` in the `build` section to customize:
- Application name and metadata
- Icons and resources
- Installer properties
- File inclusions/exclusions

## Architecture

### Three-Tier Architecture

1. **Data Layer**: SQLite database with SQLAlchemy ORM
2. **Application Layer**: Flask backend providing API and business logic
3. **Presentation Layer**: HTML/CSS/JS frontend within Electron shell

### Connection States

The application operates in three modes:
1. **Connected to local cache** (green indicator): Working with local database
2. **Connected to web server** (blue indicator): Working with remote server
3. **Disconnected** (red indicator): Unable to connect to either source

### Key Components

- **Flask Application**: Handles database operations and business logic
- **Electron Wrapper**: Creates desktop application experience
- **Connection Manager**: Monitors and manages connection states
- **Automatic Updater**: Handles application updates when available

## Customization

### Flask Application Customization

- Routes defined in `app.py`
- Templates in `templates/` directory
- Static assets in `static/` directory
- Database models in `models.py`

### Electron Application Customization

- Main process in `electron_app/main.js`
- IPC bridge in `electron_app/preload.js`
- Connection status in `electron_app/utils/connectionStatus.js`

### Adding Features

1. **New Database Model**:
   - Add model class to `models.py`
   - Create migration script similar to `add_password_reset_columns.py`
   - Run migration script to update database

2. **New Page/Feature**:
   - Add route to `app.py`
   - Create template in `templates/`
   - Add any required static assets
   - Link from existing navigation

## Testing

### Python Unit Tests

```bash
python -m unittest discover tests
```

### Electron Application Testing

```bash
npm test
```

## Troubleshooting

### Database Issues

For "no such column: user.reset_token" errors:

```bash
python add_password_reset_columns.py
```

This script adds missing password reset functionality columns to the User table.

### Connection Issues

- **Local Connection**: Check if Flask server is running
- **Web Connection**: Verify network connectivity and server URL
- **Indicator Missing**: Restart application or check console for errors

### Build Problems

- **Python Environment**: Run `package-venv.bat` to recreate environment
- **Icon Errors**: Ensure icons are at least 256x256 pixels
- **Missing Files**: Check `package.json` includes all necessary files
- **Module Errors**: Run `npm install` and try again

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests to ensure functionality
5. Submit a pull request

---

&copy; 2023-2025 AMRS Maintenance. All rights reserved.
