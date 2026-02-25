"""Structured JSON logging configuration using structlog."""
from __future__ import annotations

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings

# ─── Context variables (propagated per-request) ───────────────────────────────
_request_id_var: ContextVar[str] = ContextVar("request_id", default="")
_user_id_var: ContextVar[str] = ContextVar("user_id", default="")


def get_request_id() -> str:
    return _request_id_var.get()


def get_user_id() -> str:
    return _user_id_var.get()


def set_request_id(value: str) -> None:
    _request_id_var.set(value)


def set_user_id(value: str) -> None:
    _user_id_var.set(value)


# ─── Custom processors ────────────────────────────────────────────────────────
def _inject_context(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Inject per-request context into every log entry."""
    request_id = get_request_id()
    user_id = get_user_id()
    if request_id:
        event_dict["request_id"] = request_id
    if user_id:
        event_dict["user_id"] = user_id
    return event_dict


def _rename_event_key(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Rename structlog's 'event' key to 'message' for log aggregators."""
    event_dict["message"] = event_dict.pop("event", "")
    return event_dict


# ─── Configure structlog ──────────────────────────────────────────────────────
def configure_logging() -> None:
    """Call once at application startup to initialise structlog + stdlib logging."""

    log_level = logging.DEBUG if settings.is_development else logging.INFO

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _inject_context,
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.is_development:
        # Human-friendly coloured output in dev
        structlog.configure(
            processors=[
                *shared_processors,
                structlog.dev.ConsoleRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(log_level),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # JSON output for production log aggregators (Loki, Datadog, etc.)
        structlog.configure(
            processors=[
                *shared_processors,
                _rename_event_key,
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(log_level),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )

    # Route stdlib logging through structlog so third-party libs use our format
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    for name in ("uvicorn", "uvicorn.access", "sqlalchemy.engine", "celery"):
        logging.getLogger(name).setLevel(log_level)


# ─── Request logging middleware ───────────────────────────────────────────────
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Attaches a request_id to every request and logs method + path + duration."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        import time

        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        set_request_id(request_id)

        # Attempt to extract user_id from JWT without full auth overhead
        user_id = ""
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                from jose import jwt as jose_jwt

                token = auth_header[7:]
                payload = jose_jwt.decode(
                    token,
                    settings.SECRET_KEY.get_secret_value(),
                    algorithms=[settings.ALGORITHM],
                    options={"verify_exp": False},
                )
                user_id = str(payload.get("sub", ""))
            except Exception:
                pass
        set_user_id(user_id)

        log = structlog.get_logger()
        start = time.perf_counter()

        response: Response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log.info(
            "http_request",
            method=request.method,
            endpoint=str(request.url.path),
            status_code=response.status_code,
            execution_time_ms=duration_ms,
        )

        response.headers["X-Request-ID"] = request_id
        return response


# ─── Module-level logger for direct use ───────────────────────────────────────
logger = structlog.get_logger("findus")
