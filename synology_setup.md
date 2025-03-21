# Setting Up the Maintenance Tracker on Synology NAS

These instructions will help you run the application directly on your Synology NAS using Python.

## Prerequisites:
1. Synology NAS with DSM 7.0 or higher
2. Python 3 package installed on your NAS
3. SSH access enabled on your NAS (Control Panel > Terminal & SNMP > Terminal)

## Setup Instructions:

### 1. Install Required Packages
- Log in to your Synology DSM
- Open Package Center
- Search for and install "Python 3"
- (Optional) Install "Git Server" if you want to clone the repository directly

### 2. Transfer the Application
- Upload your application files to a folder on your NAS, e.g., `/volume1/maintenance-tracker/`
- You can use File Station to create this folder and upload files

### 3. Set Up Python Environment
- SSH into your Synology NAS (use an SSH client like PuTTY or Terminal)
- Navigate to your application directory:
  ```bash
  cd /volume1/maintenance-tracker/
  ```
- Create and activate a virtual environment:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

### 4. Initialize the Database
- Run the setup script:
  ```bash
  python -m flask add-reset-columns
  python -m flask init-db
  