#!/usr/bin/env bash
# Builds and (re)starts the production stack, then loads the content files. Safe to re-run for every update:
#   git pull && ./scripts/deploy.sh
# Settings come from .env (see DEPLOY.md). WORKERS sets how many submissions are judged at once (default 2).
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "No .env yet. Run: python3 scripts/init_env.py --domain your.domain" >&2
  exit 1
fi
set -a
. ./.env
set +a
if [ -z "${DOMAIN:-}" ]; then
  echo "Set DOMAIN in .env (python3 scripts/init_env.py --domain your.domain adds it)." >&2
  exit 1
fi

compose() { docker compose -f docker-compose.prod.yml "$@"; }

echo "==> Building images"
compose build

echo "==> Starting services (migrations run as the API starts)"
compose up -d --remove-orphans --scale worker="${WORKERS:-2}"

echo "==> Loading topics, problems, test cases and solution guides"
compose exec -T api python -m app.seed

echo "==> Status"
compose ps
echo
echo "Live at https://${DOMAIN#*://} (the first HTTPS certificate can take a minute)."
echo "First deploy? Create your admin account:"
echo "  docker compose -f docker-compose.prod.yml exec api python -m app.create_admin <username> <email>"
