"""
Simple script to connect to the AMRS Preventative Maintenance web application.
This script does not require compilation and can be run directly with Python.
"""

import webbrowser
import tkinter as tk
from tkinter import ttk
import json
import os

# Configuration
SERVER_URL = "https://amrs-preventative-maintenance.onrender.com"
CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.amrs-maintenance')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')

# Create config directory if it doesn't exist
os.makedirs(CONFIG_DIR, exist_ok=True)

# Load or create configuration
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"server_url": SERVER_URL, "auto_connect": True}
    else:
        # Default config
        config = {"server_url": SERVER_URL, "auto_connect": True}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return config

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

# Create the UI
root = tk.Tk()
root.title("AMRS Maintenance Connector")
root.geometry("400x200")

# Make it look nicer with a modern theme if available
try:
    style = ttk.Style()
    style.theme_use('clam')  # Use a more modern theme if available
except:
    pass  # Fall back to default theme if 'clam' not available

# Load config
config = load_config()

# Create the UI elements
frame = ttk.Frame(root, padding=20)
frame.pack(fill=tk.BOTH, expand=True)

# Title label
title_label = ttk.Label(frame, text="AMRS Maintenance Connector", font=("", 14, "bold"))
title_label.pack(pady=(0, 15))

# Server URL input
url_frame = ttk.Frame(frame)
url_frame.pack(fill=tk.X, pady=(0, 10))

url_label = ttk.Label(url_frame, text="Server URL:")
url_label.pack(side=tk.LEFT)

url_var = tk.StringVar(value=config["server_url"])
url_entry = ttk.Entry(url_frame, textvariable=url_var, width=35)
url_entry.pack(side=tk.LEFT, padx=(5, 0))

# Auto-connect checkbox
auto_connect_var = tk.BooleanVar(value=config["auto_connect"])
auto_connect = ttk.Checkbutton(frame, text="Automatically connect on startup", variable=auto_connect_var)
auto_connect.pack(anchor=tk.W, pady=(0, 10))

# Connect button
def connect():
    url = url_var.get().strip()
    config["server_url"] = url
    config["auto_connect"] = auto_connect_var.get()
    save_config(config)
    webbrowser.open(url)
    status_label.config(text=f"Opening {url} in your browser...")

connect_btn = ttk.Button(frame, text="Connect to AMRS Maintenance", command=connect)
connect_btn.pack(fill=tk.X, pady=(5, 10))

# Status label
status_label = ttk.Label(frame, text="Ready to connect")
status_label.pack()

# Auto-connect on startup if enabled
if config["auto_connect"]:
    root.after(1000, connect)

# Start the application
root.mainloop()
