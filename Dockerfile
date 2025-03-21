FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create the instance directory for the SQLite database
RUN mkdir -p instance
# Ensure the backups directory exists
RUN mkdir -p backups

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Expose the port
EXPOSE 5050

# Run setup commands at startup
CMD ["sh", "-c", "python -m flask add-reset-columns && python app.py"]
