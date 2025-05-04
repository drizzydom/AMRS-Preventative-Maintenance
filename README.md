# AMRS Preventative Maintenance System

A full-featured, cross-platform Preventative Maintenance Tracker for Accurate Machine Repair Services (AMRS). This application helps organizations manage, schedule, and track maintenance tasks for machines and sites, with robust notification, reporting, and user management features.

## Features

- **Multi-site, multi-user support** with role-based access control (admin, manager, technician, etc.)
- **Machine and site management**: Add, edit, and track machines, sites, and maintenance tasks.
- **Automated email notifications** for overdue, due soon, and completed maintenance tasks.
- **Customizable notification preferences** per user and per site.
- **Audit history tracking** and reporting.
- **Import/export** via Excel templates.
- **Emergency maintenance request system**.
- **Secure authentication** and encrypted sensitive fields.
- **Responsive web UI** and standalone desktop app (Electron + Flask).
- **Cloud hosting** (Render.com) and local deployment support.
- **Comprehensive test suite**.

## Architecture

- **Backend**: Python (Flask), SQLAlchemy ORM, PostgreSQL (Render) or SQLite (local/desktop).
- **Frontend**: Jinja2 templates, Bootstrap, custom JS.
- **Email**: Flask-Mail, SMTP (configurable).
- **Desktop App**: Electron (Node.js) + Flask backend.
- **Hosting**: [Render.com](https://render.com/) for production web deployment.
- **CI/CD**: GitHub Actions for automated builds and releases.

## Directory Structure

```
.
├── app.py                  # Main Flask application
├── config.py               # Configuration (uses environment variables)
├── db_config.py            # Database configuration logic
├── notification_scheduler.py # Automated notification logic
├── templates/              # Jinja2 HTML templates
├── static/                 # Static files (JS, CSS, images)
├── requirements.txt        # Python dependencies
├── requirements-windows.txt# Windows-specific dependencies
├── requirements-render.txt # Render.com-specific dependencies
├── setup_env.py            # Environment setup script
├── setup_electron_env.py   # Electron/desktop setup script
├── Dockerfile              # For containerized deployment
├── server/                 # Render.com deployment files
├── tests/                  # Test suite (pytest)
└── ... (see workspace for full list)
```

## Hosting & Deployment

### Render.com (Production)

- **Database**: PostgreSQL (managed by Render)
- **App**: Flask app served via Gunicorn, auto-deployed from GitHub
- **Environment variables**: All secrets and config (see below)
- **Backups**: Automated by Render for PostgreSQL

### Local/Standalone

- **Database**: SQLite (default) or PostgreSQL (if configured)
- **App**: Flask development server or Electron desktop app
- **Environment variables**: Loaded from `.env` file

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/accuratemachinerepair/AMRS-Preventative-Maintenance.git
cd AMRS-Preventative-Maintenance
```

### 2. Set Up Environment Variables

Copy `.env.example` to `.env` and fill in your secrets and configuration:

```bash
cp .env.example .env
```

Edit `.env` with your preferred editor. At minimum, set:

- `SECRET_KEY`
- `DATABASE_URL` (for PostgreSQL, e.g. on Render)
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`
- `EMERGENCY_CONTACT_EMAIL` (optional)

**Never commit your `.env` file to version control!**

### 3. Install Python Dependencies

#### Local/Development

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Windows

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements-windows.txt
```

#### Render.com

Dependencies are installed automatically from `requirements.txt` or `requirements-render.txt`.

### 4. Initialize the Database

#### Local/Development

```bash
python init_database.py
```

#### Render.com

Database tables are created automatically on first run if not present.

### 5. Run the Application

#### Local/Development

```bash
python app.py
```

Visit [http://localhost:10000](http://localhost:10000) (or the port you set).

#### Desktop App

```bash
python setup_electron_env.py
npm install
npm run electron
```

#### Render.com

- App is auto-deployed and served at your Render-provided URL.

---

## Self-Hosting and Running Locally

You can run AMRS Preventative Maintenance on your own infrastructure or workstation. Here’s how:

### Local Development (macOS/Linux/Windows)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/accuratemachinerepair/AMRS-Preventative-Maintenance.git
   cd AMRS-Preventative-Maintenance
   ```
2. **Set up a Python virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Copy and configure your environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your preferred editor and set your secrets/configuration
   ```
5. **Initialize the database:**
   ```bash
   python init_database.py
   ```
6. **Run the application:**
   ```bash
   python app.py
   ```
   The app will be available at http://localhost:10000 by default.

### Customizing for Your Organization
- **Branding:** Replace the logo in `static/img/logo.png` and update company info in templates as needed.
- **Email:** Set up your SMTP credentials in `.env` for notifications.
- **Database:** Use SQLite for simple setups or set `DATABASE_URL` for PostgreSQL.
- **User Roles:** Use the admin UI to manage users and permissions.
- **Notification Preferences:** Each user can set their own in their profile.

### Deploying to a Server (Linux/Cloud VPS)
1. Follow the local steps above.
2. Use a production WSGI server (e.g., Gunicorn) and a reverse proxy (e.g., Nginx) for deployment.
3. Set up a process manager (e.g., systemd or supervisor) to keep the app running.
4. Secure your server (firewall, HTTPS, etc.).

### Deploying on Render.com
- Push your repository to GitHub.
- Create a new Web Service on Render, connect your repo, and set the build/start commands:
  - **Build Command:** `pip install -r requirements.txt`
  - **Start Command:** `gunicorn app:app`
- Add your environment variables in the Render dashboard.
- Attach a PostgreSQL database (Render provides this as a managed service).
- The app will auto-deploy and be available at your Render URL.

### Desktop App (Electron)
- Run `python setup_electron_env.py` to prepare the backend.
- Run `npm install` and `npm run electron` to launch the desktop app.
- The desktop app bundles the Flask backend and runs locally.

### Updating
- Pull the latest changes from GitHub:
  ```bash
  git pull origin main
  pip install -r requirements.txt
  # Restart your app as needed
  ```

### Backups
- For SQLite: Back up the `instance/` directory.
- For PostgreSQL: Use your cloud provider’s backup tools (Render does this automatically).

### Support
For help, contact [sales@accuratemachinerepair.com](mailto:sales@accuratemachinerepair.com).

---

## Customization

- **Configuration**: All settings are controlled via environment variables or `.env`.
- **Email**: Use your SMTP provider (Gmail, IONOS, etc.) and set credentials in `.env`.
- **Database**: Use SQLite for local/dev, PostgreSQL for production (set `DATABASE_URL`).
- **User Roles**: Manage via the admin UI.
- **Notification Preferences**: Each user can set their own in their profile.

---

## Running Tests

```bash
pytest
```

---

## Troubleshooting

- **Email not sending**: Check SMTP settings in `.env` and use `python test_email_cli.py recipient@example.com` to test.
- **Database issues**: Ensure `DATABASE_URL` is set and accessible.
- **Render.com**: Check Render dashboard logs for errors.
- **Desktop app**: Ensure both Python and Node.js dependencies are installed.

---

## Security

- **Never commit secrets**: `.env` is in `.gitignore`.
- **Production**: Always set a strong `SECRET_KEY` and `USER_FIELD_ENCRYPTION_KEY`.
- **Backups**: Render.com provides daily PostgreSQL backups.

---

## License

See [LICENSE](LICENSE).

---

## Support

For questions or support, file an Issue on the repository.

---

**This README is up to date as of May 2025.**
