"""FindUs — FastAPI application entry point (Module 2: Auth wired in)."""
from __future__ import annotations

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

# ─── OpenTelemetry setup ──────────────────────────────────────────────────────
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


# ─── Lifespan ─────────────────────────────────────────────────────────────────
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

    yield

    await close_redis()
    log.info("shutting_down")


# ─── Application factory ──────────────────────────────────────────────────────
def create_app() -> FastAPI:
    application = FastAPI(
        title="FindUs API",
        description="AI-powered HR portal — REST API",
        version="1.0.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ─── Rate limiter state + exception handler ────────────────────────────────
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    application.add_middleware(SlowAPIMiddleware)

    # ─── CORS ─────────────────────────────────────────────────────────────────
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

    # ─── Request / structured logging ─────────────────────────────────────────
    application.add_middleware(RequestLoggingMiddleware)

    # ─── OpenTelemetry ────────────────────────────────────────────────────────
    _setup_otel(application)

    # ─── Ensure all models are registered in Base.metadata so FK references
    #     resolve correctly (e.g. jobs.company_id → companies.id)
    import app.models.audit_log    # noqa: F401
    import app.models.company      # noqa: F401
    import app.models.job          # noqa: F401
    import app.models.user         # noqa: F401
    import app.models.candidate    # noqa: F401
    import app.models.application  # noqa: F401
    import app.models.ai_summary   # noqa: F401
    import app.models.saved_search  # noqa: F401

    # ─── Routers ──────────────────────────────────────────────────────────────
    from app.routers.auth import router as auth_router
    from app.routers.jobs import analytics_router, router as jobs_router
    from app.routers.candidates import router as candidates_router
    from app.routers.applications import router as applications_router
    from app.routers.ai import router as ai_router
    from app.routers.search import router as search_router

    application.include_router(auth_router)
    # applications_router must be before jobs_router so /jobs/search (static)
    # is matched before /jobs/{job_id} (dynamic) in Starlette's route matching.
    application.include_router(applications_router)
    application.include_router(jobs_router)
    application.include_router(analytics_router)
    application.include_router(candidates_router)
    application.include_router(ai_router)
    application.include_router(search_router)

    # ─── Global exception handler — ensures CORS headers on every 500 ─────────
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

    # ─── Health check ─────────────────────────────────────────────────────────
    @application.get(
        "/health",
        tags=["system"],
        summary="Health check",
        response_description="Service liveness indicator",
    )
    async def health_check() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    return application


app = create_app()
