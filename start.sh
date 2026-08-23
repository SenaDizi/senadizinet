#!/bin/sh
set -e

PORT_TO_USE="${PORT:-8000}"
HOST_TO_USE="${HOST:-0.0.0.0}"

echo "🚀 SenaDizi Render başlatılıyor -> Host: $HOST_TO_USE, Port: $PORT_TO_USE"
exec uvicorn app.main:app --host "$HOST_TO_USE" --port "$PORT_TO_USE"
