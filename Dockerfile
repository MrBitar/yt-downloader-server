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

WORKDIR /app

# Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

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

# Copy application
COPY server.py .

# Downloads
RUN mkdir -p downloads

# Start bgutil first, then Gunicorn
CMD sh -c ' \
    node /app/bgutil-ytdlp-pot-provider/server/build/main.js --port 4416 & \
    BGUTIL_PID=$!; \
    sleep 3; \
    echo "================================"; \
    echo "BGUTIL SERVER STARTED"; \
    echo "PID: $BGUTIL_PID"; \
    echo "PORT: 4416"; \
    echo "================================"; \
    gunicorn --bind 0.0.0.0:$PORT server:app \
'
