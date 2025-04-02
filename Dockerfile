FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Set default environment variables
ENV ENVIRONMENT=development \
    LOG_LEVEL=INFO \
    MAX_CONNECTIONS=20 \
    POOL_TIMEOUT=30 \
    ADMIN_PANEL_ENABLED=false \
    WEBAPP_SERVICE_URL=http://webapp:3000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 