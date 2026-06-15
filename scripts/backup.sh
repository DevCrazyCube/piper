#!/usr/bin/env bash
# Encrypted logical backup (part of the 3-2-1 strategy — docs/04-security.md).
# Backups are ENCRYPTED at rest and fall under the same erasure obligation as live data.
# Usage: bash scripts/backup.sh   (reads creds from .env)
set -euo pipefail
cd "$(dirname "$0")/.."

set -a; . ./.env; set +a
: "${AEGIS_DB_USER:?}" "${AEGIS_DB_NAME:?}"
PASS="${AEGIS_BACKUP_PASSPHRASE:-$AEGIS_MASTER_KEY}"   # prefer a dedicated backup key

mkdir -p backups
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="backups/aegis-${TS}.sql.gz.enc"

docker compose exec -T db pg_dump -U "$AEGIS_DB_USER" -d "$AEGIS_DB_NAME" \
  | gzip \
  | openssl enc -aes-256-cbc -salt -pbkdf2 -pass "pass:${PASS}" -out "$OUT"

echo "wrote ${OUT} ($(du -h "$OUT" | cut -f1))"
echo "restore: openssl enc -d -aes-256-cbc -pbkdf2 -pass pass:\$KEY -in ${OUT} | gunzip | psql ..."
