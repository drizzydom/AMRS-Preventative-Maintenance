# AMRS Preventative Maintenance - Browser Testing for Offline Mode

This document provides instructions for testing the offline mode functionality of the AMRS Preventative Maintenance application in a web browser.

## Quick Start

To test the offline mode in a web browser:

```bash
# Start the test server on port 8080 (default)
./test_offline_browser.sh

# Or specify a custom port
./test_offline_browser.sh 9090
```

Then open your browser and navigate to `http://localhost:8080` (or your custom port).

## Testing Steps

1. **Login**:
   - Use the default credentials:
     - Username: `admin`
     - Password: `admin`

2. **Observe Offline Indicators**:
   - Notice the "Offline Mode" indicator in the top navigation bar
   - Check the offline banner below the header with sync status

3. **Test Data Operations**:
   - Navigate to different sections (Machines, Parts, Maintenance)
   - Create new records or modify existing ones
   - Verify that changes are saved to the local database

4. **Test Sync Functionality**:
   - Click the "Sync" button in the offline banner
   - Observe the simulated sync process
   - Verify the last sync time updates correctly

## Advanced Testing

### Use the Full Test Demo

For a more comprehensive test including automatic browser launch:

```bash
python full_offline_test_demo.py
```

### Test with Different Database Files

To use a specific database file:

```bash
DB_FILE=custom_test.db ./test_offline_browser.sh
```

### Force Database Recreation

If you encounter database issues:

```bash
RECREATE_DB=true ./test_offline_browser.sh
```

## Troubleshooting

- **Port Conflicts**: If the port is already in use, try a different port number
- **Database Errors**: Use the `RECREATE_DB=true` flag to start with a fresh database
- **JavaScript Issues**: Check the browser console for any errors
- **Login Problems**: Run the debugging script to check and fix database issues:
  ```bash
  python debug_offline_browser.py
  ```

## What to Look For

A successful implementation should:

1. Clearly indicate offline status to the user
2. Store all changes locally without requiring server connectivity
3. Provide a way to synchronize data when connection is restored
4. Handle errors gracefully when offline

See `TESTING_OFFLINE_MODE.md` for more detailed testing instructions.
