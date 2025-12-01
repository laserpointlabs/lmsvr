FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure data directory exists and is writable by any user
RUN mkdir -p /app/data && chmod 777 /app/data

# Expose port
EXPOSE 8000

# Run the application
# Note: User will be set via docker-compose.yml user directive
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

