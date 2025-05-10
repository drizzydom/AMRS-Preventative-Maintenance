# Offline Token Authentication System

This document explains how to test and use the offline token authentication system for the AMRS Preventative Maintenance application.

## Overview

The offline token authentication system allows users to log in once while online and continue using the application offline. It uses JWT (JSON Web Tokens) for secure authentication with configurable expiry times.

## Features

- **Configurable Token Expiry**: Set token validity from 1 day to 1 year (default: 30 days)
- **Automatic Token Refresh**: Tokens are automatically refreshed before they expire
- **Token Persistence**: Tokens are stored securely for offline use
- **Enhanced Security**: Protects against token tampering and replay attacks
- **Flexible Configuration**: Use environment variables to customize behavior

## Quick Start

1. Run the offline token authentication test:

```powershell
python run_offline_token_test.py --expiry 30 --port 5000 --debug
```

2. Run the complete end-to-end test:

```powershell
python test_offline_auth.py e2e --username admin --password admin
```

## Configuration Options

### Environment Variables

Set these environment variables to customize token behavior:

- `TOKEN_EXPIRY_DAYS`: Number of days before tokens expire (default: 30)
- `USE_ENHANCED_TOKEN_MANAGER`: Use the enhanced token manager with additional features (default: true)
- `JWT_SECRET_KEY`: Secret key for token signing (default: secure_offline_jwt_secret_key_for_testing)
- `TOKEN_REFRESH_THRESHOLD_DAYS`: Days before expiry to trigger auto-refresh (default: 5)
- `ENCRYPT_TOKEN_STORAGE`: Encrypt token storage files (default: false)

### Command Line Options

When using `run_offline_token_test.py`:

- `--expiry DAYS`: Set token expiry in days
- `--port PORT`: Set the port for the offline app
- `--debug`: Run in debug mode
- `--enhanced`: Use the enhanced token manager
- `--no-browser`: Do not automatically open browser
- `--recreate-db`: Recreate the database

## Testing Commands

### Basic Token Tests

Generate a test token:

```powershell
python test_token_auth.py generate --username admin --expiry 30
```

Validate a token:

```powershell
python test_token_auth.py validate --token "your_token_here"
```

List all stored tokens:

```powershell
python test_token_auth.py list
```

### Advanced Testing

Run end-to-end offline authentication test:

```powershell
python test_offline_auth.py e2e --username admin --password admin
```

Test token API endpoints:

```powershell
python test_offline_auth.py api --app-url http://localhost:5000
```

Test token security:

```powershell
python test_offline_auth.py security --username admin
```

Test token expiry (quick test with short expiry):

```powershell
python test_offline_auth.py expiry --seconds 10
```

Test enhanced token manager features:

```powershell
python test_offline_auth.py enhanced --username admin
```

## Manual Testing Process

1. Start the offline app with token authentication:

```powershell
python run_offline_token_test.py --debug
```

2. Open a browser and navigate to http://localhost:5000

3. Log in with username "admin" and password "admin"

4. The app will generate and store a token

5. Close the browser and reopen it, navigate to http://localhost:5000

6. You should be automatically logged in using the stored token

7. To verify token details, run:

```powershell
python test_token_auth.py list
```

## Token Authentication Flow

1. **Initial Online Login**:
   - User logs in with username/password
   - System authenticates credentials
   - System generates a JWT token with configurable expiry
   - Token is stored securely on the client device

2. **Subsequent Offline Logins**:
   - System checks for existing valid token
   - If token is valid, user is automatically logged in
   - If token is approaching expiry, it's automatically refreshed
   - If token is expired, user must log in online again

3. **Token Validation Process**:
   - Token signature is verified
   - Token expiry is checked
   - Token contents are validated

## Implementation Details

The system consists of several components:

1. **TokenManager**: Basic token management functionality
2. **EnhancedTokenManager**: Advanced features like auto-refresh and encrypted storage
3. **API Endpoints**: For token validation and refresh
4. **Integration with Flask-Login**: For seamless authentication

## Troubleshooting

### Common Issues

1. **Token Not Being Stored**:
   - Check file permissions in the `instance/tokens` directory
   - Verify the token manager is properly initialized

2. **Token Expiring Too Quickly**:
   - Check `TOKEN_EXPIRY_DAYS` setting
   - Verify system clock is accurate

3. **Automatic Refresh Not Working**:
   - Ensure `USE_ENHANCED_TOKEN_MANAGER` is set to true
   - Check `TOKEN_REFRESH_THRESHOLD_DAYS` setting

4. **Test Scripts Failing**:
   - Make sure all dependencies are installed: `pip install PyJWT flask`
   - Verify the database has default users created

## Security Considerations

- The token secret key should be kept secure in a production environment
- Consider enabling encrypted token storage for production use
- Tokens should have a reasonable expiry time based on security requirements

## Extending the System

To add additional data to tokens:

1. Modify the `generate_token` function call in `offline_app.py`
2. Add the data to the `additional_data` dictionary
3. Access the data from the token payload after validation
