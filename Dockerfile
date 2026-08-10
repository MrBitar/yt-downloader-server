FROM python:3.12-slim

# ============================================================
# SYSTEM DEPENDENCIES
# ============================================================

RUN apt-get update \
    && apt-get install -y \
        ffmpeg \
        curl \
        ca-certificates \
        git \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# NODE.JS 22
# ============================================================

RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && node --version \
    && npm --version

# ============================================================
# APPLICATION
# ============================================================

WORKDIR /app

# ============================================================
# PYTHON DEPENDENCIES
# ============================================================

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

# ============================================================
# BGUTIL PO TOKEN PROVIDER
# ============================================================

RUN git clone \
    --single-branch \
    --branch 1.3.1 \
    https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git \
    /app/bgutil-ytdlp-pot-provider

# ============================================================
# BUILD BGUTIL
# ============================================================

RUN cd /app/bgutil-ytdlp-pot-provider/server \
    && npm ci \
    && npx tsc

# ============================================================
# COPY APPLICATION
# ============================================================

COPY server.py /app/server.py

RUN mkdir -p /app/downloads

# ============================================================
# VERIFY EVERYTHING
# ============================================================

RUN echo "===== SERVER.PY =====" \
    && ls -la /app/server.py \
    && echo "===== BGUTIL SERVER =====" \
    && ls -la /app/bgutil-ytdlp-pot-provider/server \
    && echo "===== BGUTIL BUILD =====" \
    && ls -la /app/bgutil-ytdlp-pot-provider/server/build

# ============================================================
# START SERVER
# ============================================================

CMD sh -c '\
    echo "========================================"; \
    echo "STARTING BGUTIL PO TOKEN SERVER"; \
    echo "========================================"; \
    cd /app/bgutil-ytdlp-pot-provider/server; \
    node build/main.js > /tmp/bgutil.log 2>&1 & \
    BGUTIL_PID=$!; \
    echo "BGUTIL PID: $BGUTIL_PID"; \
    sleep 5; \
    echo "===== BGUTIL LOG ====="; \
    cat /tmp/bgutil.log || true; \
    echo "========================================"; \
    echo "STARTING GUNICORN"; \
    echo "========================================"; \
    exec gunicorn --bind 0.0.0.0:${PORT:-10000} server:app \
'
