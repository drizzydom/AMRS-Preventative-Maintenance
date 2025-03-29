# AMRS Preventative Maintenance System

A comprehensive solution for tracking, scheduling, and managing preventative maintenance tasks for industrial equipment and machinery.

## Overview

The AMRS Preventative Maintenance System provides organizations with a robust platform for ensuring all maintenance tasks are performed on schedule, reducing equipment downtime and extending asset lifespan. The system supports both online and offline operations, making it suitable for environments with limited connectivity.

## Key Features

- **Maintenance Scheduling**: Schedule and track regular maintenance tasks by machine, part, or site
- **Status Monitoring**: Dashboard with visual indicators showing overdue, upcoming, and completed maintenance tasks
- **Multi-Platform Support**: Server application with web, desktop, and mobile clients
- **Offline Capability**: Windows client with full offline support and automatic data synchronization
- **Credential Management**: Secure storage of user credentials for seamless authentication
- **Site and Machine Organization**: Hierarchical organization of maintenance assets
- **Maintenance History**: Complete historical records of all maintenance activities

## System Architecture

The AMRS Preventative Maintenance System consists of:

1. **Server Application**: Central API server for data storage, authentication, and business logic
2. **Web Client**: Browser-based interface for administrators and office-based users
3. **Windows Client**: Desktop application for technicians, with offline support
4. **Mobile Client**: Smartphone application for on-the-go maintenance recording (coming soon)

## Installation Options

### Server Installation

The server application can be deployed using Docker for easy setup:

```bash
docker-compose up -d
```

Or installed directly on a server with:

```bash
cd server
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:9000
```

### Windows Client Installation

The Windows client can be used in two ways:

1. **Portable Application**: Simply download and run the executable without installation
2. **Standard Installation**: Run the installer for full system integration

See the [Windows Client README](windows_client/README.md) for detailed instructions.

## Usage

1. **Login**: Access the system using your provided credentials
2. **Dashboard**: View overall maintenance status and statistics
3. **Maintenance Tasks**: Browse and filter maintenance tasks by status, machine, or site
4. **Record Maintenance**: Document completed maintenance with notes and timestamps
5. **Reports**: Generate maintenance reports for compliance and planning (admin only)

## Development Setup

To set up a development environment:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/AMRS-Preventative-Maintenance.git
   cd AMRS-Preventative-Maintenance
   ```

2. Set up the server:
   ```bash
   cd server
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver
   ```

3. Set up the client (see client-specific README files for details)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
