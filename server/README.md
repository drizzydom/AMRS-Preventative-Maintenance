# AMRS Preventative Maintenance Server

The server component of the AMRS Preventative Maintenance System, providing REST API endpoints for client applications and database management.

## Features

- **REST API**: For web, desktop, and mobile clients
- **Authentication**: Secure JWT-based authentication
- **Database Management**: Efficient data storage and retrieval
- **Business Logic**: Core maintenance scheduling and tracking
- **Health Endpoints**: API health monitoring
- **Multi-client Support**: Web, desktop, and mobile

## Installation

### Docker Installation (Recommended)
```bash
docker-compose up -d
```
This starts the server on port 9000 by default.

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

- `/api/login` - User authentication
- `/api/dashboard` - Dashboard summary data
- `/api/sites` - Site management
- `/api/machines` - Machine management
- `/api/parts` - Part management
- `/api/maintenance/record` - Record maintenance activities
- `/api/health` - Server health check

See the API documentation for full details.

## Configuration

Set options via environment variables or `.env` file:
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Secret key for JWT
- `DEBUG`: Enable/disable debug mode
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts

## Database Backup

To back up:
```bash
python manage.py dumpdata > backup.json
```
To restore:
```bash
python manage.py loaddata backup.json
```

## Monitoring

- `/api/health` - Basic health check
- `/api/health/detailed` - Detailed system info (admin only)

## Security Considerations

- Keep `SECRET_KEY` private
- Use HTTPS in production
- Regularly update dependencies
- Implement proper firewall rules

## Development

1. Install dev dependencies:
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

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.
