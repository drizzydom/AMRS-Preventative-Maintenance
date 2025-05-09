# Testing Offline Mode in the AMRS Preventative Maintenance Application

This document provides instructions for testing the offline mode functionality in the AMRS Preventative Maintenance application.

## Prerequisites

1. Python 3.7 or later
2. Required Python packages (install with `pip install -r requirements.txt`)

## Starting the Test Environment

The application can be run in offline test mode using one of the following methods:

### Method 1: Using the Test Script

```bash
# Start on default port 8080
./test_offline_browser.sh

# Start on a custom port
./test_offline_browser.sh 9090
```

### Method 2: Using Python Directly

```bash
# Start on default port 8080
python run_offline_app_test.py

# Start on a custom port
python run_offline_app_test.py 9090

# Alternatively, use environment variables
TEST_PORT=7070 python run_offline_app_test.py
```

## Testing Workflow

1. **Launch the Application**: Start the offline test app using one of the methods above
2. **Access in Browser**: Open http://localhost:8080 (or your custom port) in your web browser
3. **Log in**: Use the default credentials (username: `admin`, password: `admin`)
4. **Verify Offline Indicators**: 
   - Check that the offline banner appears at the top of the page
   - Verify the "Offline Mode" indicator in the header
5. **Test Data Entry**:
   - Create or modify records in the application
   - Verify changes are saved to the local database
6. **Test Sync Functionality**:
   - Click the "Sync" button in the offline banner
   - Observe the simulated sync process
   - Verify the last sync time updates

## Troubleshooting

- **Database Issues**: If you encounter database errors, try recreating the database:
  ```bash
  RECREATE_DB=true python run_offline_app_test.py
  ```
- **Port Conflicts**: If the port is already in use, try a different port number

## Evaluating Results

The test is successful if:

1. The application runs properly in offline mode
2. Changes persist in the local database
3. The UI correctly indicates offline status
4. Sync functionality simulates properly

## Additional Notes

- The test environment uses a separate database file (`maintenance_test.db`) to avoid interfering with your main application data
- All data entered during testing is stored locally and not sent to any server
