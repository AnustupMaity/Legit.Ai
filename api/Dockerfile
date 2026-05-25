FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code into the api package structure
COPY . /app/api

# Add both /app and /app/api to PYTHONPATH to resolve inconsistent imports
ENV PYTHONPATH="/app:/app/api"

# Create models directory for caching
RUN mkdir -p /app/models

# Expose port
EXPOSE 7860

# Default command
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]
