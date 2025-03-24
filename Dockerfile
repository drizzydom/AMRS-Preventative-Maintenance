FROM python:3.11-slim

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy application code
COPY . .

# Create volume mount points
VOLUME ["/app/instance", "/app/backups"]

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5000

# Run with gunicorn for production with proper bind to 0.0.0.0
# Get number of workers from environment or default to 2
CMD gunicorn --bind 0.0.0.0:5000 \
    --workers ${GUNICORN_WORKERS:-2} \
    --threads ${GUNICORN_THREADS:-2} \
    --timeout ${GUNICORN_TIMEOUT:-120} \
    --keepalive ${GUNICORN_KEEPALIVE:-5} \
    --log-level info \
    app:app
