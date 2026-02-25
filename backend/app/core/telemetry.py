"""OpenTelemetry setup and Prometheus metrics helpers."""
from __future__ import annotations

import contextlib
import time
from typing import Any, Generator

import structlog

_log = structlog.get_logger("telemetry")

# ── Prometheus metrics ────────────────────────────────────────────────────────
try:
    from prometheus_client import Counter, Gauge, Histogram  # type: ignore

    REQUEST_COUNT = Counter(
        "total_requests_total",
        "Total HTTP requests received",
        ["method", "path", "status"],
    )
    FAILED_REQUEST_COUNT = Counter(
        "failed_requests_total",
        "Total HTTP requests that returned 5xx",
        ["method", "path"],
    )
    AI_TOKENS_USED = Counter(
        "ai_tokens_used_total",
        "Total AI tokens consumed (Groq)",
        ["model", "operation"],
    )
    DB_QUERY_DURATION = Histogram(
        "db_query_duration_seconds",
        "Duration of DB queries in seconds",
        ["operation"],
        buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
    )
    ACTIVE_WS_CONNECTIONS = Gauge(
        "active_websocket_connections",
        "Number of currently active WebSocket connections",
    )
    ACTIVE_JOBS_TOTAL = Gauge(
        "active_jobs_total",
        "Number of currently published/active jobs",
    )
    TOTAL_CANDIDATES = Gauge(
        "total_candidates_total",
        "Total number of candidate profiles",
    )
    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False
    _log.warning("prometheus_not_installed", hint="pip install prometheus-client")


def record_ai_tokens(model: str, operation: str, token_count: int) -> None:
    """Increment the AI tokens counter after every Groq API call."""
    if _PROMETHEUS_AVAILABLE:
        AI_TOKENS_USED.labels(model=model, operation=operation).inc(token_count)


@contextlib.contextmanager
def db_query_span(operation: str) -> Generator[None, None, None]:
    """Context manager that measures DB query duration."""
    t0 = time.monotonic()
    try:
        yield
    finally:
        if _PROMETHEUS_AVAILABLE:
            DB_QUERY_DURATION.labels(operation=operation).observe(time.monotonic() - t0)


# ── OpenTelemetry manual spans ────────────────────────────────────────────────
try:
    from opentelemetry import trace as _otel_trace  # type: ignore
    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False


@contextlib.contextmanager
def groq_span(operation: str, model: str, user_id: str | None = None) -> Generator[Any, None, None]:
    """Wrap a Groq API call in an OpenTelemetry span."""
    if not _OTEL_AVAILABLE:
        yield None
        return
    tracer = _otel_trace.get_tracer("findus.ai")
    with tracer.start_as_current_span(f"groq.{operation}") as span:
        span.set_attribute("ai.model", model)
        span.set_attribute("ai.operation", operation)
        if user_id:
            span.set_attribute("user.id", user_id)
        yield span


@contextlib.contextmanager
def celery_task_span(task_name: str, **attributes: Any) -> Generator[Any, None, None]:
    """Wrap a Celery task in an OpenTelemetry span."""
    if not _OTEL_AVAILABLE:
        yield None
        return
    tracer = _otel_trace.get_tracer("findus.celery")
    with tracer.start_as_current_span(f"celery.{task_name}") as span:
        span.set_attribute("celery.task", task_name)
        for k, v in attributes.items():
            span.set_attribute(k, str(v))
        yield span


def update_gauge_active_ws(count: int) -> None:
    if _PROMETHEUS_AVAILABLE:
        ACTIVE_WS_CONNECTIONS.set(count)


def update_gauge_active_jobs(count: int) -> None:
    if _PROMETHEUS_AVAILABLE:
        ACTIVE_JOBS_TOTAL.set(count)


def update_gauge_candidates(count: int) -> None:
    if _PROMETHEUS_AVAILABLE:
        TOTAL_CANDIDATES.set(count)
