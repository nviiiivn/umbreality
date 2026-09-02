#!/bin/bash
# UmbrealityAI — Public Tunnel via localhost.run
# Uses known IPs as DNS backup for flaky resolvers
LOG=/tmp/localtunnel.log
KNOWN_IPS="54.161.197.247 35.171.254.69 54.82.85.249"

log() { echo "[$(date)] $*"; }

resolve() {
    # Try system DNS first, fall back to known IPs
    IP=$(getent hosts localhost.run 2>/dev/null | awk '{print $1}')
    if [ -n "$IP" ]; then
        echo "$IP"
        return 0
    fi
    # Try Google DNS
    IP=$(dig @8.8.8.8 localhost.run +short 2>/dev/null | head -1)
    if [ -n "$IP" ]; then
        echo "$IP"
        return 0
    fi
    # Fall back to known IP
    echo "$1"
}

exec > "$LOG" 2>&1
log "Starting localhost.run tunnel for port 6999"

while true; do
    HOST=$(resolve "${KNOWN_IPS%% *}")
    log "Resolved localhost.run → $HOST"
    log "Connecting..."
    ssh -o StrictHostKeyChecking=no \
        -o ServerAliveInterval=10 \
        -o ServerAliveCountMax=6 \
        -o ExitOnForwardFailure=yes \
        -o TCPKeepAlive=yes \
        -R 80:localhost:6999 "root@$HOST"
    log "Disconnected (exit: $?). Reconnecting in 5s..."
    sleep 5
done
