"""
This is a simple adapter file for Render.com deployments.
Since Render insists on running 'gunicorn app:app', this file
redirects to the actual application in wsgi.py.
"""
import os
import sys

print("Render adapter: Importing app from wsgi.py")

# Import the app from wsgi.py
from wsgi import app

# Log information for debugging
if __name__ == "__main__":
    print(f"Running with Python {sys.version}")
    print(f"App imported from: {app.__module__}")
