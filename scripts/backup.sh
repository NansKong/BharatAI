#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# BharatAI — PostgreSQL Backup Script
# Run via cron in production:
#   0 2 * * * /opt/bharatai/scripts/backup.sh >> /var/log/bharatai-backup.log 2>&1
# ─────────────────────────────────────────────────────────────
set -euo pipefail

# ── Configuration ──────────────────────────────────────────
DB_NAME="${DB_NAME:-bharatai_db}"
DB_USER="${DB_USER:-bharatai}"
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-5432}"

S3_BUCKET="${S3_BUCKET:-bharatai-backups}"
S3_PREFIX="${S3_PREFIX:-postgres}"

BACKUP_DIR="/tmp/bharatai-backups"
RETENTION_DAYS=7

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="${DB_NAME}_${TIMESTAMP}.sql.gz"

# ── Create backup directory ────────────────────────────────
mkdir -p "$BACKUP_DIR"

# ── Dump → Gzip ───────────────────────────────────────────
echo "[$(date -Iseconds)] Starting pg_dump for ${DB_NAME}..."
pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -Fc \
    --no-owner \
    --no-acl \
    "$DB_NAME" | gzip > "${BACKUP_DIR}/${FILENAME}"

BACKUP_SIZE=$(stat --printf="%s" "${BACKUP_DIR}/${FILENAME}" 2>/dev/null || stat -f "%z" "${BACKUP_DIR}/${FILENAME}" 2>/dev/null || echo "unknown")
echo "[$(date -Iseconds)] Backup created: ${FILENAME} (${BACKUP_SIZE} bytes)"

# ── Upload to S3 ──────────────────────────────────────────
if command -v aws &> /dev/null; then
    aws s3 cp "${BACKUP_DIR}/${FILENAME}" "s3://${S3_BUCKET}/${S3_PREFIX}/${FILENAME}"
    echo "[$(date -Iseconds)] Uploaded to s3://${S3_BUCKET}/${S3_PREFIX}/${FILENAME}"
else
    echo "[$(date -Iseconds)] WARNING: aws CLI not found — backup stays local only"
fi

# ── Clean old local backups ───────────────────────────────
find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
echo "[$(date -Iseconds)] Cleaned local backups older than ${RETENTION_DAYS} days"

echo "[$(date -Iseconds)] Backup complete ✓"
