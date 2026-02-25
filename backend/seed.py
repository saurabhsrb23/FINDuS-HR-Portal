"""Bootstrap seed data — idempotent, run anytime.
Module 10: seed4() fills every remaining table with 10 records."""
from __future__ import annotations

import asyncio
import uuid
from datetime import date, datetime, timezone

import structlog
from sqlalchemy import func, select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.company import Company
from app.models.job import Job, JobStatus, JobType, PipelineStage, JobSkill, JobQuestion, QuestionType
from app.models.candidate import (
    CandidateProfile, WorkExperience, Education, CandidateSkill,
    Certification, Project,
)
from app.models.application import Application, ApplicationStatus, JobAlert
from app.models.ai_summary import AISummary, SummaryType
from app.models.saved_search import SavedSearch, TalentPool, TalentPoolCandidate, SearchAnalytic
from app.models.audit_log import AuditLog
from app.models.admin import AdminUser, AdminRole, PlatformEvent
from app.models.chat import (
    ChatConversation, ConversationParticipant, ChatMessage, ChatMessageRead,
    ChatReaction, ChatReport, ConversationType, MessageType, ReportStatus,
)

log = structlog.get_logger("seed")

# ── Fixed UUIDs ────────────────────────────────────────────────────────────────
U_ELITE  = uuid.UUID("00000000-0000-0000-0000-000000000001")
U_ADMIN  = uuid.UUID("00000000-0000-0000-0000-000000000002")
U_HR     = uuid.UUID("00000000-0000-0000-0000-000000000003")
U_CAND   = uuid.UUID("00000000-0000-0000-0000-000000000004")
U_HR2    = uuid.UUID("00000000-0000-0000-0000-000000000005")
U_HR3    = uuid.UUID("00000000-0000-0000-0000-000000000006")
U_HR4    = uuid.UUID("00000000-0000-0000-0000-000000000007")
U_HR5    = uuid.UUID("00000000-0000-0000-0000-000000000008")
U_HR6    = uuid.UUID("00000000-0000-0000-0000-000000000009")
U_DEV1   = uuid.UUID("00000000-0000-0000-0000-000000000011")
U_DEV2   = uuid.UUID("00000000-0000-0000-0000-000000000012")
U_DEV3   = uuid.UUID("00000000-0000-0000-0000-000000000013")
U_DEV4   = uuid.UUID("00000000-0000-0000-0000-000000000014")
U_DEV5   = uuid.UUID("00000000-0000-0000-0000-000000000015")
U_DEV6   = uuid.UUID("00000000-0000-0000-0000-000000000016")
U_DEV7   = uuid.UUID("00000000-0000-0000-0000-000000000017")
U_DEV8   = uuid.UUID("00000000-0000-0000-0000-000000000018")
U_DEV9   = uuid.UUID("00000000-0000-0000-0000-000000000019")
U_DEV10  = uuid.UUID("00000000-0000-0000-0000-000000000020")

C_TCS       = uuid.UUID("00000000-0000-0000-0001-000000000001")
C_INFOSYS   = uuid.UUID("00000000-0000-0000-0001-000000000002")
C_WIPRO     = uuid.UUID("00000000-0000-0000-0001-000000000003")
C_HCL       = uuid.UUID("00000000-0000-0000-0001-000000000004")
C_ACCENTURE = uuid.UUID("00000000-0000-0000-0001-000000000005")

J1  = uuid.UUID("00000000-0000-0000-0002-000000000001")
J2  = uuid.UUID("00000000-0000-0000-0002-000000000002")
J3  = uuid.UUID("00000000-0000-0000-0002-000000000003")
J4  = uuid.UUID("00000000-0000-0000-0002-000000000004")
J5  = uuid.UUID("00000000-0000-0000-0002-000000000005")
J6  = uuid.UUID("00000000-0000-0000-0002-000000000006")
J7  = uuid.UUID("00000000-0000-0000-0002-000000000007")
J8  = uuid.UUID("00000000-0000-0000-0002-000000000008")
J9  = uuid.UUID("00000000-0000-0000-0002-000000000009")
J10 = uuid.UUID("00000000-0000-0000-0002-000000000010")

CP0  = uuid.UUID("00000000-0000-0000-0003-000000000000")
CP1  = uuid.UUID("00000000-0000-0000-0003-000000000001")
CP2  = uuid.UUID("00000000-0000-0000-0003-000000000002")
CP3  = uuid.UUID("00000000-0000-0000-0003-000000000003")
CP4  = uuid.UUID("00000000-0000-0000-0003-000000000004")
CP5  = uuid.UUID("00000000-0000-0000-0003-000000000005")
CP6  = uuid.UUID("00000000-0000-0000-0003-000000000006")
CP7  = uuid.UUID("00000000-0000-0000-0003-000000000007")
CP8  = uuid.UUID("00000000-0000-0000-0003-000000000008")
CP9  = uuid.UUID("00000000-0000-0000-0003-000000000009")
CP10 = uuid.UUID("00000000-0000-0000-0003-000000000010")

NOW = datetime.now(timezone.utc)


# ── seed1 ──────────────────────────────────────────────────────────────────────
async def seed1(db) -> None:
    count = await db.scalar(select(func.count()).select_from(User))
    if count and count > 0:
        log.info("seed1_skip")
        return

    company = Company(
        id=C_TCS, name="TCS", industry="IT Services",
        size="large", website="https://tcs.com",
    )
    db.add(company)

    users = [
        User(id=U_ELITE, email="elite@donehr.com",       password_hash=hash_password("Elite@Admin1!"),  full_name="Elite Admin",    role=UserRole.ELITE_ADMIN, is_active=True, is_verified=True),
        User(id=U_ADMIN, email="admin@donehr.com",       password_hash=hash_password("Admin@1234!"),    full_name="System Admin",   role=UserRole.ADMIN,       is_active=True, is_verified=True),
        User(id=U_HR,    email="hr@donehr.com",          password_hash=hash_password("Hr@123456!"),     full_name="Priya HR",       role=UserRole.HR_ADMIN,    is_active=True, is_verified=True),
        User(id=U_CAND,  email="candidate@donehr.com",   password_hash=hash_password("Candidate@1!"),   full_name="Demo Candidate", role=UserRole.CANDIDATE,   is_active=True, is_verified=True),
    ]
    for u in users:
        db.add(u)
    await db.commit()
    log.info("seed1_done", users=4)
    print("Seeding base users... done (4 users)")


# ── seed_admin_users ───────────────────────────────────────────────────────────
async def seed_admin_users(db) -> None:
    count = await db.scalar(select(func.count()).select_from(AdminUser))
    if count and count > 0:
        log.info("seed_admin_skip")
        return

    SA_ID = uuid.UUID("00000000-0000-0000-0099-000000000001")
    admins = [
        AdminUser(
            id=SA_ID,
            email="superadmin@donehr.com",
            password_hash=hash_password("SuperAdmin@2024!"),
            pin_hash=hash_password("123456"),
            full_name="Super Admin",
            role=AdminRole.SUPERADMIN,
            is_active=True,
        ),
        AdminUser(
            id=uuid.UUID("00000000-0000-0000-0099-000000000002"),
            email="admin@donehr.com",
            password_hash=hash_password("Admin@2024!"),
            pin_hash=hash_password("654321"),
            full_name="Platform Admin",
            role=AdminRole.ADMIN,
            is_active=True,
        ),
        AdminUser(
            id=uuid.UUID("00000000-0000-0000-0099-000000000003"),
            email="elite@donehr.com",
            password_hash=hash_password("Elite@2024!"),
            pin_hash=hash_password("111111"),
            full_name="Elite Viewer",
            role=AdminRole.ELITE_ADMIN,
            is_active=True,
        ),
    ]
    for a in admins:
        db.add(a)
    await db.commit()
    log.info("seed_admin_done", admins=3)
    print("Seeding admin users... done (3 admin portal users)")


# ── seed2 ──────────────────────────────────────────────────────────────────────
async def seed2(db) -> None:
    count = await db.scalar(select(func.count()).select_from(User))
    if count and count > 10:
        log.info("seed2_skip")
        return

    # 4 more companies
    for company in [
        Company(id=C_INFOSYS,   name="Infosys",           industry="IT Services", size="large", website="https://infosys.com"),
        Company(id=C_WIPRO,     name="Wipro",             industry="IT Services", size="large", website="https://wipro.com"),
        Company(id=C_HCL,       name="HCL Technologies",  industry="IT Services", size="large", website="https://hcl.com"),
        Company(id=C_ACCENTURE, name="Accenture",         industry="Consulting",  size="large", website="https://accenture.com"),
    ]:
        db.add(company)

    # 5 additional HR users
    for u in [
        User(id=U_HR2, email="recruiter1@tcs.com",        password_hash=hash_password("Hr@123456!"), full_name="Anita Sharma",  role=UserRole.RECRUITER,      is_active=True, is_verified=True),
        User(id=U_HR3, email="hiring@infosys.com",        password_hash=hash_password("Hr@123456!"), full_name="Raj Kapoor",    role=UserRole.HIRING_MANAGER, is_active=True, is_verified=True),
        User(id=U_HR4, email="hr2@wipro.com",             password_hash=hash_password("Hr@123456!"), full_name="Meena Patel",   role=UserRole.HR,             is_active=True, is_verified=True),
        User(id=U_HR5, email="talent@hcl.com",            password_hash=hash_password("Hr@123456!"), full_name="Suresh Reddy",  role=UserRole.RECRUITER,      is_active=True, is_verified=True),
        User(id=U_HR6, email="recruiter@accenture.com",   password_hash=hash_password("Hr@123456!"), full_name="Kavita Singh",  role=UserRole.HR_ADMIN,       is_active=True, is_verified=True),
    ]:
        db.add(u)

    # 10 candidate users
    for u in [
        User(id=U_DEV1,  email="arjun.sharma@gmail.com",   password_hash=hash_password("Dev@123456!"), full_name="Arjun Sharma",  role=UserRole.CANDIDATE, is_active=True, is_verified=True),
        User(id=U_DEV2,  email="priya.patel@gmail.com",    password_hash=hash_password("Dev@123456!"), full_name="Priya Patel",   role=UserRole.CANDIDATE, is_active=True, is_verified=True),
        User(id=U_DEV3,  email="rahul.verma@gmail.com",    password_hash=hash_password("Dev@123456!"), full_name="Rahul Verma",   role=UserRole.CANDIDATE, is_active=True, is_verified=True),
        User(id=U_DEV4,  email="sneha.kumar@gmail.com",    password_hash=hash_password("Dev@123456!"), full_name="Sneha Kumar",   role=UserRole.CANDIDATE, is_active=True, is_verified=True),
        User(id=U_DEV5,  email="vikram.singh@gmail.com",   password_hash=hash_password("Dev@123456!"), full_name="Vikram Singh",  role=UserRole.CANDIDATE, is_active=True, is_verified=True),
        User(id=U_DEV6,  email="ananya.roy@gmail.com",     password_hash=hash_password("Dev@123456!"), full_name="Ananya Roy",    role=UserRole.CANDIDATE, is_active=True, is_verified=True),
        User(id=U_DEV7,  email="karthik.nair@gmail.com",   password_hash=hash_password("Dev@123456!"), full_name="Karthik Nair",  role=UserRole.CANDIDATE, is_active=True, is_verified=True),
        User(id=U_DEV8,  email="pooja.desai@gmail.com",    password_hash=hash_password("Dev@123456!"), full_name="Pooja Desai",   role=UserRole.CANDIDATE, is_active=True, is_verified=True),
        User(id=U_DEV9,  email="rohit.gupta@gmail.com",    password_hash=hash_password("Dev@123456!"), full_name="Rohit Gupta",   role=UserRole.CANDIDATE, is_active=True, is_verified=True),
        User(id=U_DEV10, email="divya.menon@gmail.com",    password_hash=hash_password("Dev@123456!"), full_name="Divya Menon",   role=UserRole.CANDIDATE, is_active=True, is_verified=True),
    ]:
        db.add(u)

    await db.flush()

    # 10 jobs
    job_defs = [
        dict(id=J1,  title="Senior Python Developer",   company_id=C_TCS,       posted_by=U_HR,  job_type=JobType.FULL_TIME, location="Bangalore", salary_min=1800000, salary_max=2500000, experience_years_min=4, experience_years_max=8,  description="Build scalable Python microservices using Django and FastAPI."),
        dict(id=J2,  title="React Frontend Engineer",   company_id=C_INFOSYS,   posted_by=U_HR2, job_type=JobType.FULL_TIME, location="Hyderabad", salary_min=1200000, salary_max=2000000, experience_years_min=2, experience_years_max=6,  description="Build modern React SPAs with TypeScript and Next.js."),
        dict(id=J3,  title="DevOps Engineer",           company_id=C_WIPRO,     posted_by=U_HR3, job_type=JobType.FULL_TIME, location="Pune",      salary_min=1500000, salary_max=2200000, experience_years_min=3, experience_years_max=7,  description="Own CI/CD pipelines and AWS cloud infrastructure."),
        dict(id=J4,  title="Data Scientist",            company_id=C_HCL,       posted_by=U_HR4, job_type=JobType.FULL_TIME, location="Bangalore", salary_min=2000000, salary_max=3000000, experience_years_min=3, experience_years_max=8,  description="Build ML models for product analytics and forecasting."),
        dict(id=J5,  title="Java Backend Developer",    company_id=C_ACCENTURE, posted_by=U_HR5, job_type=JobType.FULL_TIME, location="Chennai",   salary_min=1400000, salary_max=2200000, experience_years_min=3, experience_years_max=7,  description="Enterprise Java Spring Boot microservices for banking."),
        dict(id=J6,  title="Full Stack Engineer (MERN)",company_id=C_TCS,       posted_by=U_HR6, job_type=JobType.FULL_TIME, location="Mumbai",    salary_min=1300000, salary_max=2000000, experience_years_min=2, experience_years_max=5,  description="End-to-end feature development on React and Node.js."),
        dict(id=J7,  title="Cloud Architect (AWS)",     company_id=C_INFOSYS,   posted_by=U_HR,  job_type=JobType.FULL_TIME, location="Bangalore", salary_min=2500000, salary_max=3500000, experience_years_min=6, experience_years_max=12, description="Design cloud-native architectures on AWS and Azure."),
        dict(id=J8,  title="Android Developer",         company_id=C_WIPRO,     posted_by=U_HR2, job_type=JobType.FULL_TIME, location="Hyderabad", salary_min=1200000, salary_max=1800000, experience_years_min=2, experience_years_max=5,  description="Kotlin-based Android apps using Jetpack Compose."),
        dict(id=J9,  title="QA Automation Engineer",    company_id=C_HCL,       posted_by=U_HR3, job_type=JobType.FULL_TIME, location="Noida",     salary_min=1000000, salary_max=1600000, experience_years_min=2, experience_years_max=5,  description="Selenium + TestNG automation suite and CI integration."),
        dict(id=J10, title="Product Manager (Tech)",    company_id=C_ACCENTURE, posted_by=U_HR4, job_type=JobType.FULL_TIME, location="Bangalore", salary_min=2200000, salary_max=3200000, experience_years_min=5, experience_years_max=10, description="Lead product roadmap for SaaS platform."),
    ]
    for jd in job_defs:
        db.add(Job(**jd, status=JobStatus.ACTIVE, views_count=0, applications_count=0))

    await db.flush()

    stage_names  = ["Applied", "Screening", "Interview", "Offer", "Hired", "Rejected"]
    stage_colors = ["#6366f1", "#f59e0b", "#3b82f6", "#10b981", "#22c55e", "#ef4444"]
    for jid in [J1,J2,J3,J4,J5,J6,J7,J8,J9,J10]:
        for order, (name, color) in enumerate(zip(stage_names, stage_colors)):
            db.add(PipelineStage(job_id=jid, stage_name=name, stage_order=order, color=color, is_default=True))

    skills_map = {
        J1:  ["Python","Django","FastAPI","PostgreSQL","Docker"],
        J2:  ["React","TypeScript","Next.js","CSS","Redux"],
        J3:  ["Docker","Kubernetes","AWS","CI/CD","Terraform"],
        J4:  ["Python","Machine Learning","TensorFlow","SQL","Statistics"],
        J5:  ["Java","Spring Boot","Microservices","Kafka","MySQL"],
        J6:  ["React","Node.js","MongoDB","Express.js","TypeScript"],
        J7:  ["AWS","Azure","Terraform","Kubernetes","Cloud Architecture"],
        J8:  ["Android","Kotlin","Jetpack Compose","Firebase","REST APIs"],
        J9:  ["Selenium","TestNG","Java","Automation","REST Assured"],
        J10: ["Product Management","Agile","Scrum","Analytics","SQL"],
    }
    for jid, skills in skills_map.items():
        for i, skill in enumerate(skills):
            db.add(JobSkill(job_id=jid, skill_name=skill, is_required=(i < 3)))

    for jid in [J1, J2, J3]:
        db.add(JobQuestion(job_id=jid, question_text="Years of relevant experience?", question_type=QuestionType.TEXT,   is_required=True,  display_order=0))
        db.add(JobQuestion(job_id=jid, question_text="Are you open to relocation?",   question_type=QuestionType.YES_NO, is_required=False, display_order=1))
        db.add(JobQuestion(job_id=jid, question_text="Notice period (days)?",          question_type=QuestionType.TEXT,   is_required=True,  display_order=2))

    await db.flush()

    # 10 candidate profiles
    profile_defs = [
        dict(id=CP1,  user_id=U_DEV1,  full_name="Arjun Sharma",  headline="Senior Python Developer | Django | AWS | 6 Years",    location="Bangalore, India", years_of_experience=6.0,  notice_period_days=30, desired_salary_min=1800000, desired_salary_max=2500000, open_to_remote=True,  profile_strength=92, desired_role="Python Developer",     summary="6-year Python veteran specializing in Django REST APIs and AWS cloud deployments."),
        dict(id=CP2,  user_id=U_DEV2,  full_name="Priya Patel",   headline="React Frontend Engineer | TypeScript | 4 Years",       location="Hyderabad, India", years_of_experience=4.0,  notice_period_days=45, desired_salary_min=1200000, desired_salary_max=1800000, open_to_remote=True,  profile_strength=85, desired_role="Frontend Engineer",    summary="Frontend specialist with deep React and TypeScript experience building responsive SPAs."),
        dict(id=CP3,  user_id=U_DEV3,  full_name="Rahul Verma",   headline="Java Backend Developer | Spring Boot | Microservices",  location="Pune, India",      years_of_experience=5.0,  notice_period_days=60, desired_salary_min=1400000, desired_salary_max=2000000, open_to_remote=False, profile_strength=88, desired_role="Java Developer",       summary="Java backend developer with expertise in Spring Boot microservices and Kafka."),
        dict(id=CP4,  user_id=U_DEV4,  full_name="Sneha Kumar",   headline="Data Scientist | Python | ML | 3 Years",               location="Bangalore, India", years_of_experience=3.0,  notice_period_days=30, desired_salary_min=1600000, desired_salary_max=2200000, open_to_remote=True,  profile_strength=80, desired_role="Data Scientist",       summary="Data scientist building ML models for product analytics using TensorFlow and Pandas."),
        dict(id=CP5,  user_id=U_DEV5,  full_name="Vikram Singh",  headline="DevOps Engineer | AWS | Kubernetes | 5 Years",         location="Chennai, India",   years_of_experience=5.0,  notice_period_days=30, desired_salary_min=1700000, desired_salary_max=2300000, open_to_remote=True,  profile_strength=90, desired_role="DevOps Engineer",      summary="DevOps engineer managing AWS EKS clusters and building CI/CD pipelines for 500+ services."),
        dict(id=CP6,  user_id=U_DEV6,  full_name="Ananya Roy",    headline="Full Stack MERN Developer | 4 Years",                  location="Mumbai, India",    years_of_experience=4.0,  notice_period_days=15, desired_salary_min=1300000, desired_salary_max=1900000, open_to_remote=True,  profile_strength=82, desired_role="Full Stack Developer", summary="Full stack MERN developer delivering end-to-end features from React UI to Node.js APIs."),
        dict(id=CP7,  user_id=U_DEV7,  full_name="Karthik Nair",  headline="Cloud Architect | AWS Certified | 8 Years",            location="Bangalore, India", years_of_experience=8.0,  notice_period_days=60, desired_salary_min=2500000, desired_salary_max=3500000, open_to_remote=True,  profile_strength=95, desired_role="Cloud Architect",      summary="AWS certified cloud architect with 8 years designing enterprise multi-region cloud solutions."),
        dict(id=CP8,  user_id=U_DEV8,  full_name="Pooja Desai",   headline="Android Developer | Kotlin | Jetpack | 3 Years",       location="Hyderabad, India", years_of_experience=3.0,  notice_period_days=30, desired_salary_min=1200000, desired_salary_max=1700000, open_to_remote=False, profile_strength=78, desired_role="Android Developer",    summary="Android developer with 3 production apps on Play Store using Kotlin and Jetpack Compose."),
        dict(id=CP9,  user_id=U_DEV9,  full_name="Rohit Gupta",   headline="QA Automation Engineer | Selenium | 4 Years",          location="Noida, India",     years_of_experience=4.0,  notice_period_days=30, desired_salary_min=1100000, desired_salary_max=1600000, open_to_remote=True,  profile_strength=75, desired_role="QA Engineer",          summary="QA automation specialist who automated 85% of regression suites with Selenium and TestNG."),
        dict(id=CP10, user_id=U_DEV10, full_name="Divya Menon",   headline="Product Manager | Agile | SaaS | 6 Years",             location="Bangalore, India", years_of_experience=6.0,  notice_period_days=45, desired_salary_min=2200000, desired_salary_max=3000000, open_to_remote=True,  profile_strength=88, desired_role="Product Manager",      summary="Product manager with MBA from IIM-A who has launched 5 successful SaaS products."),
    ]
    for pd in profile_defs:
        db.add(CandidateProfile(**pd))

    await db.flush()

    skills_data = [
        (CP1,  [("Python",5,6.0),("Django",5,5.0),("FastAPI",4,3.0),("AWS",4,4.0),("PostgreSQL",4,5.0),("Docker",4,4.0)]),
        (CP2,  [("React",5,4.0),("TypeScript",4,3.0),("Next.js",4,2.0),("CSS",4,4.0),("Redux",3,3.0),("JavaScript",5,5.0)]),
        (CP3,  [("Java",5,5.0),("Spring Boot",5,4.0),("Microservices",4,3.0),("Kafka",3,2.0),("MySQL",4,5.0),("Docker",3,2.0)]),
        (CP4,  [("Python",5,3.0),("Machine Learning",4,3.0),("TensorFlow",3,2.0),("SQL",4,3.0),("Pandas",5,3.0),("Scikit-learn",4,2.0)]),
        (CP5,  [("Docker",5,5.0),("Kubernetes",5,4.0),("AWS",5,5.0),("Terraform",4,3.0),("CI/CD",5,5.0),("Linux",5,5.0)]),
        (CP6,  [("React",4,4.0),("Node.js",4,4.0),("MongoDB",4,3.0),("Express.js",4,3.0),("TypeScript",3,2.0),("REST APIs",4,4.0)]),
        (CP7,  [("AWS",5,8.0),("Azure",4,5.0),("Terraform",5,6.0),("Kubernetes",5,5.0),("Cloud Architecture",5,8.0),("Python",4,5.0)]),
        (CP8,  [("Android",5,3.0),("Kotlin",5,3.0),("Jetpack Compose",4,2.0),("Firebase",4,2.0),("REST APIs",3,3.0),("Java",3,2.0)]),
        (CP9,  [("Selenium",5,4.0),("TestNG",4,3.0),("Java",4,4.0),("REST Assured",4,3.0),("Automation",5,4.0),("Postman",4,4.0)]),
        (CP10, [("Product Management",5,6.0),("Agile",5,5.0),("Scrum",5,5.0),("SQL",3,3.0),("Analytics",4,4.0),("JIRA",4,5.0)]),
    ]
    for cp_id, skills in skills_data:
        for skill_name, proficiency, years_exp in skills:
            db.add(CandidateSkill(candidate_id=cp_id, skill_name=skill_name, proficiency=proficiency, years_exp=years_exp))

    work_data = [
        (CP1,  "Infosys",    "Python Developer",     "2020-01-01", None,         True,  "Built Django REST APIs serving 1M+ req/day"),
        (CP2,  "Wipro",      "Frontend Developer",   "2020-06-01", None,         True,  "Led React migration of legacy Angular app"),
        (CP3,  "TCS",        "Java Developer",       "2019-03-01", None,         True,  "Maintained Spring Boot microservices for banking"),
        (CP4,  "HCL",        "Data Analyst",         "2021-07-01", None,         True,  "Built ML pipeline for churn prediction"),
        (CP5,  "Accenture",  "DevOps Engineer",      "2019-09-01", None,         True,  "Managed AWS EKS clusters for 500+ services"),
        (CP6,  "Infosys",    "Full Stack Dev",       "2020-11-01", None,         True,  "Delivered MERN stack e-commerce platform"),
        (CP7,  "TCS",        "Cloud Engineer",       "2016-04-01", "2021-04-01", False, "Designed multi-region AWS architecture"),
        (CP8,  "Wipro",      "Android Developer",    "2021-01-01", None,         True,  "Published 3 apps on Play Store"),
        (CP9,  "HCL",        "QA Engineer",          "2020-08-01", None,         True,  "Automated 85% of regression test suite"),
        (CP10, "Accenture",  "Product Manager",      "2018-05-01", None,         True,  "Launched 5 SaaS products from 0 to 1"),
    ]
    for cp_id, company, title, start, end, is_cur, desc in work_data:
        db.add(WorkExperience(
            candidate_id=cp_id, company_name=company, job_title=title,
            start_date=date.fromisoformat(start),
            end_date=date.fromisoformat(end) if end else None,
            is_current=is_cur, description=desc,
        ))

    edu_data = [
        (CP1,  "IIT Bombay",          "B.Tech", "Computer Science",        2014, 2018, "8.5 CGPA"),
        (CP2,  "BITS Pilani",         "B.E.",   "Computer Science",        2016, 2020, "8.2 CGPA"),
        (CP3,  "VIT Vellore",         "B.Tech", "Information Technology",  2015, 2019, "8.0 CGPA"),
        (CP4,  "IIT Delhi",           "M.Tech", "Data Science",            2018, 2020, "9.1 CGPA"),
        (CP5,  "NIT Trichy",          "B.Tech", "Computer Science",        2015, 2019, "8.3 CGPA"),
        (CP6,  "Manipal University",  "B.Tech", "Computer Science",        2016, 2020, "7.8 CGPA"),
        (CP7,  "IIT Kharagpur",       "B.Tech", "Computer Science",        2012, 2016, "9.0 CGPA"),
        (CP8,  "RVCE Bangalore",      "B.E.",   "Electronics & Comm.",     2017, 2021, "7.5 CGPA"),
        (CP9,  "Pune University",     "B.E.",   "Computer Science",        2016, 2020, "7.2 CGPA"),
        (CP10, "IIM Ahmedabad",       "MBA",    "Technology Management",   2014, 2016, "3.8 GPA"),
    ]
    for cp_id, inst, deg, field, sy, ey, grade in edu_data:
        db.add(Education(candidate_id=cp_id, institution=inst, degree=deg, field_of_study=field, start_year=sy, end_year=ey, grade=grade))

    await db.commit()
    log.info("seed2_done")
    print("Seeding extended data... done (5 HR + 10 candidates + 5 companies + 10 jobs)")


# ── seed3 ──────────────────────────────────────────────────────────────────────
async def seed3(db) -> None:
    existing = await db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == U_CAND))
    if existing:
        log.info("seed3_skip")
        return

    profile = CandidateProfile(
        id=CP0,
        user_id=U_CAND,
        full_name="Demo Candidate",
        headline="Software Engineer | Python | React | 3 Years",
        location="Mumbai, India",
        summary="Full stack developer with experience in Python and React.",
        desired_role="Software Engineer",
        desired_salary_min=1200000,
        desired_salary_max=1800000,
        years_of_experience=3.0,
        notice_period_days=30,
        open_to_remote=True,
        profile_strength=72,
    )
    db.add(profile)
    await db.flush()

    for sn, prof, yrs in [("Python",4,3.0),("React",3,2.0),("Node.js",3,2.0),("PostgreSQL",3,3.0),("Docker",2,1.0)]:
        db.add(CandidateSkill(candidate_id=CP0, skill_name=sn, proficiency=prof, years_exp=yrs))

    db.add(Education(candidate_id=CP0, institution="Mumbai University", degree="B.Tech", field_of_study="Computer Science", start_year=2018, end_year=2022, grade="8.0 CGPA"))
    db.add(WorkExperience(candidate_id=CP0, company_name="StartupXYZ", job_title="Software Engineer", start_date=date(2022, 7, 1), is_current=True, description="Building REST APIs with Python FastAPI"))

    timeline = [{"status": "applied", "timestamp": NOW.isoformat(), "note": "Application submitted"}]
    db.add(Application(id=uuid.UUID("00000000-0000-0000-0004-000000000001"), job_id=J1, candidate_id=CP0, status=ApplicationStatus.APPLIED,    cover_letter="I am excited to apply for this Python developer role.", timeline=timeline))
    db.add(Application(id=uuid.UUID("00000000-0000-0000-0004-000000000002"), job_id=J3, candidate_id=CP0, status=ApplicationStatus.SCREENING, cover_letter="I believe my DevOps experience aligns well.", timeline=timeline))

    await db.commit()
    log.info("seed3_done")
    print("Seeding demo candidate... done (profile + 5 skills + 2 applications)")


# ── seed4 ──────────────────────────────────────────────────────────────────────
async def seed4(db) -> None:
    """Fill every remaining table with ~10 records."""

    # Applications (8 more, total 10)
    app_count = await db.scalar(select(func.count()).select_from(Application))
    if not app_count or app_count <= 2:
        timeline = [{"status": "applied", "timestamp": NOW.isoformat(), "note": "Application submitted"}]
        for app_id, job_id, cand_id, status, cover in [
            (uuid.UUID("00000000-0000-0000-0004-000000000003"), J2,  CP1,  ApplicationStatus.INTERVIEW, "Senior Python dev applying for React role"),
            (uuid.UUID("00000000-0000-0000-0004-000000000004"), J4,  CP4,  ApplicationStatus.OFFER,     "Data scientist interested in ML projects"),
            (uuid.UUID("00000000-0000-0000-0004-000000000005"), J5,  CP3,  ApplicationStatus.HIRED,     "Java developer excited about enterprise work"),
            (uuid.UUID("00000000-0000-0000-0004-000000000006"), J3,  CP5,  ApplicationStatus.APPLIED,   "DevOps engineer with K8s experience"),
            (uuid.UUID("00000000-0000-0000-0004-000000000007"), J6,  CP6,  ApplicationStatus.SCREENING, "MERN developer seeking full stack role"),
            (uuid.UUID("00000000-0000-0000-0004-000000000008"), J7,  CP7,  ApplicationStatus.INTERVIEW, "Cloud architect with 8+ years experience"),
            (uuid.UUID("00000000-0000-0000-0004-000000000009"), J8,  CP8,  ApplicationStatus.APPLIED,   "Android developer with Kotlin expertise"),
            (uuid.UUID("00000000-0000-0000-0004-000000000010"), J9,  CP9,  ApplicationStatus.REJECTED,  "QA engineer with automation experience"),
        ]:
            db.add(Application(id=app_id, job_id=job_id, candidate_id=cand_id, status=status, cover_letter=cover, timeline=timeline))
        await db.flush()
        print("Seeding applications... done (10 total)")

    # Certifications
    cert_count = await db.scalar(select(func.count()).select_from(Certification))
    if not cert_count or cert_count == 0:
        for cp_id, name, org, issue, expiry, cred_id in [
            (CP1,  "AWS Certified Developer",              "Amazon Web Services", "2022-03-15", "2025-03-15", "DVA-C01"),
            (CP2,  "Google UX Design Certificate",         "Google",              "2022-08-01", "2025-08-01", "GUX-2022"),
            (CP3,  "Oracle Java SE 11 Developer",          "Oracle",              "2021-05-10", "2024-05-10", "1Z0-819"),
            (CP4,  "TensorFlow Developer Certificate",     "Google",              "2022-11-20", None,         "TF-2022"),
            (CP5,  "AWS Certified DevOps Engineer",        "Amazon Web Services", "2021-09-01", "2024-09-01", "DOP-C01"),
            (CP6,  "MongoDB Developer Path",               "MongoDB University",  "2023-01-15", None,         "MDBDEV-2023"),
            (CP7,  "AWS Solutions Architect Professional", "Amazon Web Services", "2020-06-01", "2023-06-01", "SAP-C01"),
            (CP8,  "Associate Android Developer",          "Google",              "2022-04-20", "2025-04-20", "AAD-2022"),
            (CP9,  "ISTQB Foundation Level",               "ISTQB",               "2021-03-05", None,         "CTFL-2021"),
            (CP10, "Certified Scrum Product Owner",        "Scrum Alliance",      "2020-10-10", "2023-10-10", "CSPO-12345"),
        ]:
            db.add(Certification(
                candidate_id=cp_id, name=name, issuing_org=org,
                issue_date=date.fromisoformat(issue),
                expiry_date=date.fromisoformat(expiry) if expiry else None,
                credential_id=cred_id,
            ))
        await db.flush()
        print("Seeding certifications... done (10)")

    # Projects
    proj_count = await db.scalar(select(func.count()).select_from(Project))
    if not proj_count or proj_count == 0:
        for cp_id, title, desc, stack, purl, rurl in [
            (CP1,  "DoneHR Portal",           "AI-powered HR recruitment platform",                    ["Python","FastAPI","React","PostgreSQL"], "https://donehr.com",      "https://github.com/user/donehr"),
            (CP2,  "Portfolio Builder",        "Drag-and-drop portfolio creator for developers",        ["React","Next.js","TypeScript","Tailwind"], None,                    "https://github.com/user/portfolio"),
            (CP3,  "Banking API Gateway",      "Microservices gateway for banking transactions",        ["Java","Spring Boot","Kafka","MySQL"],      None,                    "https://github.com/user/bankapi"),
            (CP4,  "Stock Price Predictor",    "LSTM neural network for NSE stock prediction",          ["Python","TensorFlow","Pandas","Plotly"],   None,                    "https://github.com/user/stock-ml"),
            (CP5,  "K8s Auto-Scaler",          "Custom Kubernetes HPA controller for cost optimization",["Go","Kubernetes","Prometheus","Docker"],   None,                    "https://github.com/user/k8s-scaler"),
            (CP6,  "E-Commerce Platform",      "Full stack MERN e-commerce with payments",              ["React","Node.js","MongoDB","Stripe"],      "https://shop.example.com","https://github.com/user/ecommerce"),
            (CP7,  "Multi-Cloud Cost Monitor", "Real-time AWS/Azure cost monitoring dashboard",         ["Python","AWS","Azure","Terraform","React"], "https://cloudcost.io",  "https://github.com/user/cloudcost"),
            (CP8,  "Fitness Tracker App",      "Kotlin Android app for workout tracking",               ["Kotlin","Android","Firebase","Room DB"],   None,                    "https://github.com/user/fitness"),
            (CP9,  "Test Automation Framework","Reusable Selenium+TestNG framework with HTML reports",  ["Java","Selenium","TestNG","Maven"],         None,                    "https://github.com/user/automation"),
            (CP10, "SaaS Analytics Dashboard", "Product analytics dashboard with custom metrics",       ["React","Python","SQL","D3.js"],             "https://analytics.io",  "https://github.com/user/analytics"),
        ]:
            db.add(Project(
                candidate_id=cp_id, title=title, description=desc,
                tech_stack=stack, project_url=purl, repo_url=rurl,
                start_date=date(2022, 1, 1), end_date=date(2023, 6, 30),
            ))
        await db.flush()
        print("Seeding projects... done (10)")

    # Job Alerts
    alert_count = await db.scalar(select(func.count()).select_from(JobAlert))
    if not alert_count or alert_count == 0:
        for cp_id, title, kw, loc, jtype, sal_min in [
            (CP1,  "Python Jobs Bangalore",  "python django fastapi",      "Bangalore", JobType.FULL_TIME, 1800000),
            (CP2,  "React Jobs",             "react typescript nextjs",    "Hyderabad", JobType.FULL_TIME, 1200000),
            (CP3,  "Java Remote",            "java spring boot kafka",     None,        JobType.FULL_TIME, 1400000),
            (CP4,  "Data Science ML",        "machine learning data science","Bangalore",JobType.FULL_TIME, 1800000),
            (CP5,  "DevOps Openings",        "devops kubernetes aws",      None,        JobType.FULL_TIME, 1500000),
            (CP6,  "Full Stack MERN",        "react nodejs mongodb",       "Mumbai",    JobType.FULL_TIME, 1300000),
            (CP7,  "Cloud Architecture",     "cloud aws azure architect",  None,        JobType.FULL_TIME, 2500000),
            (CP8,  "Android Dev",            "android kotlin jetpack",     "Hyderabad", JobType.FULL_TIME, 1200000),
            (CP9,  "QA Automation",          "selenium testng automation", "Noida",     JobType.FULL_TIME, 1000000),
            (CP10, "Product Management",     "product manager agile",      "Bangalore", JobType.FULL_TIME, 2000000),
        ]:
            db.add(JobAlert(candidate_id=cp_id, title=title, keywords=kw, location=loc, job_type=jtype, salary_min=sal_min, is_active=True))
        await db.flush()
        print("Seeding job alerts... done (10)")

    # AI Summaries
    ai_count = await db.scalar(select(func.count()).select_from(AISummary))
    if not ai_count or ai_count == 0:
        for entity_id, content in [
            (CP1,  {"summary":"Arjun is a senior Python developer with strong expertise in Django and AWS. 6 years building scalable microservices.",    "strengths":["Python","AWS","System Design"],     "top_skills":["Python","Django","FastAPI","AWS"],              "experience_years":6}),
            (CP2,  {"summary":"Priya is a skilled React frontend engineer. 4 years delivering high-quality SPAs with TypeScript and Next.js.",           "strengths":["React","UI/UX","TypeScript"],        "top_skills":["React","TypeScript","Next.js"],                 "experience_years":4}),
            (CP3,  {"summary":"Rahul is a Java backend developer specializing in enterprise microservices. 5 years with Spring Boot and Kafka.",         "strengths":["Java","Spring Boot","Architecture"],  "top_skills":["Java","Spring Boot","Microservices"],           "experience_years":5}),
            (CP4,  {"summary":"Sneha is a data scientist building predictive models. 3 years experience with TensorFlow and Pandas.",                    "strengths":["Machine Learning","Python","Stats"],  "top_skills":["Python","TensorFlow","Pandas"],                 "experience_years":3}),
            (CP5,  {"summary":"Vikram is a certified DevOps engineer. 5 years automating AWS and Kubernetes infrastructure at scale.",                   "strengths":["AWS","Kubernetes","CI/CD"],           "top_skills":["Docker","Kubernetes","AWS","Terraform"],        "experience_years":5}),
            (CP6,  {"summary":"Ananya is a full stack MERN developer. 4 years delivering React+Node.js applications end-to-end.",                       "strengths":["React","Node.js","Full Stack"],       "top_skills":["React","Node.js","MongoDB"],                    "experience_years":4}),
            (CP7,  {"summary":"Karthik is an AWS certified cloud architect with 8 years designing enterprise cloud solutions at scale.",                 "strengths":["Cloud Architecture","AWS","Terraform"],"top_skills":["AWS","Azure","Terraform","Kubernetes"],         "experience_years":8}),
            (CP8,  {"summary":"Pooja is an Android developer specializing in Kotlin and Jetpack Compose. 3 production apps on Play Store.",             "strengths":["Android","Kotlin","Mobile"],          "top_skills":["Android","Kotlin","Jetpack Compose"],           "experience_years":3}),
            (CP9,  {"summary":"Rohit is a QA automation specialist. 4 years building comprehensive Selenium+TestNG test suites.",                       "strengths":["Automation","Selenium","Testing"],    "top_skills":["Selenium","TestNG","Java","REST Assured"],      "experience_years":4}),
            (CP10, {"summary":"Divya is an experienced product manager with MBA from IIM-A. 6 years launching SaaS products end-to-end.",               "strengths":["Product Strategy","Agile","Data"],   "top_skills":["Product Management","Agile","Analytics"],       "experience_years":6}),
        ]:
            db.add(AISummary(entity_id=entity_id, entity_type="candidate", summary_type=SummaryType.RESUME_SUMMARY, content=content, model_used="llama-3.3-70b-versatile", token_usage=850))
        await db.flush()
        print("Seeding AI summaries... done (10)")

    # Saved Searches
    ss_count = await db.scalar(select(func.count()).select_from(SavedSearch))
    if not ss_count or ss_count == 0:
        for uid, name, filters in [
            (U_HR,  "Senior Python Devs",         {"query":"python senior","skills":[{"skill":"Python","min_proficiency":4}],"location":"Bangalore"}),
            (U_HR2, "React Specialists",           {"query":"react typescript","min_experience":3,"open_to_remote":True}),
            (U_HR3, "Java Microservices",          {"query":"java spring boot microservices","min_experience":4}),
            (U_HR4, "Data Scientists ML",          {"query":"machine learning tensorflow","skills":[{"skill":"Python"}]}),
            (U_HR5, "Cloud/DevOps Engineers",      {"query":"aws kubernetes devops","open_to_remote":True}),
            (U_HR6, "Full Stack MERN",             {"query":"react nodejs mongodb","min_experience":2}),
            (U_HR,  "Cloud Architects",            {"query":"cloud architect aws","min_experience":6}),
            (U_HR2, "Mobile Developers",           {"query":"android kotlin ios"}),
            (U_HR3, "QA Automation",               {"query":"selenium testng automation","location":"Noida"}),
            (U_HR4, "Product Managers",            {"query":"product manager agile","min_experience":5}),
        ]:
            db.add(SavedSearch(user_id=uid, name=name, filters=filters))
        await db.flush()
        print("Seeding saved searches... done (10)")

    # Talent Pools
    pool_count = await db.scalar(select(func.count()).select_from(TalentPool))
    if not pool_count or pool_count == 0:
        pool_ids = [uuid.UUID(f"00000000-0000-0000-0005-{i+1:012d}") for i in range(10)]
        cp_ids   = [CP1,CP2,CP3,CP4,CP5,CP6,CP7,CP8,CP9,CP10]
        for i, (uid, name) in enumerate([
            (U_HR,  "Python Developers Q1 2025"),
            (U_HR2, "React Frontend Talent"),
            (U_HR3, "Java Backend Pipeline"),
            (U_HR4, "Data Science Candidates"),
            (U_HR5, "DevOps Shortlist"),
            (U_HR6, "Full Stack Pool"),
            (U_HR,  "Cloud Architecture Bench"),
            (U_HR2, "Mobile Developers"),
            (U_HR3, "QA Automation Team"),
            (U_HR4, "Product Leadership"),
        ]):
            db.add(TalentPool(id=pool_ids[i], user_id=uid, name=name))
        await db.flush()
        for pool_id, cp_id in zip(pool_ids, cp_ids):
            db.add(TalentPoolCandidate(pool_id=pool_id, candidate_id=cp_id, notes="Strong fit for the role"))
        await db.flush()
        print("Seeding talent pools... done (10 pools + 10 candidates)")

    # Search Analytics
    sa_count = await db.scalar(select(func.count()).select_from(SearchAnalytic))
    if not sa_count or sa_count == 0:
        for uid, filters, result_count in [
            (U_HR,  {"query":"python","skills":["Python"]}, 4),
            (U_HR2, {"query":"react frontend","min_experience":2}, 3),
            (U_HR3, {"query":"java spring","location":"Pune"}, 2),
            (U_HR4, {"query":"data science ml","skills":["Python","TensorFlow"]}, 2),
            (U_HR5, {"query":"devops kubernetes","open_to_remote":True}, 3),
            (U_HR6, {"query":"full stack mern"}, 4),
            (U_HR,  {"query":"cloud architect aws","min_experience":6}, 2),
            (U_HR2, {"query":"android kotlin"}, 1),
            (U_HR3, {"query":"selenium automation"}, 1),
            (U_HR4, {"query":"product manager agile","min_experience":5}, 2),
        ]:
            db.add(SearchAnalytic(user_id=uid, filters=filters, result_count=result_count))
        await db.flush()
        print("Seeding search analytics... done (10)")

    # Audit Logs
    audit_count = await db.scalar(select(func.count()).select_from(AuditLog))
    if not audit_count or audit_count == 0:
        for uid, action, entity_type, entity_id, old_val, new_val in [
            (U_HR,   "job_published",           "job",         str(J1),  None,                    {"status":"active"}),
            (U_HR2,  "job_published",           "job",         str(J2),  None,                    {"status":"active"}),
            (U_DEV1, "application_submitted",   "application", str(uuid.UUID("00000000-0000-0000-0004-000000000003")), None, {"status":"applied"}),
            (U_HR3,  "pipeline_updated",        "pipeline",    str(J3),  None,                    {"stage":"Interview"}),
            (U_DEV4, "profile_updated",         "candidate",   str(CP4), {"headline":"Data Analyst"},{"headline":"Data Scientist | Python | ML"}),
            (U_HR4,  "job_paused",              "job",         str(J4),  {"status":"active"},     {"status":"paused"}),
            (U_DEV5, "resume_uploaded",         "candidate",   str(CP5), None,                    {"filename":"vikram_resume.pdf"}),
            (U_HR5,  "application_status_changed","application",str(uuid.UUID("00000000-0000-0000-0004-000000000008")),{"status":"applied"},{"status":"screening"}),
            (U_HR6,  "job_closed",              "job",         str(J6),  {"status":"active"},     {"status":"closed"}),
            (U_HR,   "candidate_shortlisted",   "application", str(uuid.UUID("00000000-0000-0000-0004-000000000007")),{"status":"screening"},{"status":"interview"}),
        ]:
            db.add(AuditLog(user_id=uid, action=action, entity_type=entity_type, entity_id=entity_id, old_value_json=old_val, new_value_json=new_val, ip_address="127.0.0.1"))
        await db.flush()
        print("Seeding audit logs... done (10)")

    # Platform Events
    pe_count = await db.scalar(select(func.count()).select_from(PlatformEvent))
    if not pe_count or pe_count == 0:
        SA_ID = uuid.UUID("00000000-0000-0000-0099-000000000001")
        for event_type, target_id, target_type, details in [
            ("user_registered",      str(U_DEV1),  "user",        {"email":"arjun.sharma@gmail.com","role":"candidate"}),
            ("user_registered",      str(U_DEV2),  "user",        {"email":"priya.patel@gmail.com","role":"candidate"}),
            ("job_published",        str(J1),       "job",         {"title":"Senior Python Developer","company":"TCS"}),
            ("job_published",        str(J2),       "job",         {"title":"React Frontend Engineer","company":"Infosys"}),
            ("application_received", str(uuid.UUID("00000000-0000-0000-0004-000000000003")),"application",{"job":"Senior Python Developer","candidate":"Arjun Sharma"}),
            ("ai_match_score",       str(uuid.UUID("00000000-0000-0000-0004-000000000004")),"application",{"score":88,"grade":"A"}),
            ("user_deactivated",     str(U_DEV9),  "user",        {"reason":"Account inactive 90 days"}),
            ("bulk_email_sent",      None,          "system",      {"template":"job_alert","recipient_count":10}),
            ("admin_login",          str(SA_ID),   "admin",       {"email":"superadmin@donehr.com","ip":"127.0.0.1"}),
            ("system_health_check",  None,          "system",      {"db_latency_ms":2.3,"redis_latency_ms":0.8,"status":"healthy"}),
        ]:
            db.add(PlatformEvent(event_type=event_type, actor_id=SA_ID, actor_role="superadmin", target_id=target_id, target_type=target_type, details=details, ip_address="127.0.0.1"))
        await db.flush()
        print("Seeding platform events... done (10)")

    # Chat Conversations, Messages, Reads, Reactions, Reports
    chat_count = await db.scalar(select(func.count()).select_from(ChatConversation))
    if not chat_count or chat_count == 0:
        conv_ids = [uuid.UUID(f"00000000-0000-0000-0006-{i+1:012d}") for i in range(10)]
        msg_ids  = [uuid.UUID(f"00000000-0000-0000-0007-{i+1:012d}") for i in range(10)]

        # 5 direct conversations
        for conv_id, hr_id, dev_id, title in [
            (conv_ids[0], U_HR,  U_DEV1, "HR and Arjun Sharma"),
            (conv_ids[1], U_HR2, U_DEV2, "HR and Priya Patel"),
            (conv_ids[2], U_HR3, U_DEV3, "HR and Rahul Verma"),
            (conv_ids[3], U_HR4, U_DEV4, "HR and Sneha Kumar"),
            (conv_ids[4], U_HR5, U_DEV5, "HR and Vikram Singh"),
        ]:
            db.add(ChatConversation(id=conv_id, type=ConversationType.DIRECT, title=title, creator_id=hr_id))
            db.add(ConversationParticipant(conversation_id=conv_id, user_id=hr_id,  is_admin=True))
            db.add(ConversationParticipant(conversation_id=conv_id, user_id=dev_id, is_admin=False))

        # 3 group conversations
        for conv_id, creator, title, participants in [
            (conv_ids[5], U_HR,  "Python Team Interviews",  [U_HR, U_HR2, U_DEV1, U_DEV4]),
            (conv_ids[6], U_HR3, "Java Backend Candidates", [U_HR3, U_HR4, U_DEV3, U_DEV9]),
            (conv_ids[7], U_HR6, "Full Stack Shortlist",    [U_HR6, U_HR5, U_DEV2, U_DEV6]),
        ]:
            db.add(ChatConversation(id=conv_id, type=ConversationType.GROUP, title=title, creator_id=creator))
            for uid in participants:
                db.add(ConversationParticipant(conversation_id=conv_id, user_id=uid, is_admin=(uid == creator)))

        # 2 broadcast conversations
        for conv_id, creator, title in [
            (conv_ids[8], U_HR,  "All Candidates Q1 2025 Opportunities"),
            (conv_ids[9], U_HR6, "Tech Hiring Drive Bangalore"),
        ]:
            db.add(ChatConversation(id=conv_id, type=ConversationType.BROADCAST, title=title, creator_id=creator))
            db.add(ConversationParticipant(conversation_id=conv_id, user_id=creator, is_admin=True))

        await db.flush()

        # 10 messages
        for mid, cid, sender, content in [
            (msg_ids[0], conv_ids[0], U_HR,  "Hi Arjun! Impressive Python background. Interested in our Senior Python Developer role at TCS?"),
            (msg_ids[1], conv_ids[1], U_HR2, "Hello Priya! Your React skills are a great match for our frontend position. When can we schedule a call?"),
            (msg_ids[2], conv_ids[2], U_DEV3,"Hi, thank you for reaching out! I'd love to learn more about the Java developer position at Wipro."),
            (msg_ids[3], conv_ids[3], U_HR4, "Sneha, your data science background is exactly what our team needs. Can you share your availability?"),
            (msg_ids[4], conv_ids[4], U_DEV5,"Hi! Yes, I am very interested in the DevOps role. I have 5 years of AWS and Kubernetes experience."),
            (msg_ids[5], conv_ids[5], U_HR,  "Welcome to the Python Team Interviews group! We will coordinate all Python developer interview schedules here."),
            (msg_ids[6], conv_ids[6], U_HR3, "Hello everyone. This group is for the Java backend candidates shortlist. Please share your available time slots."),
            (msg_ids[7], conv_ids[7], U_HR6, "Hi team! We have shortlisted 2 strong full stack candidates. Let us discuss their profiles before the final round."),
            (msg_ids[8], conv_ids[8], U_HR,  "Announcement: TCS is hiring 50+ engineers for Q1 2025. Positions in Python, React, Java, DevOps, and Cloud. Apply now!"),
            (msg_ids[9], conv_ids[9], U_HR6, "Announcement: Accenture Bangalore Tech Drive - walk-in interviews this Saturday for Senior Developers (5+ years)."),
        ]:
            db.add(ChatMessage(id=mid, conversation_id=cid, sender_id=sender, content=content, message_type=MessageType.TEXT))

        await db.flush()

        # 10 reads
        for msg_id, reader_id in [
            (msg_ids[0], U_DEV1), (msg_ids[1], U_DEV2), (msg_ids[2], U_HR3),
            (msg_ids[3], U_DEV4), (msg_ids[4], U_HR5),  (msg_ids[5], U_HR2),
            (msg_ids[5], U_DEV1), (msg_ids[6], U_HR4),  (msg_ids[7], U_HR5),
            (msg_ids[8], U_DEV1),
        ]:
            db.add(ChatMessageRead(message_id=msg_id, user_id=reader_id, read_at=NOW))

        # 10 reactions
        for msg_id, uid, emoji in [
            (msg_ids[0], U_DEV1, "thumbsup"),   (msg_ids[1], U_DEV2, "pray"),
            (msg_ids[2], U_HR3,  "thumbsup"),   (msg_ids[4], U_DEV5, "muscle"),
            (msg_ids[5], U_HR2,  "thumbsup"),   (msg_ids[5], U_DEV1, "tada"),
            (msg_ids[6], U_DEV3, "white_check"), (msg_ids[7], U_HR6, "fire"),
            (msg_ids[8], U_DEV1, "rocket"),      (msg_ids[9], U_DEV6, "clap"),
        ]:
            db.add(ChatReaction(message_id=msg_id, user_id=uid, emoji=emoji))

        # 1 report
        db.add(ChatReport(
            message_id=msg_ids[9],
            reporter_id=U_DEV8,
            reason="Message contains misleading job information",
            status=ReportStatus.PENDING,
        ))

        await db.flush()
        await db.commit()
        print("Seeding chat data... done (10 conversations + 10 messages + reads + reactions)")
    else:
        await db.commit()

    print("seed4 complete — all tables populated")


# ── main ───────────────────────────────────────────────────────────────────────
async def main() -> None:
    async with AsyncSessionLocal() as db:
        await seed1(db)
        await seed_admin_users(db)
        await seed2(db)
        await seed3(db)
        await seed4(db)
    print("\nAll seed data ready!")


if __name__ == "__main__":
    asyncio.run(main())
