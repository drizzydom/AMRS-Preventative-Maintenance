"""
Simple launcher script for AMRS Preventative Maintenance System.
This script opens the AMRS Maintenance app in your default web browser.

Just run: python connect_to_amrs.py
"""
import webbrowser
import time
import urllib.request
import urllib.error
import sys

# Configuration
APP_NAME = "AMRS Maintenance Tracker"
SERVER_URL = "https://amrs-preventative-maintenance.onrender.com"

def main():
    print("=" * 60)
    print(f"  {APP_NAME}")
    print("=" * 60)
    print(f"This application will connect to: {SERVER_URL}")
    print()
    
    # Check server connectivity
    print("Checking server connection...")
    try:
        with urllib.request.urlopen(f"{SERVER_URL}/health") as response:
            if response.status == 200:
                print("✅ Server is online!")
            else:
                print(f"⚠️ Server returned status code: {response.status}")
    except urllib.error.URLError:
        print("⚠️ Warning: Could not connect to server. It may be offline.")
    
    # Ask for confirmation before opening
    print()
    print("Ready to open the application in your default web browser.")
    response = input("Continue? (Y/n): ").strip().lower()
    
    if not response or response.startswith('y'):
        # Open in browser
        print("Opening application in your web browser...")
        webbrowser.open(SERVER_URL)
        
        print("✅ Application launched successfully!")
        print()
        print("You can close this window when you're done using the application.")
    else:
        print("Operation canceled.")
    
    if len(sys.argv) <= 1:  # If run directly (not imported)
        input("Press Enter to close...")

if __name__ == "__main__":
    main()
