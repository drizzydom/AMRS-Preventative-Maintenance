# AMRS Preventative Maintenance - Offline Mode Implementation

This README documents the offline mode implementation for the AMRS Preventative Maintenance application. It provides a comprehensive overview of all components, their relationships, and how the offline mode integrates with the main application.

## Architecture Overview

The offline mode implementation consists of several key components:

1. **Database Controller (`db_controller.py`)**: A unified controller that handles both SQLite and SQLCipher (encrypted) databases with graceful fallbacks.

2. **Offline Application (`offline_app.py`)**: A simplified version of the main application for testing offline functionality.

3. **Helper Scripts**:
   - `run_offline_app.py`: A wrapper script to run the offline app with SQLCipher disabled
   - `fix_sqlcipher.py`: A utility to fix SQLCipher installation issues

4. **JavaScript Utilities**:
   - `static/js/offline.js`: Handles offline detection, synchronization, and UI updates

5. **Templates**: Modified to include offline status indicators and sync controls

## Component Details

### Database Controller (`db_controller.py`)

This controller provides a unified interface for both encrypted (SQLCipher) and standard SQLite databases. Key features:

- Automatic fallback to standard SQLite if SQLCipher is unavailable
- Thread-safe connection management
- Standard API for database operations
- Support for user authentication and encryption
- Synchronization tracking and management

Usage:
```python
from db_controller import DatabaseController

# Standard SQLite
db = DatabaseController(use_encryption=False)

# Encrypted SQLite (requires SQLCipher)
db = DatabaseController(
    encryption_key="your-secret-key", 
    use_encryption=True
)

# Query example
users = db.fetch_all("SELECT * FROM users")
```

### Offline Application (`offline_app.py`)

A simplified Flask application for testing offline functionality. Features:

- Complete user authentication
- API endpoints for sync status and actions
- Visual indicators for offline status
- Session management

This application serves as both a testbed for offline functionality and a reference implementation for integrating offline features into the main application.

### Integration with Main Application

To integrate offline mode into the main application:

1. Import the database controller:
   ```python
   from db_controller import DatabaseController
   ```

2. Initialize it based on configuration:
   ```python
   # Check if offline mode is enabled
   offline_mode = os.environ.get('OFFLINE_MODE', 'false').lower() == 'true'
   
   # Create appropriate controller
   if offline_mode:
       db = DatabaseController(use_encryption=True, encryption_key=config.ENCRYPTION_KEY)
   else:
       # Use existing database configuration
   ```

3. Add sync endpoints to the main application (similar to offline_app.py)

4. Include offline.js for connection detection and UI updates

## Synchronization Strategy

The synchronization process works as follows:

1. **Track Changes**: All offline changes are tracked with `is_synced` flags
2. **Detect Connection**: JavaScript monitors connection status
3. **Upload Changes**: When online, pending changes are uploaded to the server
4. **Download Updates**: New server data is downloaded to the local database
5. **Conflict Resolution**: Server changes take precedence by default

## Database Schema Extensions

The following tables/columns were added to support offline mode:

1. **sync_info table**:
   - Tracks last synchronization time
   - Stores sync configuration

2. **Additional columns in data tables**:
   - `is_synced`: Boolean flag to track sync status
   - `client_id`: UUID for tracking local records
   - `last_modified`: Timestamp for conflict resolution

## How to Test Offline Mode

1. Run the offline application:
   ```bash
   python run_offline_app.py
   ```

2. Create test data in offline mode
3. Test synchronization by toggling the network connection
4. Verify data integrity after synchronization

## SQLCipher Issues and Solutions

SQLCipher may have installation issues on some platforms. If encountered:

1. Run the fix script:
   ```bash
   python fix_sqlcipher.py
   ```

2. Or set environment variable manually:
   ```bash
   DISABLE_SQLCIPHER=true python offline_app.py
   ```

3. The application will fall back to standard SQLite without encryption

## Future Enhancements

Planned enhancements for the offline mode include:

1. Better conflict resolution strategies
2. Progressive Web App (PWA) capabilities
3. Background synchronization
4. Multi-device synchronization
5. Enhanced offline security measures

## Files Modified/Created

- Created: `db_controller.py`
- Created: `offline_app.py`
- Created: `run_offline_app.py`
- Created: `fix_sqlcipher.py`
- Created: `static/js/offline.js`
- Modified: Templates to support offline mode indicators
- Created: `OFFLINE_MODE_USAGE.md` and `offline_mode_guide.md`

## References

For more detailed information, see:
- `offline_mode_guide.md`: Detailed implementation guide
- `OFFLINE_MODE_USAGE.md`: End-user instructions
