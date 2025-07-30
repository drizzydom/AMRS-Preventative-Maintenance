# AMRS Preventative Maintenance: Secure Bootstrap Token Installer Strategy

## Objective
Enable a seamless, secure, one-click installer for the offline/Electron client that:
- Includes the `BOOTSTRAP_SECRET_TOKEN` in the installer (not in source code or repo)
- On first run, stores the token in the OS keyring
- Allows the app to use the token from keyring to bootstrap and synchronize the rest of the secrets
- Keeps the user experience simple (no manual entry)

## Key Security Principles
- **Never commit the bootstrap token to source control.**
- **Inject the token at build/package time only.**
- **Store the token in the OS keyring on first run.**
- **App always reads the token from keyring.**

## Implementation Steps

### 1. Build/Packaging (on secure build machine)
- Use your packaging tool (e.g., PyInstaller, Inno Setup, NSIS) to include the token as an encrypted resource, data file, or environment variable.
- Example: For PyInstaller, add a data file or use a build-time environment variable.

### 2. Post-Install Script (runs on first launch)
- A Python script (e.g., `set_bootstrap_token.py`) is run by the installer or on first app launch.
- This script:
    - Extracts the token from the resource/file/env var
    - Stores it in keyring using `keyring.set_password('amrs', 'BOOTSTRAP_SECRET_TOKEN', token)`
    - Optionally deletes the token file/resource after use

### 3. App Logic
- On startup, the app reads the token from keyring
- If not present, shows an error (should not happen in normal install)
- Uses the token to bootstrap and synchronize other secrets

## Example: set_bootstrap_token.py

```python
import keyring
import os

def main():
    # Replace this with secure extraction from installer resource or env var
    token = os.environ.get('BOOTSTRAP_SECRET_TOKEN')
    if not token:
        print('Bootstrap token not found!')
        return
    keyring.set_password('amrs', 'BOOTSTRAP_SECRET_TOKEN', token)
    print('Bootstrap token stored in keyring.')

if __name__ == '__main__':
    main()
```

## Security Notes
- Anyone with access to the .exe can theoretically extract the token, but this is standard for desktop apps that must bootstrap secrets.
- For higher security, rotate the token periodically and monitor its use on the server.

## Summary
- The installer should inject the bootstrap token at build time, not in source.
- The token is stored in keyring on first run.
- The app uses the token from keyring to securely bootstrap all other secrets.
- User experience remains one-click and seamless.

---

**If you are picking up this project on a new machine, share this file with Copilot Chat and ask for implementation help.**
