# AMRS Preventative Maintenance System

A comprehensive system for tracking and managing preventative maintenance tasks for AMRS equipment.

## Components

- **Server**: Flask-based API and web interface
- **Windows Client**: Desktop application for technicians
- **Docker Deployment**: Containerized setup for easy deployment

## Quick Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/AMRS-Preventative-Maintenance.git
cd AMRS-Preventative-Maintenance

# Run the master setup script
chmod +x master_setup.sh
./master_setup.sh
```

## Troubleshooting Common Issues

### 404 Not Found Error

If you experience 404 errors after setup:

1. Run the Nginx fix script:
   ```bash
   chmod +x fix_nginx_routes.sh
   ./fix_nginx_routes.sh
   ```

2. Test route access:
   ```bash
   chmod +x test_route_access.sh
   ./test_route_access.sh
   ```

### 500 Internal Server Error

If you encounter 500 Internal Server errors:

1. Run the all-in-one fix script:
   ```bash
   chmod +x fix_500_error.sh
   ./fix_500_error.sh
   ```

2. If database issues persist:
   ```bash
   chmod +x db_fix.sh
   ./db_fix.sh
   ```

3. For complex issues, run the diagnostics:
   ```bash
   chmod +x diagnose_500_error.sh
   ./diagnose_500_error.sh
   ```

### Docker Issues

For Docker-related problems:

1. Clean up Docker resources:
   ```bash
   chmod +x docker_cleanup.sh
   ./docker_cleanup.sh
   ```

2. Restart containers:
   ```bash
   chmod +x restart_containers.sh
   ./restart_containers.sh
   ```

## Advanced Configuration

For HTTPS, DDNS, and other advanced configurations, see the documentation in the [`docs`](./docs) directory.
