#!/bin/sh

echo "================================"
echo "STARTING BGUTIL PO-TOKEN SERVER"
echo "================================"

cd /app/bgutil-ytdlp-pot-provider/server

node build/main.js --port 4416 &

BGUTIL_PID=$!

echo "BGUTIL PID: $BGUTIL_PID"

sleep 5

echo "================================"
echo "CHECKING BGUTIL"
echo "================================"

if kill -0 "$BGUTIL_PID" 2>/dev/null; then
    echo "BGUTIL PROCESS IS RUNNING"
else
    echo "BGUTIL PROCESS FAILED TO START"
fi

echo "================================"
echo "STARTING GUNICORN"
echo "================================"

exec gunicorn --bind 0.0.0.0:${PORT} server:app
