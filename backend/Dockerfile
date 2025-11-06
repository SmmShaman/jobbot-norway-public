# Dockerfile for Google Cloud Run
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (needed for web scraping)
RUN playwright install --with-deps chromium

# Copy application code
COPY ./app ./app

# Cloud Run injects PORT env variable, default to 8080
ENV PORT=8080
EXPOSE 8080

# Run the application with dynamic port from Cloud Run
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
