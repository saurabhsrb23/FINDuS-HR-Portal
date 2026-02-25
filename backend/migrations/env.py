"""Alembic sync migration environment for FindUs."""
from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

# ─── Load application config & models ─────────────────────────────────────────
from app.core.config import settings

try:
    from app.db.base import Base

    # Import all models so their tables are registered in Base.metadata
    # for Alembic autogenerate to detect them.
    from app.models.audit_log import AuditLog  # noqa: F401
    from app.models.company import Company  # noqa: F401
    from app.models.job import Job, JobQuestion, JobSkill, PipelineStage  # noqa: F401
    from app.models.user import User  # noqa: F401
    from app.models.candidate import (  # noqa: F401
        CandidateProfile, WorkExperience, Education, Certification, Project, CandidateSkill
    )
    from app.models.application import Application, ApplicationAnswer, JobAlert  # noqa: F401
    from app.models.ai_summary import AISummary  # noqa: F401

    target_metadata = Base.metadata
except ImportError:
    from sqlalchemy import MetaData

    target_metadata = MetaData()

# ─── Alembic config ───────────────────────────────────────────────────────────
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Always use psycopg2 (sync) for migrations — asyncpg's prepared-statement
# protocol does not handle PL/pgSQL EXCEPTION blocks correctly.
_sync_url = str(settings.DATABASE_URL).replace(
    "postgresql+asyncpg", "postgresql+psycopg2"
)
config.set_main_option("sqlalchemy.url", _sync_url)


# ─── Offline migrations ───────────────────────────────────────────────────────
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ─── Online migrations (sync psycopg2) ───────────────────────────────────────
def run_migrations_online() -> None:
    connectable = create_engine(_sync_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    connectable.dispose()


# ─── Dispatch ─────────────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
