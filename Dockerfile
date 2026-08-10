FROM python:3.12-slim

# System dependencies
RUN apt-get update \
    && apt-get install -y \
        ffmpeg \
        curl \
        ca-certificates \
        git \
    && rm -rf /var/lib/apt/lists/*

# Node.js 22
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && node --version \
    && npm --version

# Application directory
WORKDIR /app

# Python dependencies
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

# Install bgutil
RUN git clone \
    --single-branch \
    --branch 1.3.1 \
    https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git \
    /app/bgutil-ytdlp-pot-provider

# Build bgutil
RUN cd /app/bgutil-ytdlp-pot-provider/server \
    && npm ci \
    && npx tsc

# IMPORTANT:
# Copy server.py into /app
COPY server.py /app/server.py

# Create downloads directory
RUN mkdir -p /app/downloads

# Verify server.py exists during Docker build
RUN ls -la /app/server.py

# Start Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "server:app"]
