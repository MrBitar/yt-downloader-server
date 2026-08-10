FROM python:3.12-slim

# Install system dependencies
RUN apt-get update \
    && apt-get install -y \
        ffmpeg \
        curl \
        git \
        ca-certificates \
        nodejs \
        npm \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install the matching bgutil PO-token provider
RUN git clone --single-branch --branch 1.3.1 \
        https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git \
        /app/bgutil-ytdlp-pot-provider \
    && cd /app/bgutil-ytdlp-pot-provider/server \
    && npm ci \
    && npx tsc

# Copy application
COPY server.py .

# Create downloads directory
RUN mkdir -p downloads

# Verify important components during the build
RUN node --version \
    && yt-dlp --version \
    && python -c "import bgutil_ytdlp_pot_provider; print('bgutil PO-token provider installed')"

# Render provides the PORT environment variable
CMD gunicorn --bind 0.0.0.0:$PORT server:app
