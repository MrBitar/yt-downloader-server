FROM python:3.12-slim

# Install FFmpeg
RUN apt-get update \
    && apt-get install -y ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY server.py .

# Create downloads directory
RUN mkdir -p downloads

# Render provides the PORT environment variable
CMD gunicorn --bind 0.0.0.0:$PORT server:app
