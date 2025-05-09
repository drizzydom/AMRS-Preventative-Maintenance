# AMRS Preventative Maintenance - Offline Mode Browser Testing Implementation

## Summary of Changes

We have successfully implemented the ability to run the AMRS Preventative Maintenance application on a different port for browser-based testing of the offline functionality. This implementation enables comprehensive testing of the offline mode, including UI indicators, database synchronization, and the complete offline workflow.

## Implemented Features

1. **Custom Port Configuration**
   - Created `run_offline_app_test.py` to run the app on a configurable port
   - Added command-line argument and environment variable support for port specification
   - Created `test_offline_browser.sh` as a convenient wrapper script

2. **Enhanced Database Flexibility**
   - Modified `db_controller.py` to support custom database filenames via environment variables
   - Implemented separate test database to avoid interfering with production data

3. **Improved UI Indicators**
   - Enhanced offline mode indicators in the navigation bar
   - Added connection status display that updates automatically
   - Implemented offline banner with sync functionality

4. **Sync Functionality**
   - Added API endpoints for sync status and trigger
   - Implemented JavaScript to handle sync operations
   - Created UI elements to display sync status

5. **Comprehensive Testing Tools**
   - Created `full_offline_test_demo.py` for end-to-end testing and demonstration
   - Added detailed testing documentation in `TESTING_OFFLINE_MODE.md`
   - Created a quick reference guide in `BROWSER_TESTING_GUIDE.md`

## How to Test

### Basic Testing

```bash
# Run on default port 8080
./test_offline_browser.sh

# Run on custom port
./test_offline_browser.sh 9090
```

### Full Demo Test

```bash
# Run the comprehensive test and demo
python full_offline_test_demo.py
```

### With Custom Database File

```bash
# Use a specific database file
DB_FILE=custom_test.db ./test_offline_browser.sh
```

## Testing Workflow

1. Start the offline app using one of the methods above
2. Open a web browser and navigate to http://localhost:8080 (or your custom port)
3. Log in with the default credentials (username: admin, password: admin)
4. Verify the offline indicators are visible (status in header and offline banner)
5. Create or modify data to test local storage functionality
6. Test the sync button to simulate synchronization
7. Verify changes persist after refreshing the page

## Notes for Future Development

- The current implementation simulates sync functionality for testing purposes
- For production use, the sync endpoints would need to communicate with the actual server
- Additional error handling could be implemented for network failures during sync
- User preferences could be added to configure sync frequency and notifications

## Files Modified/Created

- Modified: `db_controller.py` - Added support for custom database filenames
- Modified: `offline_app.py` - Added API endpoints for sync and improved configuration
- Modified: `templates/base.html` - Enhanced offline mode UI elements
- Created: `run_offline_app_test.py` - Script to run the app on a custom port
- Created: `test_offline_browser.sh` - Convenient shell script for browser testing
- Created: `full_offline_test_demo.py` - Comprehensive test script
- Created: `TESTING_OFFLINE_MODE.md` - Detailed testing instructions
- Created: `BROWSER_TESTING_GUIDE.md` - Quick reference for browser testing
- Updated: `OFFLINE_MODE_README.md` - Added information about browser testing
