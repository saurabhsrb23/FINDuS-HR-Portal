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

# ─── Seed database (only if users table is empty) ─────────────────────────────
# Strip +asyncpg driver prefix so psql gets a plain postgresql:// URL
PSQL_URL="${DATABASE_URL/+asyncpg/}"
USER_COUNT=$(psql "${PSQL_URL}" -tAc "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")
if [ "$USER_COUNT" = "0" ]; then
  echo "==> [start.sh] Seeding database..."
  python seed.py && echo "==> [start.sh] Seed complete." || echo "==> [start.sh] Seed skipped (seed.py not found or failed)."
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
