# Offline Mode Usage Guide

This document provides instructions for using the offline mode in the AMRS Preventative Maintenance application.

## Running the Offline Mode

To use the application in offline mode, you can use one of the following methods:

### Method 1: Standard Start

```bash
python offline_app.py
```

### Method 2: With SQLCipher Disabled (Recommended for SQLCipher installation issues)

```bash
python run_offline_app.py
```

Or set the environment variable manually:

```bash
DISABLE_SQLCIPHER=true python offline_app.py
```

### Method 3: Reset Database and Start Fresh

If you encounter database corruption issues:

```bash
RECREATE_DB=true python run_offline_app.py
```

## Fixing SQLCipher Installation Issues

If you encounter errors related to SQLCipher installation, run:

```bash
python fix_sqlcipher.py
```

This will:
1. Attempt to fix the installation
2. Set up environment variables to disable SQLCipher
3. Configure the application to use standard SQLite without encryption

## Troubleshooting Common Issues

### "file is not a database" Error

This error occurs when the SQLite database file is corrupted. To fix:

```bash
# Remove the database file
rm -f instance/maintenance.db

# Start with a fresh database
RECREATE_DB=true python run_offline_app.py
```

### Routes Not Found or Template Issues

If certain pages like dashboard or forgot_password show errors:

1. Make sure you're using the latest version of the application
2. Restart the application completely
3. Clear your browser cache

### Connection Issues

If you see frequent connection errors in offline mode:

1. Check your browser's connection settings
2. Ensure no proxy is interfering with local connections
3. Try using a different port:

```bash
PORT=5001 python run_offline_app.py
```

## Data Synchronization

When working offline, your data is stored locally. To sync when back online:

1. Connect to a network with access to the main server
2. Click the "Sync" button in the application navbar
3. Monitor the sync progress indicator

Data conflicts are resolved using a "last update wins" strategy by default.
