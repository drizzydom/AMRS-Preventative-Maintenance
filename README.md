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

1. Download the latest release from the Releases page
2. Run the installer
3. Launch the AMRS Maintenance Tracker application
4. The application will automatically connect to the production server at https://amrs-preventative-maintenance.onrender.com

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

1. **Prerequisites**:
   - Install [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
     - During installation, select "Desktop development with C++
     - This is required to build NumPy and other dependencies
   - Ensure you have Python 3.8-3.10 installed (3.11+ may have compatibility issues with some dependencies)

2. Install requirements:
   ```
   pip install -r requirements.txt
   ```

3. Run the build script:
   ```
   python build_windows_app.py
   ```

4. The executable will be created in the `dist` folder

#### Alternative: Use Pre-built Release

If you encounter build issues, you can download the pre-built Windows application from the [Releases](https://github.com/yourusername/AMRS-Preventative-Maintenance/releases) page.

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
