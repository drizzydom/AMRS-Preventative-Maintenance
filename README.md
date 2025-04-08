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

#### Features

- **Standalone Window Mode**: View the application in a dedicated window
- **Auto-start Option**: Configure the application to launch on Windows startup
- **Offline Capability**: Connect to the server even when offline
- **Native Integration**: Integrates with Windows for a seamless experience

#### Building the Windows Client 

1. **Prerequisites**:
   - Python 3.8 or 3.9 (recommended for best compatibility)
   - Microsoft Visual C++ Build Tools 2019 or later
   - Admin privileges (required for startup feature)

2. **Build Steps**:
   - Open Command Prompt as Administrator
   - Navigate to the project directory:
     ```
     cd C:\path\to\AMRS-Preventative-Maintenance
     ```
   - Create a virtual environment:
     ```
     python -m venv venv
     venv\Scripts\activate
     ```
   - Install required dependencies:
     ```
     pip install -r requirements.txt
     ```
   - Run the build script:
     ```
     python build_windows_app.py
     ```
   - The executable will be created in the `dist` folder

3. **Running the Application**:
   - Navigate to the `dist` folder
   - Double-click `AMRSMaintenanceTracker.exe`
   - The application will open in its own window and connect to the server
   - You can configure it to start with Windows through the Tools menu

#### Troubleshooting Windows Build

If you encounter encoding errors during the build process:

1. **Fix for Unicode/Encoding Errors**:
   - Open Command Prompt and run:
     ```
     chcp 65001
     ```
   - This switches the Command Prompt to UTF-8 encoding
   - Then run the build script again

2. **Fix for Missing Dependencies**:
   - If PyInstaller fails with missing dependencies, run:
     ```
     pip install pywin32 tkinter
     ```

3. **Use the Batch File Alternative**:
   - If the EXE file doesn't build properly, use the batch file:
   - Run `AMRS_Launcher.bat` from the `dist` folder

#### Building the Windows Client (Simplified Method)

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
   - The script will create:
     - A standalone executable (if PyInstaller works correctly)
     - A batch file launcher (as fallback)
   - Both can be found in the `dist` folder

3. **Running the Application**:
   - Navigate to the `dist` folder
   - Double-click either:
     - `AMRSMaintenanceTracker.exe` (if PyInstaller worked successfully)
     - `AMRS_Launcher.bat` (if PyInstaller failed)

#### Troubleshooting

If you encounter issues with the build:

1. **Dependency Issues**:
   - The fallback batch launcher requires only Python and standard libraries
   - Make sure Python is added to your PATH environment variable

2. **Manual Setup**:
   - If the build script fails completely, run these commands:
     ```
     pip install tkinter
     python amrs_connect.py
     ```

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
