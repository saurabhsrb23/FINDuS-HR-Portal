"""Candidate profile repository — DB access layer."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import (
    CandidateProfile,
    CandidateSkill,
    Certification,
    Education,
    Project,
    WorkExperience,
)
from app.schemas.candidate import (
    CandidateProfileUpdate,
    CandidateSkillCreate,
    CertificationCreate,
    EducationCreate,
    ProjectCreate,
    WorkExperienceCreate,
)


class CandidateRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Profile ──────────────────────────────────────────────────────────────

    async def get_by_user_id(self, user_id: uuid.UUID) -> CandidateProfile | None:
        result = await self._db.execute(
            select(CandidateProfile).where(CandidateProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, profile_id: uuid.UUID) -> CandidateProfile | None:
        result = await self._db.execute(
            select(CandidateProfile).where(CandidateProfile.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def create_profile(self, user_id: uuid.UUID) -> CandidateProfile:
        profile = CandidateProfile(user_id=user_id)
        self._db.add(profile)
        await self._db.flush()
        await self._db.refresh(profile)
        return profile

    async def update_profile(self, profile: CandidateProfile, data: CandidateProfileUpdate) -> CandidateProfile:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        await self._db.flush()
        await self._db.refresh(profile)
        return profile

    async def set_resume(self, profile: CandidateProfile, url: str, filename: str) -> CandidateProfile:
        profile.resume_url = url
        profile.resume_filename = filename
        await self._db.flush()
        await self._db.refresh(profile)
        return profile

    async def set_profile_strength(self, profile: CandidateProfile, score: int) -> None:
        profile.profile_strength = score
        await self._db.flush()

    # ── Work Experiences ─────────────────────────────────────────────────────

    async def add_work_experience(self, profile_id: uuid.UUID, data: WorkExperienceCreate) -> WorkExperience:
        exp = WorkExperience(candidate_id=profile_id, **data.model_dump())
        self._db.add(exp)
        await self._db.flush()
        await self._db.refresh(exp)
        return exp

    async def get_work_experience(self, exp_id: uuid.UUID) -> WorkExperience | None:
        result = await self._db.execute(
            select(WorkExperience).where(WorkExperience.id == exp_id)
        )
        return result.scalar_one_or_none()

    async def delete_work_experience(self, exp: WorkExperience) -> None:
        await self._db.delete(exp)
        await self._db.flush()

    # ── Education ────────────────────────────────────────────────────────────

    async def add_education(self, profile_id: uuid.UUID, data: EducationCreate) -> Education:
        edu = Education(candidate_id=profile_id, **data.model_dump())
        self._db.add(edu)
        await self._db.flush()
        await self._db.refresh(edu)
        return edu

    async def get_education(self, edu_id: uuid.UUID) -> Education | None:
        result = await self._db.execute(
            select(Education).where(Education.id == edu_id)
        )
        return result.scalar_one_or_none()

    async def delete_education(self, edu: Education) -> None:
        await self._db.delete(edu)
        await self._db.flush()

    # ── Certifications ───────────────────────────────────────────────────────

    async def add_certification(self, profile_id: uuid.UUID, data: CertificationCreate) -> Certification:
        cert = Certification(candidate_id=profile_id, **data.model_dump())
        self._db.add(cert)
        await self._db.flush()
        await self._db.refresh(cert)
        return cert

    async def delete_certification(self, cert: Certification) -> None:
        await self._db.delete(cert)
        await self._db.flush()

    # ── Projects ─────────────────────────────────────────────────────────────

    async def add_project(self, profile_id: uuid.UUID, data: ProjectCreate) -> Project:
        proj = Project(candidate_id=profile_id, **data.model_dump())
        self._db.add(proj)
        await self._db.flush()
        await self._db.refresh(proj)
        return proj

    async def delete_project(self, proj: Project) -> None:
        await self._db.delete(proj)
        await self._db.flush()

    # ── Skills ───────────────────────────────────────────────────────────────

    async def add_skill(self, profile_id: uuid.UUID, data: CandidateSkillCreate) -> CandidateSkill:
        skill = CandidateSkill(candidate_id=profile_id, **data.model_dump())
        self._db.add(skill)
        await self._db.flush()
        await self._db.refresh(skill)
        return skill

    async def delete_skill(self, skill: CandidateSkill) -> None:
        await self._db.delete(skill)
        await self._db.flush()
