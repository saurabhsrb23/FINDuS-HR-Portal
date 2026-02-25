"""Celery application — used by start.sh as: celery -A app.worker worker|beat."""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "donehr",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.email_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,                   # only ack after successful execution
    worker_prefetch_multiplier=1,          # fair dispatch
    task_track_started=True,
    result_expires=3600,                   # results TTL: 1 hour
    broker_connection_retry_on_startup=True,
)

# ─── Periodic tasks (Celery Beat) ─────────────────────────────────────────────
# Beat schedules for future maintenance tasks will be added here as modules arrive.
celery_app.conf.beat_schedule = {}

# Expose as `app` so `celery -A app.worker` auto-discovers the instance
app = celery_app
