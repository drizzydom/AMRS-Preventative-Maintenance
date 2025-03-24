# Maintenance Tracking System

A simple web-based system for tracking maintenance schedules for equipment at different sites.

## Features

- User authentication with admin privileges
- Track sites, machines, and parts
- Maintenance scheduling and tracking
- Admin panel for managing entities
- Dashboard view with maintenance status indicators

## Setup Instructions

### Prerequisites

- Python 3.9, 3.10, or 3.11 installed
  - **Note:** Python 3.13 is not currently compatible with some of the dependencies
  - For macOS: `brew install python@3.11` 
  - For Windows: Download from [python.org](https://www.python.org/downloads/)
- pip package manager (included with Python)

### Easy Setup

1. Clone this repository:
```
git clone https://github.com/yourusername/maintenance-tracker.git
cd maintenance-tracker
```

2. Run the setup script:

**For macOS/Linux:**
```
chmod +x setup.sh
./setup.sh
```

**For Windows:**
```
setup.bat
```

3. Run the application:
```
# Activate virtual environment if not already active
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the application
python app.py
```

4. Open your browser and navigate to:
```
http://localhost:8000
```

### Manual Setup

If the setup script doesn't work for your environment, you can manually set up:

1. Create and activate a virtual environment:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install required packages:
```
pip install -r requirements.txt
```

3. Initialize the database and run the application:
```
flask --app app init-db
python app.py
```

### Default Login

- Username: admin
- Password: admin

## Usage

1. After logging in, you'll see the dashboard with all sites, machines and parts
2. Use the admin panel to add/remove sites, machines, and parts
3. Parts with upcoming maintenance will be highlighted on the dashboard
4. Use the "Update Maintenance" button on the Admin Parts page to record completed maintenance

## Troubleshooting

- **Python version compatibility:** This application works best with Python 3.9-3.11
- **SQLAlchemy errors:** If you see SQLAlchemy errors, they're likely due to Python version incompatibility
- **Database schema errors:** If you see "no such column" errors after updating the code, reset the database:
  ```
  ./reset_db.sh
  ```
  Or manually:
  ```
  rm instance/maintenance.db
  flask --app app init-db
  ```
- **Database errors:** If the database doesn't initialize properly, delete the `instance` folder and try again
- **Virtual environment issues:** Make sure to activate the virtual environment before running any commands

## Email Notifications

The system can send automatic email notifications when maintenance is due or overdue.

### Setting Up Email

1. Configure your email server settings by setting environment variables:
```
