"""SQLAlchemy declarative base.

All model files import `Base` from here.
This module also imports every model at the bottom so that Alembic's
autogenerate can discover their metadata without being told about them
individually in env.py.

Circular-import safety: `Base` is defined before the model imports, so
Python's partial-module mechanism allows the model files to safely
``from app.db.base import Base`` while this module is still loading.
"""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Project-wide SQLAlchemy declarative base."""


# Model imports are intentionally NOT here — importing models from base.py
# causes a circular import when the app's router chain loads user.py first.
# For Alembic autogenerate, models are imported in migrations/env.py.
