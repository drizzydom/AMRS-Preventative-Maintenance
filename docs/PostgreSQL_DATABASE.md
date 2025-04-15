# PostgreSQL Database Management on Render

This document explains how to manage the PostgreSQL database on Render, including backup and restore operations.

## Database Configuration

The application now uses PostgreSQL as its database backend. The database URL is configured through the `DATABASE_URL` environment variable and has a fallback default value in the application code.

## Database Backups

Database backups are now managed directly through the Render platform, which offers automated backups for PostgreSQL databases.

### Viewing Backups

1. Log in to the Render dashboard
2. Navigate to your PostgreSQL service
3. Click on the "Backups" tab
4. Here you can see all available backups

### Creating a Manual Backup

1. Navigate to the "Backups" tab in your PostgreSQL service
2. Click "Create Backup"
3. Wait for the backup to complete

### Restoring a Backup

1. Navigate to the "Backups" tab in your PostgreSQL service
2. Find the backup you want to restore
3. Click "Restore"
4. Confirm the restoration
5. Wait for the process to complete

### Automated Backups

Render automatically creates daily backups of your PostgreSQL database. You can configure the retention period in the database settings.

## Local Development

For local development, you can use:

- PostgreSQL on your local machine
- A cloud-hosted PostgreSQL instance
- Docker container running PostgreSQL

Set the `DATABASE_URL` environment variable to point to your development database.

## Exporting Data

If you need to export data from your Render PostgreSQL database:

1. Log in to the Render dashboard
2. Navigate to your PostgreSQL service
3. Click on "Connect"
4. Use the provided connection details with pg_dump:

```bash
pg_dump -h HOSTNAME -U USERNAME -d DATABASE_NAME > backup.sql
```

## Importing Data

To import data to your Render PostgreSQL database:

```bash
psql -h HOSTNAME -U USERNAME -d DATABASE_NAME < backup.sql
```
