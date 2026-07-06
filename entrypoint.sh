#!/bin/bash
set -e

NIM_START=$(find /opt/nim -name "start_server.py" -type f 2>/dev/null | head -1)
if [ -z "$NIM_START" ]; then
    echo "[entrypoint] ERROR: start_server.py not found"
    exit 1
fi

echo "[entrypoint] Starting NIM server from $NIM_START ..."
python "$NIM_START" &

echo "[entrypoint] Waiting for gRPC on port 52000..."
for i in $(seq 1 150); do
    if python -c "import socket; s=socket.socket(); s.connect(('localhost',52000)); s.close()" 2>/dev/null; then
        echo "[entrypoint] gRPC ready after $((i*2))s"
        break
    fi
    sleep 2
done

echo "[entrypoint] Starting bridge on port 8080..."
exec uvicorn bridge_server:app --host 0.0.0.0 --port 8080 --log-level info
