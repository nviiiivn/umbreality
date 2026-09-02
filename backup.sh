#!/bin/bash
# Umbreality Complete Backup — everything in one snapshot
# Usage: ./backup.sh
# Restore: tar -xzf <backup-file> -C /home/nvii
set -e

BACKUP_DIR="/home/nvii/backups"
DATE=$(date +%Y%m%d-%H%M%S)
PROJ="/home/nvii/projects/umbreality-ai"
RETENTION_DAYS=30
SNAPSHOT="$BACKUP_DIR/umbreality-full-$DATE.tar.gz"
SNAPSHOT_LATEST="$BACKUP_DIR/umbreality-full-latest.tar.gz"

mkdir -p "$BACKUP_DIR"

echo "[backup] 🌀 Umbreality Full Backup — $DATE"

# Phase 1: Safe-copy all SQLite databases
DB_TEMP=$(mktemp -d)
echo "[backup] Backing up databases..."
for db in $(find "$PROJ" -name '*.db' -not -path '*/node_modules/*' -not -path '*/.venv/*' | sort); do
    name=$(echo "$db" | sed "s|$PROJ/||" | tr '/' '_')
    cp "$db" "$DB_TEMP/$name"
    echo "  $name"
done

# Phase 2: Create the full snapshot
echo "[backup] Creating snapshot..."
tar -czf "$SNAPSHOT" \
    --exclude='node_modules' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='creative/outputs' \
    -C /home/nvii \
    "projects/umbreality-ai" \
    "www" \
    ".cloudflared/config.yml" \
    "Caddyfile" \
    ".config/systemd/user/umbreality-api.service" \
    "backups" 2>/dev/null

# Add the safe DB copies
tar -rf "$SNAPSHOT" -C "$DB_TEMP" . 2>/dev/null || true

# Phase 3: Manifest
SIZE=$(du -h "$SNAPSHOT" | cut -f1)
sha256sum "$SNAPSHOT" > "$SNAPSHOT.sha256"
echo "[backup] ✅ Complete — $SIZE"
echo ""
echo "To restore: tar -xzf $SNAPSHOT_LATEST -C /home/nvii"
echo "To restore a specific backup: tar -xzf <file> -C /home/nvii"

# Phase 4: Clean old + symlink latest
rm -f "$SNAPSHOT_LATEST"
ln -s "$SNAPSHOT" "$SNAPSHOT_LATEST"
find "$BACKUP_DIR" -name 'umbreality-full-*.tar.gz' -mtime +$RETENTION_DAYS -delete 2>/dev/null

rm -rf "$DB_TEMP"
