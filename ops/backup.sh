#!/bin/bash
# =============================================================================
# FolioBrake PostgreSQL Auto-Backup Script
# Creates daily database backups with configurable retention.
# Usage: ./backup.sh  |  crontab: 0 2 * * * /path/to/backup.sh >> /var/log/backup.log 2>&1
# =============================================================================

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
BACKUP_DIR="${BACKUP_DIR:-/root/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
COMPOSE_DIR="/root/code/FolioBrake/ops"
DB_USER="${POSTGRES_USER:-guardian}"
DB_NAME="${POSTGRES_DB:-guardian}"

# ── Setup ────────────────────────────────────────────────────────────────────
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/guardian_${TIMESTAMP}.sql"

echo "[$(date -Iseconds)] Starting backup of '$DB_NAME' database..."

# ── Dump ─────────────────────────────────────────────────────────────────────
cd "$COMPOSE_DIR"
if ! docker compose exec -T postgres pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE" 2>/dev/null; then
    echo "[$(date -Iseconds)] ERROR: pg_dump failed" >&2
    rm -f "$BACKUP_FILE"
    exit 1
fi

# ── Verify ───────────────────────────────────────────────────────────────────
FILE_SIZE=$(stat -c%s "$BACKUP_FILE" 2>/dev/null || stat -f%z "$BACKUP_FILE" 2>/dev/null || echo "0")
if [ "$FILE_SIZE" -lt 100 ]; then
    echo "[$(date -Iseconds)] ERROR: Backup file suspiciously small ($FILE_SIZE bytes)" >&2
    rm -f "$BACKUP_FILE"
    exit 1
fi

echo "[$(date -Iseconds)] Backup saved: $BACKUP_FILE ($FILE_SIZE bytes)"

# ── Cleanup old backups ──────────────────────────────────────────────────────
DELETED=$(find "$BACKUP_DIR" -name "guardian_*.sql" -mtime +"$RETENTION_DAYS" -delete -print | wc -l)
if [ "$DELETED" -gt 0 ]; then
    echo "[$(date -Iseconds)] Cleaned up $DELETED backup(s) older than $RETENTION_DAYS days"
fi

echo "[$(date -Iseconds)] Backup completed successfully"
