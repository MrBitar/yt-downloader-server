FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

# ffmpeg: needed by yt-dlp to merge video+audio
# git/curl/gnupg: needed to fetch Node.js and the PO token provider source
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg git curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# PO token provider server: generates the tokens yt-dlp needs so YouTube
# stops treating requests from this server as a bot. Pinned to a known
# release rather than tracking master so builds stay reproducible.
RUN git clone --single-branch --branch 1.3.1 \
        https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git /tmp/pot-provider \
    && cd /tmp/pot-provider/server \
    && npm ci \
    && npx tsc \
    && mkdir -p /app/pot-server \
    && cp -r build node_modules package.json /app/pot-server/ \
    && rm -rf /tmp/pot-provider

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py .
COPY start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]
