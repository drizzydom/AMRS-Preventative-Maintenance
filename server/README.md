# AMRS Preventative Maintenance Server

The server component of the AMRS Preventative Maintenance System, providing API endpoints for client applications and database management.

## Features

- **REST API**: Comprehensive API for client applications
- **Authentication**: Secure JWT-based authentication system
- **Database Management**: Efficient data storage and retrieval
- **Business Logic**: Core maintenance scheduling and tracking logic
- **Health Endpoint**: API health monitoring for clients
- **Multi-client Support**: Supports web, desktop, and mobile clients

## Installation

### Docker Installation (Recommended)

The easiest way to deploy the server is using Docker:

```bash
docker-compose up -d
```

This will start the server on port 9000 by default.

### Manual Installation

1. Ensure Python 3.8+ is installed
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure the database:
   ```bash
   python manage.py migrate
   ```

5. Create an admin user:
   ```bash
   python manage.py createsuperuser
   ```

6. Start the server:
   ```bash
   python manage.py runserver 0.0.0.0:9000
   ```

## API Endpoints

The server provides the following key API endpoints:

- `/api/login` - User authentication
- `/api/dashboard` - Dashboard summary data
- `/api/sites` - Site management
- `/api/machines` - Machine management
- `/api/parts` - Part management
- `/api/maintenance/record` - Record maintenance activities
- `/api/health` - Server health check

See the API documentation for complete details.

## Configuration

Configuration options can be set through environment variables or the `.env` file:

- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Secret key for JWT token generation
- `DEBUG`: Enable/disable debug mode (True/False)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts

## Database Backup

To back up the database:

```bash
python manage.py dumpdata > backup.json
```

To restore from backup:

```bash
python manage.py loaddata backup.json
```

## Monitoring

The server includes endpoints for monitoring its health:

- `/api/health` - Basic health check
- `/api/health/detailed` - Detailed system information (admin only)

## Security Considerations

- Keep the `SECRET_KEY` private
- Use HTTPS in production
- Regularly update dependencies
- Implement proper firewall rules

## Development

For development work:

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Run tests:
   ```bash
   python manage.py test
   ```

3. Start development server:
   ```bash
   python manage.py runserver
   ```
