#!/bin/bash

# Remove any existing container
docker rm -f amrs-maintenance-tracker || true

# Run with explicit environment variables and volumes
docker run -d --name amrs-maintenance-tracker \
  -p 9000:9000 \
  -e DATABASE_URL=sqlite:///instance/app.db \
  -e SECRET_KEY=development_key \
  -e DEBUG=True \
  -e PYTHONUNBUFFERED=1 \
  -v "$(pwd)/server/instance:/app/instance" \
  --entrypoint "/bin/bash" \
  amrs-preventative-maintenance-server \
  -c "cd /app && python -c 'import sys; print(sys.path)' && gunicorn --bind 0.0.0.0:9000 --workers 1 --log-level debug --timeout 60 app_standalone:app"

# Follow logs
docker logs -f amrs-maintenance-tracker
