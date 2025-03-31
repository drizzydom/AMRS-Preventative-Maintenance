FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install required packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/instance

# Copy only necessary files (avoid copying problematic modules)
COPY entrypoint.sh .
RUN chmod +x /app/entrypoint.sh

# Set environment variables
ENV PORT=9000
ENV DATABASE_URL=sqlite:///instance/app.db
ENV DEBUG=False
ENV SECRET_KEY=default_dev_key_change_in_production
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 9000

# Run entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]