#!/bin/bash
# Schedule automated database backups
# Run this script via cron: 0 2 * * * /path/to/schedule_backups.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
LOG_FILE="${LOG_FILE:-./logs/backup.log}"

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "Starting scheduled backup"

# Run backup script
python3 "$SCRIPT_DIR/backup_database.py" \
    --database-url "$DATABASE_URL" \
    --backup-dir "$BACKUP_DIR" \
    --s3-bucket "${S3_BACKUP_BUCKET:-}" \
    --s3-prefix "${S3_BACKUP_PREFIX:-database-backups}" \
    --retention-days "${BACKUP_RETENTION_DAYS:-30}" \
    2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -eq 0 ]; then
    log "Backup completed successfully"
else
    log "Backup failed with exit code $EXIT_CODE"
    # Send alert (configure as needed)
    # mail -s "Backup Failed" admin@example.com < "$LOG_FILE"
fi

exit $EXIT_CODE
