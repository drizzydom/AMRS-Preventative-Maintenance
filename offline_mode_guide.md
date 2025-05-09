# AMRS Preventative Maintenance Offline Mode Implementation Guide

This guide outlines the steps taken to implement robust offline mode functionality for the AMRS Preventative Maintenance application.

## Completed Implementation

We've successfully implemented the following components for offline mode:

1. **Unified Database Controller (`db_controller.py`)**
   - Handles both standard SQLite and encrypted SQLCipher databases
   - Provides consistent API for database operations regardless of the database type
   - Manages connection lifecycle and error handling
   - Supports essential operations like table creation, data querying, and user authentication

2. **Offline Application (`offline_app.py`)**
   - Simplified version of the main application that works entirely with local database
   - Demonstrates how offline mode functionality works
   - Includes proper user authentication and session management
   - Implements API endpoints for connection and sync status

3. **UI Enhancements for Offline Mode**
   - Added offline status indicator in the navbar
   - Implemented offline banner to clearly show when application is in offline mode
   - Added sync button and status display
   - Enhanced user experience for offline/online transitions

4. **JavaScript for Offline Detection (`offline.js`)**
   - Detects online/offline status and updates UI accordingly
   - Handles synchronization when connection is restored
   - Provides clear visual indicators of connection status
   - Supports manual synchronization trigger

## Integration Steps for Main Application

To fully integrate offline mode into the main application, follow these steps:

1. **Integrate Database Controller**
   - Add the unified `db_controller.py` to the main application
   - Modify `app.py` to use the controller for both online and offline modes
   - Configure the controller to use encryption in production

2. **Enable Offline Mode Detection**
   - Add a configuration option in `config.py` to enable/disable offline mode
   - Add environment variable support for `OFFLINE_MODE`
   - Implement detection logic that checks both configuration and actual connectivity

3. **Implement Synchronization Logic in Main App**
   - Add synchronization endpoints in `app.py` that talk to both local and server databases
   - Implement logic to track changes made while offline
   - Add conflict resolution for changes made to the same records offline and online

4. **Complete UI Integration**
   - Ensure offline status is shown consistently across all pages
   - Add sync progress indicators
   - Enhance the sync UI to show pending changes and last sync time

5. **Testing**
   - Test the application in various network conditions
   - Verify that data created offline is properly synced when online
   - Test edge cases like connection drops during sync

## Offline Database Schema

The local database schema mirrors the main database schema but adds tracking fields:

- `is_synced` - Boolean flag to track if a record has been synced
- `client_id` - UUID for tracking local records before they get server IDs
- `server_id` - ID of the record on the server after synchronization
- `sync_status` - Status of synchronization (pending, synced, conflict)
- `last_modified` - Timestamp for conflict resolution

## Security Considerations

1. **Data Encryption**
   - In production, use SQLCipher with a strong encryption key
   - Store encryption keys securely, not in plaintext
   - Consider using a key derivation function based on user credentials

2. **Sensitive Data**
   - Limit which data is stored offline based on sensitivity
   - Implement data purging for offline data after certain time periods

3. **Authentication**
   - Implement token expiration for offline authentication
   - Require online authentication periodically

## Usage Instructions

1. **Starting in Offline Mode**
   ```
   OFFLINE_MODE=true python app.py
   ```

2. **Forcing Database Creation**
   ```
   RECREATE_DB=true OFFLINE_MODE=true python app.py
   ```

3. **Testing Synchronization**
   1. Start in offline mode and create some records
   2. Switch to online mode: `OFFLINE_MODE=false python app.py`
   3. Trigger synchronization through the UI

## Troubleshooting

1. **Database Connection Issues**
   - Verify the database file exists and is not corrupted
   - Check if SQLCipher is properly installed
   - Ensure encryption keys are correct

2. **Synchronization Failures**
   - Check network connectivity
   - Verify API endpoints are working
   - Look for sync error logs

3. **UI Not Reflecting Status**
   - Clear browser cache
   - Restart the application
   - Check for JavaScript errors in the console

## Next Steps for Enhancement

1. **Offline Attachment Handling**
   - Implement storage and sync of file attachments
   - Add compression for offline storage

2. **Progressive Web App Features**
   - Add service workers for true offline capability
   - Implement background sync

3. **Multi-device Sync**
   - Add device identifiers for tracking changes across devices
   - Enhance conflict resolution for multi-device setups
