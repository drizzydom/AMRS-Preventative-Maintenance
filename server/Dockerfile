FROM python:3.9-slim

WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    net-tools \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories and set permissions properly at build time
RUN mkdir -p /app/data /app/templates /app/static/css /app/static/js && \
    chmod -R 777 /app/data && \
    touch /app/data/.placeholder && \
    chmod 666 /app/data/.placeholder

# Copy application code
COPY . .

# Set permissions correctly during build time
RUN chmod -R 755 /app/templates /app/static && \
    find /app/templates -type f -exec chmod 644 {} \; && \
    find /app/static -type f -exec chmod 644 {} \;

# Make entrypoint executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    PORT=9000 \
    HOST=0.0.0.0 \
    DATABASE_PATH=/app/data/app.db \
    DEBUG=False

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:$PORT/api/health || exit 1

# Expose port
EXPOSE 9000

ENTRYPOINT ["/app/entrypoint.sh"]