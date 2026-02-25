"""Slowapi rate-limiter setup.

Usage in routers:
    from app.core.rate_limiter import limiter

    @router.post("/login")
    @limiter.limit("5/minute")
    async def login(request: Request, ...):
        ...

The limiter instance must be attached to app.state in main.py and the
SlowAPIMiddleware (or exception handler) must be registered.
"""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

# Key function: rate-limit per client IP address
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],          # no global limit — applied per-route
    headers_enabled=True,       # return X-RateLimit-* headers
    strategy="fixed-window",
)
