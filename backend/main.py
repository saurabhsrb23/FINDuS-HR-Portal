"""FindUs — FastAPI application entry point (Module 2: Auth wired in)."""
from __future__ import annotations

import asyncio as _asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

_log = structlog.get_logger("findus.errors")

from app.core.config import settings
from app.core.logging import RequestLoggingMiddleware, configure_logging
from app.core.rate_limiter import limiter
from app.core.redis_client import close_redis, init_redis

# ---- OpenTelemetry setup ----------------------------------------------------
try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    _otel_available = True
except ImportError:
    _otel_available = False


def _setup_otel(app: FastAPI) -> None:
    """Initialise OpenTelemetry tracing if the SDK is available."""
    if not _otel_available:
        return
    resource = Resource.create(
        {"service.name": "findus-backend", "environment": settings.ENVIRONMENT}
    )
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(
        endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    SQLAlchemyInstrumentor().instrument(tracer_provider=provider)


# ---- Lifespan ----------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown logic."""
    configure_logging()
    log = structlog.get_logger("findus.startup")
    log.info("starting_up", environment=settings.ENVIRONMENT)

    # Redis connection pool
    try:
        await init_redis()
        log.info("redis_connected")
    except Exception as exc:
        log.warning("redis_connection_failed", error=str(exc))

    # WebSocket Redis subscriber (Module 7)
    from app.core.websocket_manager import ws_manager
    _ws_sub_task = _asyncio.create_task(ws_manager.start_redis_subscriber())
    log.info("ws_redis_subscriber_started")

    # Chat WebSocket Redis subscriber (Module 9)
    from app.core.chat_manager import chat_manager
    _chat_sub_task = _asyncio.create_task(chat_manager.start_chat_subscriber())
    log.info("chat_redis_subscriber_started")

    yield

    # Shutdown
    _ws_sub_task.cancel()
    _chat_sub_task.cancel()
    try:
        await _ws_sub_task
    except _asyncio.CancelledError:
        pass
    try:
        await _chat_sub_task
    except _asyncio.CancelledError:
        pass

    await close_redis()
    log.info("shutting_down")


# ---- Application factory -----------------------------------------------------
def create_app() -> FastAPI:
    application = FastAPI(
        title="FindUs API",
        description="AI-powered HR portal -- REST API",
        version="1.0.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ---- Rate limiter state + exception handler ------------------------------
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    application.add_middleware(SlowAPIMiddleware)

    # ---- CORS ----------------------------------------------------------------
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[
            "X-Request-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ],
    )

    # ---- Request / structured logging ----------------------------------------
    application.add_middleware(RequestLoggingMiddleware)

    # ---- OpenTelemetry -------------------------------------------------------
    _setup_otel(application)

    # ---- Ensure all models are registered in Base.metadata so FK references
    #      resolve correctly (e.g. jobs.company_id -> companies.id)
    import app.models.audit_log    # noqa: F401
    import app.models.company      # noqa: F401
    import app.models.job          # noqa: F401
    import app.models.user         # noqa: F401
    import app.models.candidate    # noqa: F401
    import app.models.application  # noqa: F401
    import app.models.ai_summary   # noqa: F401
    import app.models.saved_search  # noqa: F401
    import app.models.admin        # noqa: F401
    import app.models.chat         # noqa: F401

    # ---- Routers -------------------------------------------------------------
    from app.routers.auth import router as auth_router
    from app.routers.jobs import analytics_router, router as jobs_router
    from app.routers.candidates import router as candidates_router
    from app.routers.applications import router as applications_router
    from app.routers.ai import router as ai_router
    from app.routers.search import router as search_router
    from app.routers.ws import router as ws_router
    from app.routers.admin import router as admin_router
    from app.routers.chat import admin_chat_router, router as chat_router

    application.include_router(auth_router)
    # applications_router must be before jobs_router so /jobs/search (static)
    # is matched before /jobs/{job_id} (dynamic) in Starlette's route matching.
    application.include_router(applications_router)
    application.include_router(jobs_router)
    application.include_router(analytics_router)
    application.include_router(candidates_router)
    application.include_router(ai_router)
    application.include_router(search_router)
    application.include_router(ws_router)
    application.include_router(admin_router)
    application.include_router(chat_router)
    application.include_router(admin_chat_router)

    # ---- Global exception handler --- ensures CORS headers on every 500 ------
    @application.exception_handler(Exception)
    async def _unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
        _log.error(
            "unhandled_exception",
            path=request.url.path,
            method=request.method,
            error=repr(exc),
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Please try again."},
        )

    # ---- Health check --------------------------------------------------------
    @application.get(
        "/health",
        tags=["system"],
        summary="Health check",
        response_description="Service liveness indicator",
    )
    async def health_check() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    # ---- Prometheus metrics --------------------------------------------------
    @application.get(
        "/metrics",
        tags=["system"],
        summary="Prometheus metrics",
        include_in_schema=False,
    )
    async def prometheus_metrics(request: Request):
        try:
            from prometheus_client import generate_latest, CONTENT_TYPE_LATEST  # type: ignore
            from starlette.responses import Response as _Resp

            # Refresh live gauges before generating output
            try:
                from app.core.telemetry import (
                    update_gauge_active_ws,
                    update_gauge_active_jobs,
                    update_gauge_candidates,
                )
                from app.core.websocket_manager import ws_manager
                from app.db.session import AsyncSessionLocal
                from sqlalchemy import func, select

                update_gauge_active_ws(len(ws_manager.active_connections))

                async with AsyncSessionLocal() as _db:
                    from app.models.job import Job, JobStatus
                    from app.models.candidate import CandidateProfile

                    active_jobs = await _db.scalar(
                        select(func.count()).select_from(Job).where(Job.status == JobStatus.ACTIVE)
                    )
                    total_candidates = await _db.scalar(
                        select(func.count()).select_from(CandidateProfile)
                    )
                    update_gauge_active_jobs(active_jobs or 0)
                    update_gauge_candidates(total_candidates or 0)
            except Exception:
                pass

            data = generate_latest()
            return _Resp(content=data, media_type=CONTENT_TYPE_LATEST)
        except ImportError:
            return JSONResponse(
                {"error": "prometheus_client not installed — pip install prometheus-client"},
                status_code=501,
            )

    return application


app = create_app()
