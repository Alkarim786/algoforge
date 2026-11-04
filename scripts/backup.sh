#!/usr/bin/env bash
# Dumps the production database to backups/ and deletes dumps older than KEEP_DAYS (default 14).
# Run nightly from cron, for example:
#   15 3 * * * /opt/algoforge/scripts/backup.sh >> /opt/algoforge/backups/backup.log 2>&1
# Restore a dump into a running stack (this replaces the current data):
#   docker compose -f docker-compose.prod.yml exec -T db sh -c \
#     'pg_restore --clean --if-exists -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < backups/<file>.dump
set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p backups
chmod 700 backups
target="backups/algoforge-$(date -u +%Y%m%dT%H%M%SZ).dump"
docker compose -f docker-compose.prod.yml exec -T db \
  sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' > "$target.partial"
mv "$target.partial" "$target"
find backups -name 'algoforge-*.dump' -mtime +"${KEEP_DAYS:-14}" -delete
echo "$(date -u +%FT%TZ) wrote $target ($(du -h "$target" | cut -f1))"
