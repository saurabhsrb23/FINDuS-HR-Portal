"""Celery application — used by start.sh as: celery -A app.worker worker|beat."""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "donehr",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.email_tasks", "app.tasks.job_tasks", "app.tasks.job_alert_tasks", "app.tasks.ai_tasks"],
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
celery_app.conf.beat_schedule = {
    # Archive closed/paused jobs older than 90 days — runs daily at 02:00 UTC
    "auto-archive-expired-jobs": {
        "task": "job_tasks.auto_archive_expired_jobs",
        "schedule": crontab(hour=2, minute=0),
    },
    # Close active jobs whose deadline has passed — runs every hour
    "close-deadline-passed-jobs": {
        "task": "job_tasks.close_deadline_passed_jobs",
        "schedule": crontab(minute=0),  # top of every hour
    },
    # Send job alert digest emails to candidates — runs daily at 07:00 UTC
    "send-job-alerts": {
        "task": "job_alert_tasks.send_job_alerts",
        "schedule": crontab(hour=7, minute=0),
    },
}

# Expose as `app` so `celery -A app.worker` auto-discovers the instance
app = celery_app
