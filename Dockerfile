FROM python:3.12-slim

# ------------------------------------------------------------
# System dependencies
# ------------------------------------------------------------

RUN apt-get update \
    && apt-get install -y \
        ffmpeg \
        curl \
        ca-certificates \
        git \
    && rm -rf /var/lib/apt/lists/*


# ------------------------------------------------------------
# Install Node.js 22
# Required by bgutil PO-token provider
# ------------------------------------------------------------

RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && node --version \
    && npm --version


# ------------------------------------------------------------
# Application directory
# ------------------------------------------------------------

WORKDIR /app


# ------------------------------------------------------------
# Python dependencies
# ------------------------------------------------------------

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt


# ------------------------------------------------------------
# Install bgutil PO-token provider
# ------------------------------------------------------------

RUN git clone \
        --single-branch \
        --branch 1.3.1 \
        https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git \
        /app/bgutil-ytdlp-pot-provider


# ------------------------------------------------------------
# Build the provider server
# ------------------------------------------------------------

RUN cd /app/bgutil-ytdlp-pot-provider/server \
    && npm ci \
    && npx tsc


# ------------------------------------------------------------
# Copy application
# ------------------------------------------------------------

COPY server.py .


# ------------------------------------------------------------
# Downloads directory
# ------------------------------------------------------------

RUN mkdir -p downloads


# ------------------------------------------------------------
# Verify installation
# ------------------------------------------------------------

RUN echo "========================================" \
    && echo "Node version:" \
    && node --version \
    && echo "========================================" \
    && echo "npm version:" \
    && npm --version \
    && echo "========================================" \
    && echo "yt-dlp version:" \
    && yt-dlp --version \
    && echo "========================================" \
    && echo "Python version:" \
    && python --version \
    && echo "========================================"


# ------------------------------------------------------------
# Start Flask application with Gunicorn
# ------------------------------------------------------------

CMD gunicorn --bind 0.0.0.0:$PORT server:app
