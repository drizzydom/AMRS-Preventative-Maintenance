# AMRS Preventative Maintenance System

A comprehensive maintenance tracking and scheduling application for AMRS machines and equipment. This system helps maintenance teams track service schedules for machinery, generates alerts for overdue maintenance, and maintains a complete service history.

## 🌟 Features

- **Dashboard**: Overview of all maintenance tasks, with overdue and upcoming work
- **Site Management**: Organize equipment by location/site
- **Machine Tracking**: Track machines at each site with detailed information
- **Parts Maintenance**: Schedule and record maintenance for individual machine parts
- **Notification System**: Email alerts for upcoming and overdue maintenance
- **User Management**: Role-based permissions system with granular access control
- **Mobile-Friendly Interface**: Responsive design works on desktops, tablets, and phones
- **Backup & Restore**: Database backup functionality for data protection

## 🔗 Live Application

The application is deployed and accessible at:
https://amrs-preventative-maintenance.onrender.com

Default login:
- Username: **admin**
- Password: **admin**

⚠️ **Important**: Please change the default admin password after your first login.

## 🚀 Installation

### Web Application Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/AMRS-Preventative-Maintenance.git
   cd AMRS-Preventative-Maintenance
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install required packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a config.py file (copy from config.example.py) and configure your settings:
   ```
   cp config.example.py config.py
   # Edit config.py with your settings
   ```

5. Run the application:
   ```
   python app.py
   ```

6. Access at http://localhost:10000

### Windows Desktop Application

A Windows desktop application is available, which provides a native interface for the system:

#### Standalone App Features

- **Offline Mode**: The app works even without an internet connection, using cached data
- **Embedded Browser**: View the application in its own window without a separate browser
- **Automatic Syncing**: Changes made offline are automatically synced when online
- **Multi-Browser Technology**: Uses multiple browser technologies for the best experience

#### Building the Windows Client 

1. **Prerequisites**:
   - Python 3.8 or 3.9 (recommended for best compatibility)
   - Basic Python packages (automatically installed by the build script)

2. **Build Steps**:
   - Open Command Prompt
   - Navigate to the project directory:
     ```
     cd C:\path\to\AMRS-Preventative-Maintenance
     ```
   - Run the build script:
     ```
     python build_windows_app.py
     ```
   - The script will:
     - Install necessary dependencies
     - Create a standalone application with offline capabilities
     - Generate an executable file in the `dist` folder

3. **Running the Application**:
   - Navigate to the `dist` folder
   - Double-click `AMRSMaintenanceTracker.exe` to launch the application
   - The app will automatically connect to the server if available
   - When offline, the app will use cached data and sync when back online

#### Troubleshooting Windows Build

If you encounter issues with the build:

1. **Browser Component Issues**:
   - The app will automatically try different browser technologies
   - If all browser components fail, it will fall back to a basic mode
   - You can manually install components with:
     ```
     pip install PyQt5 PyQt5-WebEngine
     # or
     pip install cefpython3
     ```

2. **Dependency Issues**:
   - Run the batch file in the `dist` folder if the EXE doesn't work
   - The batch file will use Python's built-in modules as a fallback

3. **Direct Browser Access**:
   - As a last resort, you can always access the application directly at:
   - https://amrs-preventative-maintenance.onrender.com

## 💻 Development

### Setup Development Environment

1. Follow the installation steps above
2. Additional development dependencies:
   ```
   pip install pytest pytest-flask flake8
   ```

3. Run tests:
   ```
   pytest
   ```

### Building the Windows App

1. **Clean Installation Method (Recommended)**:
   
   To ensure a clean build without dependency issues:

   - Open Command Prompt as Administrator
   - Create a new, clean virtual environment:
     ```
     mkdir amrs_build
     cd amrs_build
     python -m venv venv
     venv\Scripts\activate
     ```
   - Install only the minimal required packages:
     ```
     pip install pyinstaller
     pip install pillow
     ```
   - Copy the build script to this directory:
     ```
     copy \path\to\AMRS-Preventative-Maintenance\build_windows_app.py .
     ```
   - Run the build script:
     ```
     python build_windows_app.py
     ```
   - Find the executable in the `dist` folder

2. **Troubleshooting Build Issues**:

   If you encounter build issues, try these solutions:

   - **Solution 1**: Install Visual C++ Build Tools
     - Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
     - Choose "Desktop Development with C++" during installation
     - Restart your command prompt and try building again

   - **Solution 2**: Use a different Python version
     - PyInstaller works best with Python 3.8 or 3.9
     - Avoid Python 3.11+ for builds if experiencing issues

   - **Solution 3**: Manual PyInstaller command
     ```
     pyinstaller --onefile --windowed --name=AMRSMaintenanceTracker amrs_launcher_main.py
     ```

3. **Direct Executable Download**:

   For immediate use without building, download the pre-built executable from:
   [Releases Page](https://github.com/yourusername/AMRS-Preventative-Maintenance/releases)

## 📊 Deployment

### Deploying to Render

1. Fork this repository
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Use these settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn wsgi:app`
   - Add the environment variables specified in render.yaml

## 🏗️ Architecture

- **Flask**: Web framework
- **SQLAlchemy**: Database ORM
- **Flask-Login**: Authentication
- **Bootstrap**: Frontend framework
- **SQLite**: Database (persistent storage on Render)

## 📋 Data Model

- **Sites**: Physical locations where equipment is housed
- **Machines**: Individual pieces of equipment at sites
- **Parts**: Components of machines that require maintenance
- **Users**: System users with different access levels
- **Roles**: User role categories with specific permissions
- **Maintenance Records**: History of maintenance activities

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

[MIT License](LICENSE)

## 📬 Contact

Project Link: [https://github.com/yourusername/AMRS-Preventative-Maintenance](https://github.com/yourusername/AMRS-Preventative-Maintenance)
