#!/bin/bash
BACKUP_DIR="/root/backups"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cd /root/code/FolioBrake/ops
docker compose exec -T postgres pg_dump -U guardian guardian > "$BACKUP_DIR/guardian_$TIMESTAMP.sql" 2>/dev/null
echo "Backup saved to $BACKUP_DIR/guardian_$TIMESTAMP.sql"
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete 2>/dev/null
