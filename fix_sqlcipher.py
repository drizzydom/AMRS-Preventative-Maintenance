#!/usr/bin/env python3
"""
Helper script to fix SQLCipher installation issues

This script will add a DISABLE_SQLCIPHER environment variable
to prevent errors related to SQLCipher dependency installation.
"""
import os
import sys
import subprocess

# First try to run pip install pysqlcipher3 with --no-deps
try:
    print("Attempting to install pysqlcipher3 with --no-deps...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pysqlcipher3", "--no-deps"])
    print("Installation succeeded, but SQLCipher functionality may be limited.")
except subprocess.CalledProcessError:
    print("Installation failed, continuing without SQLCipher support.")

# Create environment variables file that will disable SQLCipher
env_file = None
if os.name == 'nt':  # Windows
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    with open(env_file, 'a') as f:
        f.write("\nDISABLE_SQLCIPHER=true\n")
    print(f"Added DISABLE_SQLCIPHER=true to {env_file}")
else:  # Linux/macOS
    # Check if .zshrc exists
    zshrc_path = os.path.expanduser('~/.zshrc')
    bashrc_path = os.path.expanduser('~/.bashrc')
    
    if os.path.exists(zshrc_path):
        env_file = zshrc_path
    elif os.path.exists(bashrc_path):
        env_file = bashrc_path
    else:
        env_file = os.path.expanduser('~/.bash_profile')
    
    # Add environment variable to the shell configuration file
    with open(env_file, 'a') as f:
        f.write("\n# Disable SQLCipher in AMRS Maintenance app\nexport DISABLE_SQLCIPHER=true\n")
    
    print(f"Added DISABLE_SQLCIPHER=true to {env_file}")
    print("Please restart your terminal or run 'source ~/.zshrc' (or equivalent) to apply the changes.")

print("\nSQLCipher has been disabled for the application.")
print("The application will use standard SQLite without encryption.")
print("You can remove this setting later if you install SQLCipher correctly.")
