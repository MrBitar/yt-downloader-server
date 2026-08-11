#!/bin/sh
set -e

node /app/pot-server/build/main.js &

exec gunicorn -w 1 -b 0.0.0.0:$PORT server:app --timeout 300
