FROM python:3.12-slim

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

COPY server.py .
COPY start.sh .

RUN chmod +x start.sh

RUN mkdir -p downloads

CMD ["/app/start.sh"]
