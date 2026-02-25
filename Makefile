# ──────────────────────────────────────────────────────────────────────────────
# FindUs (DoneHR) — Developer Makefile
# Usage: make <target>
# Requires: Docker, Docker Compose v2
# ──────────────────────────────────────────────────────────────────────────────

.PHONY: help up down fresh reset logs seed ps shell test lint

# ── Default target ─────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  FindUs / DoneHR — available make targets"
	@echo ""
	@echo "  First time / fresh clone:"
	@echo "    make fresh        Full fresh start (wipes DB, rebuilds images, seeds)"
	@echo ""
	@echo "  Day-to-day:"
	@echo "    make up           Start all services in background"
	@echo "    make down         Stop all services (keeps data)"
	@echo "    make reset        Stop and DELETE all data (volumes)"
	@echo "    make logs         Follow backend logs (Ctrl+C to stop)"
	@echo "    make ps           Show container status"
	@echo ""
	@echo "  Data:"
	@echo "    make seed         Re-run seed.py manually (safe, idempotent)"
	@echo "    make migrate      Run pending Alembic migrations"
	@echo ""
	@echo "  Development:"
	@echo "    make shell        Open bash shell inside backend container"
	@echo "    make test         Run backend unit tests with coverage"
	@echo "    make flush-cache  Flush Redis cache"
	@echo ""

# ── First-time / fresh clone ───────────────────────────────────────────────────
fresh: reset
	@echo ""
	@echo "==> Building images and starting services..."
	docker compose up --build -d
	@echo ""
	@echo "==> Waiting for backend to finish migrations + seed (following logs)..."
	@echo "    (Press Ctrl+C once you see 'Seed complete' or 'Application startup complete')"
	@echo ""
	docker compose logs -f backend

# ── Standard lifecycle ─────────────────────────────────────────────────────────
up:
	docker compose up --build -d

down:
	docker compose down

reset:
	@echo "==> Stopping all services and removing volumes (all data will be deleted)..."
	docker compose down -v --remove-orphans
	@echo "==> Volumes cleared."

# ── Observability ──────────────────────────────────────────────────────────────
logs:
	docker compose logs -f backend

ps:
	docker compose ps

# ── Data management ───────────────────────────────────────────────────────────
seed:
	@echo "==> Re-running seed.py (idempotent — safe to run multiple times)..."
	docker compose exec backend python seed.py

migrate:
	docker compose exec backend alembic upgrade head

flush-cache:
	docker compose exec redis redis-cli FLUSHDB

# ── Development helpers ───────────────────────────────────────────────────────
shell:
	docker compose exec backend bash

test:
	docker compose exec backend pytest tests/ -v --cov=app --cov-report=term-missing
