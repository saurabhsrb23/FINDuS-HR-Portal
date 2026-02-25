"""Application business logic — apply, search jobs, track, alerts."""
from __future__ import annotations

import uuid

import structlog
from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus, JobAlert
from app.models.company import Company
from app.models.job import Job, JobStatus
from app.repositories.application_repository import ApplicationRepository
from app.repositories.candidate_repository import CandidateRepository
from app.schemas.application import (
    ApplyRequest,
    ApplicationListItem,
    ApplicationResponse,
    JobAlertCreate,
    JobAlertResponse,
    SalaryBenchmark,
)

log = structlog.get_logger("donehr.application_service")

# ── Static salary benchmark data (INR, 2025) ──────────────────────────────────
_SALARY_DATA: list[dict] = [
    {"role": "Software Engineer", "location": "Bangalore", "min": 600000, "median": 1200000, "max": 2500000},
    {"role": "Software Engineer", "location": "Mumbai", "min": 550000, "median": 1100000, "max": 2200000},
    {"role": "Software Engineer", "location": "Delhi", "min": 500000, "median": 1000000, "max": 2000000},
    {"role": "Software Engineer", "location": "Hyderabad", "min": 550000, "median": 1100000, "max": 2100000},
    {"role": "Senior Software Engineer", "location": "Bangalore", "min": 1200000, "median": 2200000, "max": 4000000},
    {"role": "Senior Software Engineer", "location": "Mumbai", "min": 1100000, "median": 2000000, "max": 3800000},
    {"role": "Data Scientist", "location": "Bangalore", "min": 800000, "median": 1600000, "max": 3500000},
    {"role": "Data Scientist", "location": "Mumbai", "min": 750000, "median": 1500000, "max": 3200000},
    {"role": "Product Manager", "location": "Bangalore", "min": 1200000, "median": 2500000, "max": 5000000},
    {"role": "Product Manager", "location": "Mumbai", "min": 1100000, "median": 2300000, "max": 4500000},
    {"role": "DevOps Engineer", "location": "Bangalore", "min": 700000, "median": 1400000, "max": 2800000},
    {"role": "DevOps Engineer", "location": "Hyderabad", "min": 650000, "median": 1300000, "max": 2600000},
    {"role": "UX Designer", "location": "Bangalore", "min": 500000, "median": 1000000, "max": 2000000},
    {"role": "UX Designer", "location": "Mumbai", "min": 450000, "median": 900000, "max": 1800000},
    {"role": "HR Manager", "location": "Bangalore", "min": 500000, "median": 900000, "max": 1800000},
    {"role": "HR Manager", "location": "Delhi", "min": 450000, "median": 850000, "max": 1600000},
    {"role": "Marketing Manager", "location": "Mumbai", "min": 600000, "median": 1200000, "max": 2500000},
    {"role": "Sales Manager", "location": "Mumbai", "min": 550000, "median": 1100000, "max": 2200000},
    {"role": "Frontend Developer", "location": "Bangalore", "min": 500000, "median": 1000000, "max": 2200000},
    {"role": "Backend Developer", "location": "Bangalore", "min": 600000, "median": 1200000, "max": 2500000},
    {"role": "Full Stack Developer", "location": "Bangalore", "min": 700000, "median": 1400000, "max": 2800000},
    {"role": "Machine Learning Engineer", "location": "Bangalore", "min": 1000000, "median": 2000000, "max": 4000000},
]


class ApplicationService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = ApplicationRepository(db)
        self._candidate_repo = CandidateRepository(db)
        self._db = db

    # ── Job search ────────────────────────────────────────────────────────────

    async def search_jobs(
        self,
        q: str | None = None,
        location: str | None = None,
        job_type: str | None = None,
        salary_min: int | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """Search active jobs with basic text filtering."""
        stmt = select(Job).where(Job.status == JobStatus.ACTIVE)

        if q:
            search = f"%{q.lower()}%"
            stmt = stmt.where(
                or_(
                    Job.title.ilike(search),
                    Job.description.ilike(search),
                    Job.location.ilike(search),
                )
            )
        if location:
            stmt = stmt.where(Job.location.ilike(f"%{location}%"))
        if job_type:
            stmt = stmt.where(Job.job_type == job_type)
        if salary_min:
            stmt = stmt.where(Job.salary_max >= salary_min)

        # Count total
        count_result = await self._db.execute(
            select(Job.id).where(stmt.whereclause)  # type: ignore[arg-type]
        )
        total = len(count_result.scalars().all())

        # Paginate
        stmt = stmt.order_by(Job.created_at.desc()).offset((page - 1) * limit).limit(limit)
        result = await self._db.execute(stmt)
        jobs = list(result.scalars().all())

        return {
            "items": jobs,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if total else 0,
        }

    async def get_job_detail(self, job_id: uuid.UUID) -> Job:
        result = await self._db.execute(
            select(Job).where(Job.id == job_id, Job.status == JobStatus.ACTIVE)
        )
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found or not active.")
        return job

    # ── Apply ─────────────────────────────────────────────────────────────────

    async def apply(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        data: ApplyRequest,
    ) -> Application:
        # Get candidate profile
        profile = await self._candidate_repo.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Candidate profile not found. Please complete your profile first.")

        # Check job is active
        result = await self._db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")
        if job.status != JobStatus.ACTIVE:
            raise HTTPException(status_code=422, detail="This job is not accepting applications.")

        # Duplicate prevention
        existing = await self._repo.get_by_job_and_candidate(job_id, profile.id)
        if existing:
            raise HTTPException(status_code=409, detail="You have already applied to this job.")

        # Create application using candidate's resume if available
        application = await self._repo.create(
            job_id=job_id,
            candidate_id=profile.id,
            data=data,
            resume_url=profile.resume_url,
        )
        await self._db.commit()
        await self._db.refresh(application)
        log.info("application_submitted", user_id=str(user_id), job_id=str(job_id))

        # Real-time event: notify HR that a new application arrived
        try:
            from app.core.event_emitter import emit_event
            await emit_event(
                "new_application",
                {
                    "application_id": str(application.id),
                    "job_id": str(job_id),
                    "candidate_id": str(profile.id),
                    "candidate_name": profile.full_name,
                },
                target_role="hr_all",
            )
        except Exception:
            pass

        return application

    # ── My applications ───────────────────────────────────────────────────────

    async def get_my_applications(self, user_id: uuid.UUID) -> list[ApplicationListItem]:
        profile = await self._candidate_repo.get_by_user_id(user_id)
        if not profile:
            return []

        applications = await self._repo.get_by_candidate(profile.id)

        items: list[ApplicationListItem] = []
        for app in applications:
            # Join job + company details
            job_result = await self._db.execute(
                select(Job, Company.name.label("company_name"))
                .outerjoin(Company, Job.company_id == Company.id)
                .where(Job.id == app.job_id)
            )
            row = job_result.first()
            job = row[0] if row else None
            company_name = row[1] if row else None
            items.append(
                ApplicationListItem(
                    id=app.id,
                    job_id=app.job_id,
                    status=app.status,
                    applied_at=app.applied_at,
                    updated_at=app.updated_at,
                    job_title=job.title if job else None,
                    company_name=company_name,
                    job_location=job.location if job else None,
                )
            )
        return items

    async def get_application_detail(self, user_id: uuid.UUID, app_id: uuid.UUID) -> Application:
        profile = await self._candidate_repo.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found.")
        app = await self._repo.get_by_id(app_id)
        if not app or app.candidate_id != profile.id:
            raise HTTPException(status_code=404, detail="Application not found.")
        return app

    async def withdraw(self, user_id: uuid.UUID, app_id: uuid.UUID) -> Application:
        profile = await self._candidate_repo.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found.")
        app = await self._repo.get_by_id(app_id)
        if not app or app.candidate_id != profile.id:
            raise HTTPException(status_code=404, detail="Application not found.")
        if app.status == ApplicationStatus.WITHDRAWN:
            raise HTTPException(status_code=422, detail="Application already withdrawn.")
        if app.status in (ApplicationStatus.HIRED, ApplicationStatus.REJECTED):
            raise HTTPException(status_code=422, detail="Cannot withdraw a closed application.")
        app = await self._repo.withdraw(app)
        await self._db.commit()
        await self._db.refresh(app)
        return app

    # ── Recommendations ───────────────────────────────────────────────────────

    async def get_recommendations(self, user_id: uuid.UUID, limit: int = 10) -> list[Job]:
        """Basic skill-based job recommendations."""
        profile = await self._candidate_repo.get_by_user_id(user_id)
        if not profile or not profile.skills:
            # Fallback: return recent active jobs
            result = await self._db.execute(
                select(Job)
                .where(Job.status == JobStatus.ACTIVE)
                .order_by(Job.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

        # Match by skill keywords in job title/description
        skill_names = [s.skill_name.lower() for s in profile.skills]
        conditions = [Job.title.ilike(f"%{sk}%") for sk in skill_names] + \
                     [Job.description.ilike(f"%{sk}%") for sk in skill_names]

        result = await self._db.execute(
            select(Job)
            .where(Job.status == JobStatus.ACTIVE, or_(*conditions))
            .order_by(Job.created_at.desc())
            .limit(limit)
        )
        jobs = list(result.scalars().all())

        # Top up with recent jobs if not enough
        if len(jobs) < limit:
            seen_ids = {j.id for j in jobs}
            fallback = await self._db.execute(
                select(Job)
                .where(Job.status == JobStatus.ACTIVE, Job.id.not_in(seen_ids))
                .order_by(Job.created_at.desc())
                .limit(limit - len(jobs))
            )
            jobs += list(fallback.scalars().all())

        return jobs

    # ── Salary benchmark ──────────────────────────────────────────────────────

    def get_salary_benchmark(self, role: str | None = None, location: str | None = None) -> list[SalaryBenchmark]:
        results = _SALARY_DATA
        if role:
            results = [r for r in results if role.lower() in r["role"].lower()]
        if location:
            results = [r for r in results if location.lower() in r["location"].lower()]
        if not results:
            results = _SALARY_DATA[:5]  # Return first 5 as fallback
        return [
            SalaryBenchmark(
                role=r["role"],
                location=r["location"],
                min_salary=r["min"],
                median_salary=r["median"],
                max_salary=r["max"],
            )
            for r in results[:10]
        ]

    # ── Job alerts ────────────────────────────────────────────────────────────

    async def create_alert(self, user_id: uuid.UUID, data: JobAlertCreate) -> JobAlert:
        profile = await self._candidate_repo.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found.")
        alert = await self._repo.create_alert(profile.id, data)
        await self._db.commit()
        await self._db.refresh(alert)
        return alert

    async def get_alerts(self, user_id: uuid.UUID) -> list[JobAlert]:
        profile = await self._candidate_repo.get_by_user_id(user_id)
        if not profile:
            return []
        return await self._repo.get_alerts_by_candidate(profile.id)

    async def delete_alert(self, user_id: uuid.UUID, alert_id: uuid.UUID) -> None:
        profile = await self._candidate_repo.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found.")
        alert = await self._repo.get_alert_by_id(alert_id)
        if not alert or alert.candidate_id != profile.id:
            raise HTTPException(status_code=404, detail="Alert not found.")
        await self._repo.delete_alert(alert)
        await self._db.commit()
