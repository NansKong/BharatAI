# BharatAI — Disaster Recovery Playbook

## 1. PostgreSQL Restore

### From S3 Backup
```bash
# Download latest backup
aws s3 ls s3://bharatai-backups/postgres/ --recursive | sort | tail -1
aws s3 cp s3://bharatai-backups/postgres/bharatai_db_YYYYMMDD_HHMMSS.sql.gz /tmp/restore.sql.gz

# Restore
gunzip /tmp/restore.sql.gz
psql -U bharatai -d bharatai_db < /tmp/restore.sql
# Or for custom-format dumps:
pg_restore -U bharatai -d bharatai_db --no-owner --clean /tmp/restore.sql.gz
```

### From Local Backup
```bash
ls -lt /tmp/bharatai-backups/ | head -5
gunzip -c /tmp/bharatai-backups/bharatai_db_LATEST.sql.gz | psql -U bharatai -d bharatai_db
```

### Post-Restore Verification
```bash
psql -U bharatai -d bharatai_db -c "SELECT COUNT(*) FROM users;"
psql -U bharatai -d bharatai_db -c "SELECT COUNT(*) FROM opportunities;"
alembic current  # Verify migration version matches
```

## 2. Redis Recovery

Redis uses AOF + RDB persistence. On restart, Redis auto-loads from these files.

### Verify Persistence Config
```bash
redis-cli CONFIG GET save           # RDB: "3600 1 300 100 60 10000"
redis-cli CONFIG GET appendonly     # AOF: "yes"
redis-cli CONFIG GET appendfsync   # AOF fsync: "everysec"
```

### Manual Recovery
```bash
# Stop Redis
sudo systemctl stop redis

# Copy backup AOF/RDB files
cp /backup/appendonly.aof /var/lib/redis/
cp /backup/dump.rdb /var/lib/redis/

# Restart
sudo systemctl start redis
redis-cli PING  # Should return PONG
```

### Post-Restore
All JWT blocklist entries and rate-limit counters are ephemeral — they will naturally repopulate. Cache keys will be cold-started (first requests will be slower).

## 3. Elasticsearch Recovery

### From S3 Snapshot Repository
```bash
# Register snapshot repository (one-time)
curl -X PUT "localhost:9200/_snapshot/s3_backup" -H 'Content-Type: application/json' -d '{
  "type": "s3",
  "settings": { "bucket": "bharatai-backups", "base_path": "elasticsearch" }
}'

# List available snapshots
curl "localhost:9200/_snapshot/s3_backup/_all"

# Restore latest
curl -X POST "localhost:9200/_snapshot/s3_backup/SNAPSHOT_NAME/_restore" -H 'Content-Type: application/json' -d '{
  "indices": "bharatai_opportunities",
  "ignore_unavailable": true
}'
```

### Full Re-index (if no snapshot available)
```bash
# Trigger re-index from PostgreSQL
curl -X POST http://localhost:8000/api/v1/admin/reindex -H "Authorization: Bearer <ADMIN_TOKEN>"
```

## 4. Full System Recovery Checklist

| Step | Action | Verify |
|------|--------|--------|
| 1 | Restore PostgreSQL from S3 backup | `SELECT COUNT(*) FROM users` returns expected count |
| 2 | Start Redis (auto-recovers from AOF/RDB) | `redis-cli PING` → PONG |
| 3 | Run `alembic upgrade head` | No pending migrations |
| 4 | Start backend: `uvicorn app.main:app` | `/health` returns `{"status": "healthy"}` |
| 5 | Restore Elasticsearch snapshot | Search returns results |
| 6 | Start frontend: `npm run dev` | Landing page loads |
| 7 | Run smoke tests | `pytest tests/smoke/ -v` passes |

## 5. RTO / RPO Targets

| Metric | Target | Current |
|--------|--------|---------|
| RPO (data loss) | < 1 hour | ~1 hour (hourly backups) |
| RTO (time to recover) | < 30 minutes | ~20 min (scripted restore) |

## 6. Backup Schedule

| System | Method | Frequency | Retention |
|--------|--------|-----------|-----------|
| PostgreSQL | `pg_dump` → S3 | Daily 2 AM UTC | 7 daily, 4 weekly, 3 monthly |
| Redis | AOF + RDB auto-persist | Continuous | Kept on disk |
| Elasticsearch | S3 snapshot | Daily 3 AM UTC | 7 daily |
