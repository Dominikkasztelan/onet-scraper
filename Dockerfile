# Use an official lightweight Python image.
# 3.12-slim is roughly 150MB vs 1GB for full image.
FROM python:3.12-slim

# Set environment variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing pyc files to disc
# PYTHONUNBUFFERED: Ensures output is flushed directly to terminal (important for Docker logs)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a non-root user for security
RUN useradd -m appuser

# Set working directory
WORKDIR /app

# Install system dependencies if needed (e.g. for lxml or cryptic libraries)
# For this scraper, pure python deps should suffice, but we'll add build-essential just in case
# and clean up afterwards to keep image small.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Define the command to run the scraper
CMD ["python", "-m", "scrapy", "crawl", "onet"]
