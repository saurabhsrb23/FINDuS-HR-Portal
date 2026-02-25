#!/bin/bash
set -e

echo "==> [start.sh] Starting FindUs backend..."

# ─── Wait for PostgreSQL ───────────────────────────────────────────────────────
echo "==> [start.sh] Waiting for PostgreSQL to be ready..."
until pg_isready -h "${POSTGRES_HOST:-postgres}" -U "${POSTGRES_USER:-donehr}" -d "${POSTGRES_DB:-donehr}" -q; do
  echo "    PostgreSQL not ready — retrying in 2s..."
  sleep 2
done
echo "==> [start.sh] PostgreSQL is ready."

# ─── Run Alembic migrations ───────────────────────────────────────────────────
echo "==> [start.sh] Running database migrations..."
alembic upgrade head
echo "==> [start.sh] Migrations complete."

# ─── Seed database (idempotent — safe to run every startup) ───────────────────
# seed.py uses ON CONFLICT DO NOTHING / fixed UUIDs so it won't duplicate data.
# We check the users table first for a fast skip on already-seeded DBs.
echo "==> [start.sh] Checking if seed is needed..."

# Use psql (available via postgresql-client in Dockerfile) to count users
PSQL_URL="${DATABASE_URL/+asyncpg/}"
USER_COUNT=$(psql "${PSQL_URL}" -tAc "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d '[:space:]' || echo "0")
USER_COUNT="${USER_COUNT:-0}"

if [ "${USER_COUNT}" = "0" ]; then
  echo "==> [start.sh] No users found — running seed..."
  # Temporarily disable set -e so a seed failure doesn't kill the container
  set +e
  python seed.py
  SEED_EXIT=$?
  set -e

  if [ ${SEED_EXIT} -eq 0 ]; then
    echo "==> [start.sh] Seed complete — all demo data loaded."
  else
    echo ""
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    echo "!! WARNING: seed.py exited with code ${SEED_EXIT}              !!"
    echo "!! The app will still start but demo users will be missing.    !!"
    echo "!! Re-run with: docker compose exec backend python seed.py     !!"
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    echo ""
  fi
else
  echo "==> [start.sh] Database already seeded (${USER_COUNT} users found). Skipping."
fi

# ─── Start Celery worker (background) ─────────────────────────────────────────
echo "==> [start.sh] Starting Celery worker..."
celery -A app.worker worker --loglevel=info --concurrency=2 &
CELERY_WORKER_PID=$!
echo "    Celery worker PID: ${CELERY_WORKER_PID}"

# ─── Start Celery beat (background) ───────────────────────────────────────────
echo "==> [start.sh] Starting Celery beat scheduler..."
celery -A app.worker beat --loglevel=info &
CELERY_BEAT_PID=$!
echo "    Celery beat PID: ${CELERY_BEAT_PID}"

# ─── Start Uvicorn ────────────────────────────────────────────────────────────
echo "==> [start.sh] Starting Uvicorn on 0.0.0.0:8000 with 2 workers..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
