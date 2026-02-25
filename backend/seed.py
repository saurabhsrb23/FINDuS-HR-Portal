"""Bootstrap seed data — run once when the users table is empty."""
from __future__ import annotations

import asyncio
import uuid

import structlog
from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.user import User, UserRole

log = structlog.get_logger("seed")


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        # Guard: skip if any user already exists
        result = await session.execute(select(User.id).limit(1))
        if result.scalar_one_or_none() is not None:
            log.info("seed_skipped", reason="users table already has data")
            return

        users_to_create = [
            User(
                id=uuid.uuid4(),
                email="elite@donehr.com",
                password_hash=hash_password("Elite@Admin1!"),
                full_name="Elite Admin",
                role=UserRole.ELITE_ADMIN,
                is_active=True,
                is_verified=True,
            ),
            User(
                id=uuid.uuid4(),
                email="admin@donehr.com",
                password_hash=hash_password("Admin@1234!"),
                full_name="System Admin",
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
            ),
            User(
                id=uuid.uuid4(),
                email="hr@donehr.com",
                password_hash=hash_password("Hr@123456!"),
                full_name="Demo HR Manager",
                role=UserRole.HR_ADMIN,
                is_active=True,
                is_verified=True,
            ),
            User(
                id=uuid.uuid4(),
                email="candidate@donehr.com",
                password_hash=hash_password("Candidate@1!"),
                full_name="Demo Candidate",
                role=UserRole.CANDIDATE,
                is_active=True,
                is_verified=True,
            ),
        ]

        session.add_all(users_to_create)
        await session.commit()
        log.info("seed_complete", users_created=len(users_to_create))
        for u in users_to_create:
            log.info("seed_user", email=u.email, role=u.role.value)


if __name__ == "__main__":
    asyncio.run(seed())
