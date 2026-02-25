"""Candidate profile business logic."""
from __future__ import annotations

import io
import uuid

import structlog
from fastapi import HTTPException, UploadFile

from app.models.candidate import CandidateProfile
from app.repositories.candidate_repository import CandidateRepository
from app.schemas.candidate import (
    CandidateProfileUpdate,
    CandidateSkillCreate,
    CertificationCreate,
    EducationCreate,
    ProfileStrengthResponse,
    ProjectCreate,
    WorkExperienceCreate,
)

log = structlog.get_logger("donehr.candidate_service")

MAX_RESUME_SIZE = 5 * 1024 * 1024  # 5 MB
PDF_MAGIC = b"%PDF"


class CandidateService:
    def __init__(self, db) -> None:
        self._repo = CandidateRepository(db)
        self._db = db

    # ── Profile ──────────────────────────────────────────────────────────────

    async def get_or_create_profile(self, user_id: uuid.UUID) -> CandidateProfile:
        profile = await self._repo.get_by_user_id(user_id)
        if not profile:
            profile = await self._repo.create_profile(user_id)
            await self._db.commit()
            await self._db.refresh(profile)
        return profile

    async def get_profile(self, user_id: uuid.UUID) -> CandidateProfile:
        profile = await self._repo.get_by_user_id(user_id)
        if not profile:
            profile = await self._repo.create_profile(user_id)
            await self._db.commit()
            await self._db.refresh(profile)
        return profile

    async def update_profile(self, user_id: uuid.UUID, data: CandidateProfileUpdate) -> CandidateProfile:
        profile = await self.get_profile(user_id)
        profile = await self._repo.update_profile(profile, data)
        await self._recalc_strength(profile)
        await self._db.commit()
        await self._db.refresh(profile)
        return profile

    # ── Resume upload ─────────────────────────────────────────────────────────

    async def upload_resume(self, user_id: uuid.UUID, file: UploadFile) -> CandidateProfile:
        # Validate filename
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=422, detail="Only PDF files are allowed.")

        content = await file.read()

        # Size check
        if len(content) > MAX_RESUME_SIZE:
            raise HTTPException(status_code=422, detail="Resume must be smaller than 5 MB.")

        # Magic bytes check
        if not content.startswith(PDF_MAGIC):
            raise HTTPException(status_code=422, detail="File does not appear to be a valid PDF.")

        # In production: upload to S3/GCS. For now, store as base64 data URL.
        import base64
        data_url = f"data:application/pdf;base64,{base64.b64encode(content).decode()}"

        profile = await self.get_profile(user_id)
        profile = await self._repo.set_resume(profile, data_url, file.filename)
        await self._recalc_strength(profile)
        await self._db.commit()
        await self._db.refresh(profile)
        log.info("resume_uploaded", user_id=str(user_id), filename=file.filename)
        return profile

    # ── Profile strength ──────────────────────────────────────────────────────

    async def get_profile_strength(self, user_id: uuid.UUID) -> ProfileStrengthResponse:
        profile = await self.get_profile(user_id)
        return self._calc_strength(profile)

    def _calc_strength(self, profile: CandidateProfile) -> ProfileStrengthResponse:
        breakdown: dict[str, int] = {}
        tips: list[str] = []

        # Basic info (25 pts)
        basic = 0
        if profile.full_name: basic += 5
        if profile.phone: basic += 5
        if profile.location: basic += 5
        if profile.headline: basic += 5
        if profile.summary: basic += 5
        breakdown["basic_info"] = basic
        if basic < 25:
            tips.append("Complete your basic info (name, phone, location, headline, summary)")

        # Resume (20 pts)
        resume_score = 20 if profile.resume_url else 0
        breakdown["resume"] = resume_score
        if not profile.resume_url:
            tips.append("Upload your resume to increase visibility by 3x")

        # Work experience (20 pts)
        exp_score = min(20, len(profile.work_experiences) * 10)
        breakdown["work_experience"] = exp_score
        if exp_score < 20:
            tips.append("Add at least 2 work experiences")

        # Education (10 pts)
        edu_score = min(10, len(profile.educations) * 10)
        breakdown["education"] = edu_score
        if edu_score < 10:
            tips.append("Add your education details")

        # Skills (15 pts)
        skill_score = min(15, len(profile.skills) * 3)
        breakdown["skills"] = skill_score
        if skill_score < 15:
            tips.append("Add at least 5 key skills")

        # Certifications (5 pts)
        cert_score = min(5, len(profile.certifications) * 5)
        breakdown["certifications"] = cert_score
        if cert_score < 5:
            tips.append("Add certifications to stand out")

        # Projects (5 pts)
        proj_score = min(5, len(profile.projects) * 5)
        breakdown["projects"] = proj_score
        if proj_score < 5:
            tips.append("Showcase your projects")

        total = sum(breakdown.values())
        return ProfileStrengthResponse(score=total, breakdown=breakdown, tips=tips[:3])

    async def _recalc_strength(self, profile: CandidateProfile) -> None:
        result = self._calc_strength(profile)
        await self._repo.set_profile_strength(profile, result.score)

    # ── Work Experience ───────────────────────────────────────────────────────

    async def add_work_experience(self, user_id: uuid.UUID, data: WorkExperienceCreate):
        profile = await self.get_profile(user_id)
        exp = await self._repo.add_work_experience(profile.id, data)
        await self._recalc_strength(profile)
        await self._db.commit()
        await self._db.refresh(exp)
        return exp

    async def delete_work_experience(self, user_id: uuid.UUID, exp_id: uuid.UUID) -> None:
        profile = await self.get_profile(user_id)
        exp = await self._repo.get_work_experience(exp_id)
        if not exp or exp.candidate_id != profile.id:
            raise HTTPException(status_code=404, detail="Work experience not found.")
        await self._repo.delete_work_experience(exp)
        await self._recalc_strength(profile)
        await self._db.commit()

    # ── Education ────────────────────────────────────────────────────────────

    async def add_education(self, user_id: uuid.UUID, data: EducationCreate):
        profile = await self.get_profile(user_id)
        edu = await self._repo.add_education(profile.id, data)
        await self._recalc_strength(profile)
        await self._db.commit()
        await self._db.refresh(edu)
        return edu

    async def delete_education(self, user_id: uuid.UUID, edu_id: uuid.UUID) -> None:
        profile = await self.get_profile(user_id)
        edu = await self._repo.get_education(edu_id)
        if not edu or edu.candidate_id != profile.id:
            raise HTTPException(status_code=404, detail="Education not found.")
        await self._repo.delete_education(edu)
        await self._recalc_strength(profile)
        await self._db.commit()

    # ── Certifications ────────────────────────────────────────────────────────

    async def add_certification(self, user_id: uuid.UUID, data: CertificationCreate):
        profile = await self.get_profile(user_id)
        cert = await self._repo.add_certification(profile.id, data)
        await self._recalc_strength(profile)
        await self._db.commit()
        await self._db.refresh(cert)
        return cert

    async def delete_certification(self, user_id: uuid.UUID, cert_id: uuid.UUID) -> None:
        profile = await self.get_profile(user_id)
        from sqlalchemy import select
        from app.models.candidate import Certification
        result = await self._db.execute(select(Certification).where(Certification.id == cert_id))
        cert = result.scalar_one_or_none()
        if not cert or cert.candidate_id != profile.id:
            raise HTTPException(status_code=404, detail="Certification not found.")
        await self._repo.delete_certification(cert)
        await self._recalc_strength(profile)
        await self._db.commit()

    # ── Projects ─────────────────────────────────────────────────────────────

    async def add_project(self, user_id: uuid.UUID, data: ProjectCreate):
        profile = await self.get_profile(user_id)
        proj = await self._repo.add_project(profile.id, data)
        await self._recalc_strength(profile)
        await self._db.commit()
        await self._db.refresh(proj)
        return proj

    async def delete_project(self, user_id: uuid.UUID, proj_id: uuid.UUID) -> None:
        profile = await self.get_profile(user_id)
        from sqlalchemy import select
        from app.models.candidate import Project
        result = await self._db.execute(select(Project).where(Project.id == proj_id))
        proj = result.scalar_one_or_none()
        if not proj or proj.candidate_id != profile.id:
            raise HTTPException(status_code=404, detail="Project not found.")
        await self._repo.delete_project(proj)
        await self._recalc_strength(profile)
        await self._db.commit()

    # ── Skills ───────────────────────────────────────────────────────────────

    async def add_skill(self, user_id: uuid.UUID, data: CandidateSkillCreate):
        profile = await self.get_profile(user_id)
        skill = await self._repo.add_skill(profile.id, data)
        await self._recalc_strength(profile)
        await self._db.commit()
        await self._db.refresh(skill)
        return skill

    async def delete_skill(self, user_id: uuid.UUID, skill_id: uuid.UUID) -> None:
        profile = await self.get_profile(user_id)
        from sqlalchemy import select
        from app.models.candidate import CandidateSkill
        result = await self._db.execute(select(CandidateSkill).where(CandidateSkill.id == skill_id))
        skill = result.scalar_one_or_none()
        if not skill or skill.candidate_id != profile.id:
            raise HTTPException(status_code=404, detail="Skill not found.")
        await self._repo.delete_skill(skill)
        await self._recalc_strength(profile)
        await self._db.commit()
