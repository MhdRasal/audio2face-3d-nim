#!/bin/bash
set -e

NIM_START="/opt/nim/start_server.sh"
if [ ! -f "$NIM_START" ]; then
    NIM_START=$(find /opt/nim -name "start_server.sh" -type f 2>/dev/null | head -1)
fi
if [ -z "$NIM_START" ]; then
    echo "[entrypoint] ERROR: start_server.sh not found in /opt/nim"
    ls -la /opt/nim/ 2>/dev/null
    exit 1
fi

chmod +x "$NIM_START" 2>/dev/null || true
echo "[entrypoint] Starting NIM server from $NIM_START ..."
bash "$NIM_START" &

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
