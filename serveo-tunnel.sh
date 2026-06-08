#!/bin/bash
# UmbrealityAI — Public Tunnel via serveo.net
# Keeps running, reconnects on drop
# Logs to /tmp/serveo-tunnel.log

exec > /tmp/serveo-tunnel.log 2>&1

echo "[$(date)] Starting serveo tunnel for port 6999"

while true; do
    echo "[$(date)] Connecting to serveo.net..."
    ssh -o StrictHostKeyChecking=no \
        -o ServerAliveInterval=15 \
        -o ServerAliveCountMax=3 \
        -o ExitOnForwardFailure=yes \
        -R 80:localhost:6999 serveo.net 2>&1
    
    EXIT_CODE=$?
    echo "[$(date)] Tunnel disconnected (exit: $EXIT_CODE). Reconnecting in 5s..."
    sleep 5
done
