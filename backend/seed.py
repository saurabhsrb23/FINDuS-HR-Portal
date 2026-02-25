"""Bootstrap seed data -- run once when users table is empty (seed1),
and again for Module 6 extended data (seed2, guarded by user count > 4)."""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select, func

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.company import Company
from app.models.job import Job, JobStatus, JobType, PipelineStage
from app.models.candidate import CandidateProfile, WorkExperience, Education, CandidateSkill
from app.models.application import Application, ApplicationStatus

log = structlog.get_logger("seed")

# Fixed UUIDs
U_ELITE  = uuid.UUID("00000000-0000-0000-0000-000000000001")
U_ADMIN  = uuid.UUID("00000000-0000-0000-0000-000000000002")
U_HR     = uuid.UUID("00000000-0000-0000-0000-000000000003")
U_CAND   = uuid.UUID("00000000-0000-0000-0000-000000000004")
U_HR2 = uuid.UUID("00000000-0000-0000-0000-000000000005")
U_HR3 = uuid.UUID("00000000-0000-0000-0000-000000000006")
U_HR4 = uuid.UUID("00000000-0000-0000-0000-000000000007")
U_HR5 = uuid.UUID("00000000-0000-0000-0000-000000000008")
U_HR6 = uuid.UUID("00000000-0000-0000-0000-000000000009")
U_DEV1  = uuid.UUID("00000000-0000-0000-0000-000000000011")
U_DEV2  = uuid.UUID("00000000-0000-0000-0000-000000000012")
U_DEV3  = uuid.UUID("00000000-0000-0000-0000-000000000013")
U_DEV4  = uuid.UUID("00000000-0000-0000-0000-000000000014")
U_DEV5  = uuid.UUID("00000000-0000-0000-0000-000000000015")
U_DEV6  = uuid.UUID("00000000-0000-0000-0000-000000000016")
U_DEV7  = uuid.UUID("00000000-0000-0000-0000-000000000017")
U_DEV8  = uuid.UUID("00000000-0000-0000-0000-000000000018")
U_DEV9  = uuid.UUID("00000000-0000-0000-0000-000000000019")
U_DEV10 = uuid.UUID("00000000-0000-0000-0000-000000000020")
C_TECHCORP       = uuid.UUID("00000000-0000-0000-0001-000000000001")
C_DATAAI         = uuid.UUID("00000000-0000-0000-0001-000000000002")
C_CLOUDSYS       = uuid.UUID("00000000-0000-0000-0001-000000000003")
C_APPWORKS       = uuid.UUID("00000000-0000-0000-0001-000000000004")
C_ENTERPRISETECH = uuid.UUID("00000000-0000-0000-0001-000000000005")
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
CP0  = uuid.UUID("00000000-0000-0000-0003-000000000000")  # candidate@donehr.com profile

def dt(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


DEFAULT_STAGES = [
    ("Applied",   0, "#6366f1"),
    ("Screening", 1, "#f59e0b"),
    ("Interview", 2, "#3b82f6"),
    ("Offer",     3, "#10b981"),
    ("Hired",     4, "#22c55e"),
    ("Rejected",  5, "#ef4444"),
]


def make_pipeline(job_id: uuid.UUID) -> list[PipelineStage]:
    return [
        PipelineStage(
            id=uuid.uuid4(), job_id=job_id,
            stage_name=name, stage_order=order,
            color=color, is_default=True,
        )
        for name, order, color in DEFAULT_STAGES
    ]


async def seed1(session) -> None:
    users = [
        User(id=U_ELITE, email="elite@donehr.com", password_hash=hash_password("Elite@Admin1!"),
             full_name="Elite Admin", role=UserRole.ELITE_ADMIN, is_active=True, is_verified=True),
        User(id=U_ADMIN, email="admin@donehr.com", password_hash=hash_password("Admin@1234!"),
             full_name="System Admin", role=UserRole.ADMIN, is_active=True, is_verified=True),
        User(id=U_HR,    email="hr@donehr.com",    password_hash=hash_password("Hr@123456!"),
             full_name="Demo HR Manager", role=UserRole.HR_ADMIN, is_active=True, is_verified=True),
        User(id=U_CAND,  email="candidate@donehr.com", password_hash=hash_password("Candidate@1!"),
             full_name="Demo Candidate", role=UserRole.CANDIDATE, is_active=True, is_verified=True),
    ]
    session.add_all(users)
    await session.flush()
    log.info("seed1_complete", users_created=len(users))
    for u in users:
        log.info("seed1_user", email=u.email, role=u.role.value)


async def seed2(session) -> None:
    hr_users = [
        User(id=U_HR2, email="hr2@donehr.com", password_hash=hash_password("Hr2@123456!"), full_name="Ravi Shankar",  role=UserRole.HR,             is_active=True, is_verified=True),
        User(id=U_HR3, email="hr3@donehr.com", password_hash=hash_password("Hr3@123456!"), full_name="Ananya Desai",  role=UserRole.RECRUITER,      is_active=True, is_verified=True),
        User(id=U_HR4, email="hr4@donehr.com", password_hash=hash_password("Hr4@123456!"), full_name="Kiran Mehta",   role=UserRole.HIRING_MANAGER, is_active=True, is_verified=True),
        User(id=U_HR5, email="hr5@donehr.com", password_hash=hash_password("Hr5@123456!"), full_name="Pooja Nambiar", role=UserRole.RECRUITER,      is_active=True, is_verified=True),
        User(id=U_HR6, email="hr6@donehr.com", password_hash=hash_password("Hr6@123456!"), full_name="Sameer Joshi",  role=UserRole.HIRING_MANAGER, is_active=True, is_verified=True),
    ]
    session.add_all(hr_users)
    await session.flush()
    log.info("seed2_hr_users_created", count=len(hr_users))

    dev_users = [
        User(id=U_DEV1,  email="dev1@donehr.com",  password_hash=hash_password("Dev1@123456!"),  full_name="Arjun Sharma",   role=UserRole.CANDIDATE, is_active=True, is_verified=True),
        User(id=U_DEV2,  email="dev2@donehr.com",  password_hash=hash_password("Dev2@123456!"),  full_name="Priya Patel",    role=UserRole.CANDIDATE, is_active=True, is_verified=True),
        User(id=U_DEV3,  email="dev3@donehr.com",  password_hash=hash_password("Dev3@123456!"),  full_name="Rahul Verma",    role=UserRole.CANDIDATE, is_active=True, is_verified=True),
        User(id=U_DEV4,  email="dev4@donehr.com",  password_hash=hash_password("Dev4@123456!"),  full_name="Sneha Reddy",    role=UserRole.CANDIDATE, is_active=True, is_verified=True),
        User(id=U_DEV5,  email="dev5@donehr.com",  password_hash=hash_password("Dev5@123456!"),  full_name="Aditya Kumar",   role=UserRole.CANDIDATE, is_active=True, is_verified=True),
        User(id=U_DEV6,  email="dev6@donehr.com",  password_hash=hash_password("Dev6@123456!"),  full_name="Kavya Nair",     role=UserRole.CANDIDATE, is_active=True, is_verified=True),
        User(id=U_DEV7,  email="dev7@donehr.com",  password_hash=hash_password("Dev7@123456!"),  full_name="Vikram Singh",   role=UserRole.CANDIDATE, is_active=True, is_verified=True),
        User(id=U_DEV8,  email="dev8@donehr.com",  password_hash=hash_password("Dev8@123456!"),  full_name="Meena Iyer",     role=UserRole.CANDIDATE, is_active=True, is_verified=True),
        User(id=U_DEV9,  email="dev9@donehr.com",  password_hash=hash_password("Dev9@123456!"),  full_name="Suresh Babu",    role=UserRole.CANDIDATE, is_active=True, is_verified=True),
        User(id=U_DEV10, email="dev10@donehr.com", password_hash=hash_password("Dev10@123456!"), full_name="Divya Krishnan", role=UserRole.CANDIDATE, is_active=True, is_verified=True),
    ]
    session.add_all(dev_users)
    await session.flush()
    log.info("seed2_dev_users_created", count=len(dev_users))

    companies = [
        Company(id=C_TECHCORP,       name="TechCorp",       industry="Software",       size="201-500",  website="https://techcorp.example.com",       hr_id=U_HR),
        Company(id=C_DATAAI,         name="DataAI Corp",    industry="Data and AI",    size="51-200",   website="https://dataai.example.com",         hr_id=U_HR2),
        Company(id=C_CLOUDSYS,       name="CloudSys",       industry="Cloud Services", size="11-50",    website="https://cloudsys.example.com",       hr_id=U_HR3),
        Company(id=C_APPWORKS,       name="AppWorks",       industry="Mobile Apps",    size="11-50",    website="https://appworks.example.com",       hr_id=U_HR4),
        Company(id=C_ENTERPRISETECH, name="EnterpriseTech", industry="Enterprise IT",  size="501-1000", website="https://enterprisetech.example.com", hr_id=U_HR5),
    ]
    session.add_all(companies)
    await session.flush()
    log.info("seed2_companies_created", count=len(companies))

    published_at = now_utc()

    jobs = [
        Job(
            id=J1, title="Senior Python Developer",
            description=("We are looking for an experienced Python developer. You will design scalable REST APIs and mentor juniors."),
            requirements="5+ years Python. Strong Django or FastAPI. AWS (EC2, S3, RDS). Docker/CI-CD.",
            location="Bangalore, India", job_type=JobType.FULL_TIME, department="Engineering",
            salary_min=1500000, salary_max=2500000, currency="INR",
            experience_years_min=5, experience_years_max=8,
            status=JobStatus.ACTIVE, posted_by=U_HR, company_id=C_TECHCORP,
            published_at=published_at, views_count=142, applications_count=0,
        ),
        Job(
            id=J2, title="React Frontend Engineer",
            description=("Join TechCorp Mumbai as a React Frontend Engineer. Build high-performance SPAs with React 18, TypeScript, and Tailwind CSS."),
            requirements="3+ years React. TypeScript proficiency. Redux or Zustand. REST and GraphQL.",
            location="Mumbai, India", job_type=JobType.FULL_TIME, department="Engineering",
            salary_min=1000000, salary_max=1800000, currency="INR",
            experience_years_min=3, experience_years_max=6,
            status=JobStatus.ACTIVE, posted_by=U_HR, company_id=C_TECHCORP,
            published_at=published_at, views_count=98, applications_count=0,
        ),
        Job(
            id=J3, title="Data Scientist",
            description=("DataAI Corp is hiring a Data Scientist to develop and deploy ML models. Work with large datasets, conduct experiments, productionise models."),
            requirements="3+ years data science. Python (pandas, scikit-learn, PyTorch). SQL.",
            location="Hyderabad, India", job_type=JobType.FULL_TIME, department="Data Science",
            salary_min=1200000, salary_max=2000000, currency="INR",
            experience_years_min=3, experience_years_max=7,
            status=JobStatus.ACTIVE, posted_by=U_HR2, company_id=C_DATAAI,
            published_at=published_at, views_count=210, applications_count=0,
        ),
        Job(
            id=J4, title="DevOps Engineer",
            description=("CloudSys is looking for a DevOps Engineer to manage Kubernetes clusters, build IaC with Terraform, and maintain CI/CD pipelines."),
            requirements="4+ years DevOps. Kubernetes and Helm. Terraform or Pulumi. AWS or GCP.",
            location="Pune, India", job_type=JobType.FULL_TIME, department="Infrastructure",
            salary_min=1800000, salary_max=3000000, currency="INR",
            experience_years_min=4, experience_years_max=8,
            status=JobStatus.ACTIVE, posted_by=U_HR3, company_id=C_CLOUDSYS,
            published_at=published_at, views_count=75, applications_count=0,
        ),
        Job(
            id=J5, title="Mobile Developer (Flutter)",
            description=("AppWorks seeks a Flutter developer to build cross-platform iOS and Android apps. Own features end-to-end, integrate REST and GraphQL APIs."),
            requirements="2+ years Flutter/Dart. Published app on Play Store or App Store. BLoC/Riverpod.",
            location="Chennai, India", job_type=JobType.FULL_TIME, department="Mobile Engineering",
            salary_min=800000, salary_max=1500000, currency="INR",
            experience_years_min=2, experience_years_max=5,
            status=JobStatus.ACTIVE, posted_by=U_HR4, company_id=C_APPWORKS,
            published_at=published_at, views_count=60, applications_count=0,
        ),
        Job(
            id=J6, title="Java Backend Developer",
            description=("EnterpriseTech is hiring a senior Java developer to build microservices powering our enterprise SaaS platform with Spring Boot, Kafka, and Azure."),
            requirements="6+ years Java. Spring Boot/Cloud. Kafka or RabbitMQ. Azure or AWS.",
            location="Delhi, India", job_type=JobType.FULL_TIME, department="Backend Engineering",
            salary_min=2000000, salary_max=3500000, currency="INR",
            experience_years_min=6, experience_years_max=12,
            status=JobStatus.ACTIVE, posted_by=U_HR5, company_id=C_ENTERPRISETECH,
            published_at=published_at, views_count=183, applications_count=0,
        ),
        Job(
            id=J7, title="QA Lead",
            description=("QualityFirst is searching for a QA Lead to own test strategy across web and mobile products. Build Selenium/Cypress suites, mentor QA engineers."),
            requirements="5+ years QA. Selenium WebDriver and Cypress. Postman. JIRA/Xray.",
            location="Bangalore, India", job_type=JobType.FULL_TIME, department="Quality Assurance",
            salary_min=1200000, salary_max=1800000, currency="INR",
            experience_years_min=5, experience_years_max=10,
            status=JobStatus.ACTIVE, posted_by=U_HR6, company_id=C_TECHCORP,
            published_at=published_at, views_count=52, applications_count=0,
        ),
        Job(
            id=J8, title="Full Stack Developer (Remote)",
            description=("RemoteCo is a fully distributed startup. Build features across .NET backend and React frontend. 100 percent remote."),
            requirements="4+ years full stack. .NET 6+ Core. React/TypeScript. SQL Server or PostgreSQL.",
            location="Remote", job_type=JobType.FULL_TIME, department="Product Engineering",
            salary_min=1000000, salary_max=2000000, currency="INR",
            experience_years_min=4, experience_years_max=12,
            status=JobStatus.ACTIVE, posted_by=U_HR, company_id=C_TECHCORP,
            published_at=published_at, views_count=320, applications_count=0,
        ),
        Job(
            id=J9, title="Data Engineer",
            description=("DataOps Inc is hiring a Data Engineer to design large-scale data pipelines using Apache Spark and Kafka. Build data lakes on AWS."),
            requirements="4+ years data engineering. Apache Spark and PySpark. Kafka. AWS Glue/EMR/S3.",
            location="Chennai, India", job_type=JobType.FULL_TIME, department="Data Engineering",
            salary_min=1500000, salary_max=2500000, currency="INR",
            experience_years_min=4, experience_years_max=8,
            status=JobStatus.ACTIVE, posted_by=U_HR2, company_id=C_DATAAI,
            published_at=published_at, views_count=128, applications_count=0,
        ),
        Job(
            id=J10, title="Machine Learning Engineer",
            description=("AICorp is seeking an ML Engineer to build and productionise ML models at scale. Work on NLP and computer vision projects."),
            requirements="4+ years ML engineering. PyTorch or TensorFlow. MLflow. SageMaker or Vertex.",
            location="Bangalore, India", job_type=JobType.FULL_TIME, department="AI Research and Engineering",
            salary_min=1800000, salary_max=3000000, currency="INR",
            experience_years_min=4, experience_years_max=9,
            status=JobStatus.ACTIVE, posted_by=U_HR2, company_id=C_DATAAI,
            published_at=published_at, views_count=275, applications_count=0,
        ),
    ]
    session.add_all(jobs)
    await session.flush()
    log.info("seed2_jobs_created", count=len(jobs))

    all_stages: list[PipelineStage] = []
    for job in jobs:
        all_stages.extend(make_pipeline(job.id))
    session.add_all(all_stages)
    await session.flush()
    log.info("seed2_pipeline_stages_created", count=len(all_stages))

    # ------------------------------------------------------------------
    # Candidate Profiles (profile_strength=100: all fields populated)
    # 20 base +15 headline +15 summary +15 resume_url
    # +10 work_exp +10 education +5 skills>=3 +10 phone+location = 100
    # ------------------------------------------------------------------
    cp1 = CandidateProfile(
        id=CP1, user_id=U_DEV1,
        full_name="Arjun Sharma", phone="+91-9876543201", location="Bangalore, India",
        headline="Senior Python Developer | Django | AWS | 6 Years Experience",
        summary="Experienced Python developer with 6 years building scalable backend systems using Django, FastAPI, and AWS. Passionate about clean architecture and performance optimisation.",
        resume_url="seeded", resume_filename="arjun_sharma_resume.pdf",
        desired_role="Senior Python Developer",
        desired_salary_min=1800000, desired_salary_max=2500000,
        desired_location="Bangalore, India",
        open_to_remote=True, notice_period_days=30, years_of_experience=6.0,
        profile_strength=100,
    )
    cp2 = CandidateProfile(
        id=CP2, user_id=U_DEV2,
        full_name="Priya Patel", phone="+91-9876543202", location="Mumbai, India",
        headline="Frontend Engineer | React | TypeScript | Node.js | 4 Years",
        summary="Frontend-focused full stack developer with 4 years crafting pixel-perfect React applications with TypeScript. Comfortable with Node.js backends and reusable component libraries.",
        resume_url="seeded", resume_filename="priya_patel_resume.pdf",
        desired_role="React Frontend Engineer",
        desired_salary_min=1400000, desired_salary_max=1800000,
        desired_location="Mumbai, India",
        open_to_remote=True, notice_period_days=15, years_of_experience=4.0,
        profile_strength=100,
    )
    cp3 = CandidateProfile(
        id=CP3, user_id=U_DEV3,
        full_name="Rahul Verma", phone="+91-9876543203", location="Hyderabad, India",
        headline="Senior Java Developer | Spring Boot | Microservices | 8 Years",
        summary="Seasoned Java backend engineer with 8 years designing enterprise microservices using Spring Boot and Kafka. Led teams of 6+ engineers and delivered high-availability systems at scale.",
        resume_url="seeded", resume_filename="rahul_verma_resume.pdf",
        desired_role="Java Backend Developer",
        desired_salary_min=2500000, desired_salary_max=3500000,
        desired_location="Hyderabad, India",
        open_to_remote=False, notice_period_days=60, years_of_experience=8.0,
        profile_strength=100,
    )
    cp4 = CandidateProfile(
        id=CP4, user_id=U_DEV4,
        full_name="Sneha Reddy", phone="+91-9876543204", location="Bangalore, India",
        headline="Data Scientist | Python | Machine Learning | scikit-learn | 3 Years",
        summary="Data scientist with 3 years applying statistical modelling and ML techniques to solve business problems. Skilled in Python, scikit-learn, and data visualisation. Available immediately.",
        resume_url="seeded", resume_filename="sneha_reddy_resume.pdf",
        desired_role="Data Scientist",
        desired_salary_min=1200000, desired_salary_max=1800000,
        desired_location="Bangalore, India",
        open_to_remote=True, notice_period_days=0, years_of_experience=3.0,
        profile_strength=100,
    )
    cp5 = CandidateProfile(
        id=CP5, user_id=U_DEV5,
        full_name="Aditya Kumar", phone="+91-9876543205", location="Pune, India",
        headline="DevOps Engineer | Kubernetes | Terraform | AWS | 5 Years",
        summary="DevOps engineer with 5 years automating infrastructure and building robust CI/CD pipelines. Kubernetes cluster operator, Terraform power-user, and AWS certified solutions architect.",
        resume_url="seeded", resume_filename="aditya_kumar_resume.pdf",
        desired_role="DevOps Engineer",
        desired_salary_min=2000000, desired_salary_max=2800000,
        desired_location="Pune, India",
        open_to_remote=True, notice_period_days=30, years_of_experience=5.0,
        profile_strength=100,
    )
    cp6 = CandidateProfile(
        id=CP6, user_id=U_DEV6,
        full_name="Kavya Nair", phone="+91-9876543206", location="Chennai, India",
        headline="Mobile Developer | Flutter | iOS | Android | 2 Years",
        summary="Mobile developer with 2 years building cross-platform Flutter apps. Published 3 apps on Google Play and App Store. Strong UI/UX sensibility and experience with BLoC state management.",
        resume_url="seeded", resume_filename="kavya_nair_resume.pdf",
        desired_role="Mobile Developer",
        desired_salary_min=900000, desired_salary_max=1400000,
        desired_location="Chennai, India",
        open_to_remote=True, notice_period_days=15, years_of_experience=2.0,
        profile_strength=100,
    )
    cp7 = CandidateProfile(
        id=CP7, user_id=U_DEV7,
        full_name="Vikram Singh", phone="+91-9876543207", location="Delhi, India",
        headline="Principal Full Stack Developer | .NET | React | Azure | 10 Years",
        summary="Principal engineer and technical lead with 10 years delivering complex full stack solutions on .NET and React. MBA background helps bridge engineering and business stakeholder communication.",
        resume_url="seeded", resume_filename="vikram_singh_resume.pdf",
        desired_role="Principal Full Stack Developer",
        desired_salary_min=3500000, desired_salary_max=5000000,
        desired_location="Delhi, India",
        open_to_remote=True, notice_period_days=90, years_of_experience=10.0,
        profile_strength=100,
    )
    cp8 = CandidateProfile(
        id=CP8, user_id=U_DEV8,
        full_name="Meena Iyer", phone="+91-9876543208", location="Bangalore, India",
        headline="QA Lead | Selenium | Cypress | Test Automation | 7 Years",
        summary="Quality assurance professional with 7 years building end-to-end test automation frameworks. Experienced QA lead who has managed teams of 5 engineers and reduced regression time by 70 percent.",
        resume_url="seeded", resume_filename="meena_iyer_resume.pdf",
        desired_role="QA Lead",
        desired_salary_min=1600000, desired_salary_max=2200000,
        desired_location="Bangalore, India",
        open_to_remote=False, notice_period_days=30, years_of_experience=7.0,
        profile_strength=100,
    )
    cp9 = CandidateProfile(
        id=CP9, user_id=U_DEV9,
        full_name="Suresh Babu", phone="+91-9876543209", location="Hyderabad, India",
        headline="Full Stack Developer | React Native | GraphQL | Node.js | 4 Years",
        summary="Full stack developer with 4 years building mobile-first products with React Native and GraphQL APIs on Node.js. Comfortable across the stack from database design to UI implementation.",
        resume_url="seeded", resume_filename="suresh_babu_resume.pdf",
        desired_role="Full Stack Developer",
        desired_salary_min=1300000, desired_salary_max=1800000,
        desired_location="Hyderabad, India",
        open_to_remote=True, notice_period_days=30, years_of_experience=4.0,
        profile_strength=100,
    )
    cp10 = CandidateProfile(
        id=CP10, user_id=U_DEV10,
        full_name="Divya Krishnan", phone="+91-9876543210", location="Chennai, India",
        headline="Senior Data Engineer | Apache Spark | Kafka | AWS | 6 Years",
        summary="Senior data engineer with 6 years architecting large-scale data pipelines using Apache Spark and Kafka. Built petabyte-scale data lakes on AWS and enabled real-time analytics for Fortune 500 clients.",
        resume_url="seeded", resume_filename="divya_krishnan_resume.pdf",
        desired_role="Data Engineer",
        desired_salary_min=2200000, desired_salary_max=3000000,
        desired_location="Chennai, India",
        open_to_remote=False, notice_period_days=45, years_of_experience=6.0,
        profile_strength=100,
    )
    all_profiles = [cp1, cp2, cp3, cp4, cp5, cp6, cp7, cp8, cp9, cp10]
    session.add_all(all_profiles)
    await session.flush()
    log.info("seed2_candidate_profiles_created", count=len(all_profiles))

    # Work Experience
    work_experiences = [
        WorkExperience(
            id=uuid.uuid4(),
            candidate_id=CP1,
            company_name="Infosys", job_title="Senior Software Engineer",
            location="Bangalore, India", is_current=True,
            start_date=dt(2021, 6, 1),
            description="Led development of Python microservices on AWS. Reduced API latency by 40 percent.",
            achievements=["Reduced API latency by 40 percent", "Mentored 3 junior engineers", "Introduced async patterns with FastAPI"],
        ),
        WorkExperience(
            id=uuid.uuid4(),
            candidate_id=CP1,
            company_name="Wipro", job_title="Software Engineer",
            location="Bangalore, India", is_current=False,
            start_date=dt(2018, 7, 1),
            end_date=dt(2021, 5, 28),
            description="Built Django REST APIs for an e-commerce platform serving 500K users.",
            achievements=["Improved checkout conversion by 12 percent", "Migrated legacy PHP services to Django"],
        ),
        WorkExperience(
            id=uuid.uuid4(),
            candidate_id=CP2,
            company_name="Razorpay", job_title="Frontend Engineer",
            location="Mumbai, India", is_current=True,
            start_date=dt(2022, 3, 1),
            description="Built React components for Razorpay Dashboard serving 300K merchants.",
            achievements=["Reduced bundle size by 35 percent", "Implemented design system used across 4 products"],
        ),
        WorkExperience(
            id=uuid.uuid4(),
            candidate_id=CP2,
            company_name="Tata Consultancy Services", job_title="Junior Frontend Developer",
            location="Mumbai, India", is_current=False,
            start_date=dt(2020, 8, 1),
            end_date=dt(2022, 2, 28),
            description="Developed Angular and React UIs for banking clients.",
            achievements=["Delivered WCAG 2.1 AA compliance for 2 banking portals"],
        ),
        WorkExperience(
            id=uuid.uuid4(),
            candidate_id=CP3,
            company_name="HCL Technologies", job_title="Technical Lead",
            location="Hyderabad, India", is_current=True,
            start_date=dt(2020, 1, 1),
            description="Technical lead for a team of 8 Java engineers building fintech microservices.",
            achievements=["Architected event-driven system processing 50K TPS", "Led migration from monolith to microservices"],
        ),
        WorkExperience(
            id=uuid.uuid4(),
            candidate_id=CP3,
            company_name="Cognizant", job_title="Senior Java Developer",
            location="Hyderabad, India", is_current=False,
            start_date=dt(2016, 6, 1),
            end_date=dt(2019, 12, 28),
            description="Developed Spring Boot services for an insurance claims platform.",
            achievements=["Reduced claims processing time by 60 percent", "Introduced Kafka for async processing"],
        ),
        WorkExperience(
            id=uuid.uuid4(),
            candidate_id=CP4,
            company_name="Mu Sigma", job_title="Data Scientist",
            location="Bangalore, India", is_current=True,
            start_date=dt(2023, 1, 1),
            description="Built churn prediction and recommendation models for retail clients.",
            achievements=["Improved churn model F1 score from 0.72 to 0.89", "Deployed 4 models to production"],
        ),
        WorkExperience(
            id=uuid.uuid4(),
            candidate_id=CP4,
            company_name="Accenture", job_title="Data Analyst",
            location="Bangalore, India", is_current=False,
            start_date=dt(2021, 6, 1),
            end_date=dt(2022, 12, 28),
            description="Analysed customer data and built dashboards in Tableau.",
            achievements=["Automated 15 weekly reports saving 20 hours per week"],
        ),
        WorkExperience(
            id=uuid.uuid4(),
            candidate_id=CP5,
            company_name="Persistent Systems", job_title="Senior DevOps Engineer",
            location="Pune, India", is_current=True,
            start_date=dt(2021, 4, 1),
            description="Manages Kubernetes clusters (50+ nodes) and builds Terraform modules for AWS.",
            achievements=["Cut infra costs by 30 percent via spot instance optimisation", "Zero-downtime deployments via blue/green strategy"],
        ),
        WorkExperience(
            id=uuid.uuid4(),
            candidate_id=CP5,
            company_name="Tech Mahindra", job_title="DevOps Engineer",
            location="Pune, India", is_current=False,
            start_date=dt(2019, 7, 1),
            end_date=dt(2021, 3, 28),
            description="Maintained Jenkins pipelines and Docker-based microservices.",
            achievements=["Reduced build times from 45min to 8min", "Introduced Helm charts for all services"],
        ),
        WorkExperience(
            id=uuid.uuid4(),
            candidate_id=CP6,
            company_name="Zoho", job_title="Mobile Developer",
            location="Chennai, India", is_current=True,
            start_date=dt(2024, 1, 1),
            description="Develops Flutter features for Zoho mobile CRM app with 2M+ downloads.",
            achievements=["Shipped offline-sync feature reducing support tickets by 25 percent"],
        ),
        WorkExperience(
            id=uuid.uuid4(),
            candidate_id=CP6,
            company_name="Freshworks", job_title="Junior Mobile Developer",
            location="Chennai, India", is_current=False,
            start_date=dt(2022, 6, 1),
            end_date=dt(2023, 12, 28),
            description="Built and maintained Flutter UI components for Freshdesk mobile.",
            achievements=["Improved app startup time by 40 percent via lazy initialisation"],
        ),
        WorkExperience(
            id=uuid.uuid4(),
            candidate_id=CP7,
            company_name="Microsoft India", job_title="Principal Software Engineer",
            location="Delhi, India", is_current=True,
            start_date=dt(2019, 9, 1),
            description="Principal engineer for Azure-hosted enterprise SaaS platform. Leads 12-person team.",
            achievements=["Delivered platform handling 10M daily users", "Reduced Azure spend by 200K USD per year", "Filed 2 patents"],
        ),
        WorkExperience(
            id=uuid.uuid4(),
            candidate_id=CP7,
            company_name="Capgemini", job_title="Senior Full Stack Developer",
            location="Delhi, India", is_current=False,
            start_date=dt(2015, 6, 1),
            end_date=dt(2019, 8, 28),
            description="Built .NET and React solutions for UK banking and insurance clients.",
            achievements=["Led migration of legacy WinForms app to React SPA", "Improved system uptime from 99.5 to 99.97 percent"],
        ),
        WorkExperience(
            id=uuid.uuid4(),
            candidate_id=CP8,
            company_name="Flipkart", job_title="QA Lead",
            location="Bangalore, India", is_current=True,
            start_date=dt(2020, 2, 1),
            description="Leads QA team of 5 for Flipkart seller portal. Owns automation strategy.",
            achievements=["Reduced regression cycle from 5 days to 6 hours", "90 percent automation coverage achieved"],
        ),
        WorkExperience(
            id=uuid.uuid4(),
            candidate_id=CP8,
            company_name="Mindtree", job_title="Senior QA Engineer",
            location="Bangalore, India", is_current=False,
            start_date=dt(2017, 5, 1),
            end_date=dt(2020, 1, 28),
            description="Built Selenium and REST Assured test suites for e-commerce clients.",
            achievements=["Created reusable automation framework adopted by 4 projects"],
        ),
        WorkExperience(
            id=uuid.uuid4(),
            candidate_id=CP9,
            company_name="Swiggy", job_title="Full Stack Developer",
            location="Hyderabad, India", is_current=True,
            start_date=dt(2022, 5, 1),
            description="Builds React Native features for Swiggy partner app used by 1.5M restaurants.",
            achievements=["Shipped order tracking feature reducing support calls by 30 percent", "Migrated REST endpoints to GraphQL"],
        ),
        WorkExperience(
            id=uuid.uuid4(),
            candidate_id=CP9,
            company_name="Hexaware", job_title="Software Developer",
            location="Hyderabad, India", is_current=False,
            start_date=dt(2020, 7, 1),
            end_date=dt(2022, 4, 28),
            description="Developed Node.js APIs and React Native UI for logistics mobile app.",
            achievements=["Reduced API response time by 50 percent via caching", "Delivered app from scratch in 6 months"],
        ),
        WorkExperience(
            id=uuid.uuid4(),
            candidate_id=CP10,
            company_name="Amazon India", job_title="Senior Data Engineer",
            location="Chennai, India", is_current=True,
            start_date=dt(2021, 3, 1),
            description="Builds and maintains Spark-based ETL pipelines processing 5TB daily on AWS EMR.",
            achievements=["Reduced pipeline cost by 45 percent via Spark optimisation", "Built real-time Kafka pipeline for inventory updates"],
        ),
        WorkExperience(
            id=uuid.uuid4(),
            candidate_id=CP10,
            company_name="Tata Data Sciences", job_title="Data Engineer",
            location="Chennai, India", is_current=False,
            start_date=dt(2018, 8, 1),
            end_date=dt(2021, 2, 28),
            description="Built PySpark batch jobs and managed Hadoop clusters for telecom analytics.",
            achievements=["Processed 2TB daily logs for network anomaly detection", "Reduced job failure rate from 8 to 0.3 percent"],
        ),
    ]
    session.add_all(work_experiences)
    await session.flush()
    log.info("seed2_work_experiences_created", count=len(work_experiences))

    # Education
    educations = [
        Education(
            id=uuid.uuid4(),
            candidate_id=CP1,
            institution="IIT Bombay",
            degree="B.Tech", field_of_study="Computer Science and Engineering",
            grade="8.7 CGPA", start_year=2014, end_year=2018,
        ),
        Education(
            id=uuid.uuid4(),
            candidate_id=CP2,
            institution="BITS Pilani",
            degree="B.E.", field_of_study="Computer Science",
            grade="8.2 CGPA", start_year=2016, end_year=2020,
        ),
        Education(
            id=uuid.uuid4(),
            candidate_id=CP3,
            institution="NIT Warangal",
            degree="M.Tech", field_of_study="Software Engineering",
            grade="8.9 CGPA", start_year=2014, end_year=2016,
        ),
        Education(
            id=uuid.uuid4(),
            candidate_id=CP3,
            institution="Osmania University",
            degree="B.Tech", field_of_study="Information Technology",
            grade="7.8 CGPA", start_year=2010, end_year=2014,
        ),
        Education(
            id=uuid.uuid4(),
            candidate_id=CP4,
            institution="University of Hyderabad",
            degree="B.Sc.", field_of_study="Statistics and Data Science",
            grade="9.1 CGPA", start_year=2018, end_year=2021,
        ),
        Education(
            id=uuid.uuid4(),
            candidate_id=CP5,
            institution="VIT University",
            degree="B.Tech", field_of_study="Computer Science and Engineering",
            grade="8.5 CGPA", start_year=2015, end_year=2019,
        ),
        Education(
            id=uuid.uuid4(),
            candidate_id=CP6,
            institution="Anna University",
            degree="BCA", field_of_study="Computer Applications",
            grade="8.0 CGPA", start_year=2019, end_year=2022,
        ),
        Education(
            id=uuid.uuid4(),
            candidate_id=CP7,
            institution="IIM Calcutta",
            degree="MBA", field_of_study="Technology Management",
            grade="3.8 GPA", start_year=2013, end_year=2015,
        ),
        Education(
            id=uuid.uuid4(),
            candidate_id=CP7,
            institution="Delhi Technological Univ",
            degree="B.Tech", field_of_study="Computer Engineering",
            grade="8.3 CGPA", start_year=2009, end_year=2013,
        ),
        Education(
            id=uuid.uuid4(),
            candidate_id=CP8,
            institution="RV College of Engineering",
            degree="B.E.", field_of_study="Computer Science",
            grade="7.9 CGPA", start_year=2014, end_year=2018,
        ),
        Education(
            id=uuid.uuid4(),
            candidate_id=CP9,
            institution="JNTU Hyderabad",
            degree="B.Tech", field_of_study="Electronics and Communication",
            grade="7.6 CGPA", start_year=2016, end_year=2020,
        ),
        Education(
            id=uuid.uuid4(),
            candidate_id=CP10,
            institution="IIT Madras",
            degree="M.Tech", field_of_study="Data Science and Engineering",
            grade="9.2 CGPA", start_year=2016, end_year=2018,
        ),
        Education(
            id=uuid.uuid4(),
            candidate_id=CP10,
            institution="PSG College of Technology",
            degree="B.Tech", field_of_study="Information Technology",
            grade="8.6 CGPA", start_year=2012, end_year=2016,
        ),
    ]
    session.add_all(educations)
    await session.flush()
    log.info("seed2_educations_created", count=len(educations))

    # Skills
    _skills_raw = [
        (CP1, "Python", 5, 6.0),
        (CP1, "Django", 5, 5.0),
        (CP1, "FastAPI", 4, 3.0),
        (CP1, "AWS", 4, 4.0),
        (CP1, "PostgreSQL", 4, 5.0),
        (CP1, "Docker", 4, 3.0),
        (CP1, "Redis", 3, 2.0),
        (CP2, "React", 5, 4.0),
        (CP2, "TypeScript", 5, 3.0),
        (CP2, "Node.js", 4, 3.0),
        (CP2, "JavaScript", 5, 4.0),
        (CP2, "Tailwind CSS", 4, 2.0),
        (CP2, "GraphQL", 3, 2.0),
        (CP3, "Java", 5, 8.0),
        (CP3, "Spring Boot", 5, 6.0),
        (CP3, "Microservices", 5, 5.0),
        (CP3, "Kafka", 4, 4.0),
        (CP3, "MySQL", 4, 7.0),
        (CP3, "Azure", 3, 3.0),
        (CP3, "Docker", 4, 4.0),
        (CP4, "Python", 5, 3.0),
        (CP4, "Machine Learning", 5, 3.0),
        (CP4, "scikit-learn", 4, 3.0),
        (CP4, "pandas", 5, 3.0),
        (CP4, "SQL", 4, 3.0),
        (CP4, "Tableau", 3, 2.0),
        (CP5, "Kubernetes", 5, 4.0),
        (CP5, "Terraform", 5, 4.0),
        (CP5, "AWS", 5, 5.0),
        (CP5, "Docker", 5, 5.0),
        (CP5, "CI/CD", 5, 5.0),
        (CP5, "Helm", 4, 3.0),
        (CP5, "Ansible", 3, 2.0),
        (CP6, "Flutter", 5, 2.0),
        (CP6, "Dart", 5, 2.0),
        (CP6, "iOS Development", 3, 1.5),
        (CP6, "Android Development", 4, 2.0),
        (CP6, "BLoC", 4, 2.0),
        (CP6, "REST APIs", 4, 2.0),
        (CP7, ".NET", 5, 10.0),
        (CP7, "C#", 5, 10.0),
        (CP7, "React", 4, 6.0),
        (CP7, "Azure", 5, 7.0),
        (CP7, "Microservices", 5, 6.0),
        (CP7, "SQL Server", 4, 9.0),
        (CP7, "TypeScript", 4, 4.0),
        (CP8, "Selenium", 5, 7.0),
        (CP8, "Cypress", 5, 4.0),
        (CP8, "Python", 4, 5.0),
        (CP8, "Postman", 5, 6.0),
        (CP8, "JIRA", 5, 7.0),
        (CP8, "REST Assured", 4, 5.0),
        (CP8, "TestNG", 4, 5.0),
        (CP9, "React Native", 5, 4.0),
        (CP9, "GraphQL", 5, 3.0),
        (CP9, "Node.js", 4, 4.0),
        (CP9, "JavaScript", 5, 4.0),
        (CP9, "MongoDB", 3, 3.0),
        (CP9, "TypeScript", 4, 2.0),
        (CP10, "Apache Spark", 5, 6.0),
        (CP10, "Kafka", 5, 5.0),
        (CP10, "Python", 5, 6.0),
        (CP10, "AWS", 5, 5.0),
        (CP10, "PySpark", 5, 6.0),
        (CP10, "Hadoop", 4, 5.0),
        (CP10, "SQL", 4, 6.0),
    ]
    candidate_skills = [
        CandidateSkill(id=uuid.uuid4(), candidate_id=cid, skill_name=skill, proficiency=prof, years_exp=yrs)
        for cid, skill, prof, yrs in _skills_raw
    ]
    session.add_all(candidate_skills)
    await session.flush()
    log.info("seed2_skills_created", count=len(candidate_skills))

    # Applications helper
    def get_applied_stage(job_id):
        for s in all_stages:
            if s.job_id == job_id and s.stage_name == "Applied":
                return s.id
        return None

    # Applications
    applications = [
        Application(
            id=uuid.uuid4(),
            job_id=J1, candidate_id=CP1,
            status=ApplicationStatus.SCREENING,
            cover_letter=("I am thrilled to apply for the Senior Python Developer role at TechCorp. With 6 years of Python and Django experience on AWS, I can contribute immediately."),
            resume_url="seeded",
            timeline=[{"status": "applied", "timestamp": dt(2026, 2, 10).isoformat(), "note": "Applied via portal"}, {"status": "screening", "timestamp": dt(2026, 2, 12).isoformat(), "note": "Moved to screening by HR"}],
            pipeline_stage_id=get_applied_stage(J1),
            rating=4,
        ),
        Application(
            id=uuid.uuid4(),
            job_id=J2, candidate_id=CP2,
            status=ApplicationStatus.INTERVIEW,
            cover_letter=("As a React and TypeScript engineer with 4 years at Razorpay, I have built high-traffic dashboards used by hundreds of thousands of merchants."),
            resume_url="seeded",
            timeline=[{"status": "applied", "timestamp": dt(2026, 2, 8).isoformat(), "note": "Applied via portal"}, {"status": "screening", "timestamp": dt(2026, 2, 10).isoformat(), "note": "Shortlisted"}, {"status": "interview", "timestamp": dt(2026, 2, 14).isoformat(), "note": "Technical round scheduled"}],
            pipeline_stage_id=get_applied_stage(J2),
            rating=5,
        ),
        Application(
            id=uuid.uuid4(),
            job_id=J3, candidate_id=CP4,
            status=ApplicationStatus.APPLIED,
            cover_letter=("I am passionate about applying machine learning to real-world business problems. My experience at Mu Sigma with churn prediction aligns closely with DataAI Corp."),
            resume_url="seeded",
            timeline=[{"status": "applied", "timestamp": dt(2026, 2, 20).isoformat(), "note": "Applied via portal"}],
            pipeline_stage_id=get_applied_stage(J3),
            rating=None,
        ),
        Application(
            id=uuid.uuid4(),
            job_id=J4, candidate_id=CP5,
            status=ApplicationStatus.OFFER,
            cover_letter=("5 years of Kubernetes and Terraform on AWS make me an ideal fit for CloudSys. I have managed 50+ node clusters and cut infrastructure costs by 30 percent."),
            resume_url="seeded",
            timeline=[{"status": "applied", "timestamp": dt(2026, 2, 1).isoformat(), "note": "Applied via portal"}, {"status": "screening", "timestamp": dt(2026, 2, 3).isoformat(), "note": "Passed screening"}, {"status": "interview", "timestamp": dt(2026, 2, 7).isoformat(), "note": "Technical interview completed"}, {"status": "offer", "timestamp": dt(2026, 2, 15).isoformat(), "note": "Offer letter sent"}],
            pipeline_stage_id=get_applied_stage(J4),
            rating=5,
        ),
        Application(
            id=uuid.uuid4(),
            job_id=J5, candidate_id=CP6,
            status=ApplicationStatus.SCREENING,
            cover_letter=("As a Flutter developer at Zoho with 2 published apps on both stores, I am excited to bring my cross-platform mobile skills to AppWorks."),
            resume_url="seeded",
            timeline=[{"status": "applied", "timestamp": dt(2026, 2, 18).isoformat(), "note": "Applied via portal"}, {"status": "screening", "timestamp": dt(2026, 2, 20).isoformat(), "note": "Portfolio reviewed"}],
            pipeline_stage_id=get_applied_stage(J5),
            rating=4,
        ),
        Application(
            id=uuid.uuid4(),
            job_id=J6, candidate_id=CP3,
            status=ApplicationStatus.INTERVIEW,
            cover_letter=("With 8 years of Java/Spring Boot and a track record of architecting event-driven systems at scale, I am well positioned for EnterpriseTech."),
            resume_url="seeded",
            timeline=[{"status": "applied", "timestamp": dt(2026, 2, 5).isoformat(), "note": "Applied via portal"}, {"status": "screening", "timestamp": dt(2026, 2, 7).isoformat(), "note": "Passed screening"}, {"status": "interview", "timestamp": dt(2026, 2, 12).isoformat(), "note": "First round interview scheduled"}],
            pipeline_stage_id=get_applied_stage(J6),
            rating=5,
        ),
        Application(
            id=uuid.uuid4(),
            job_id=J7, candidate_id=CP8,
            status=ApplicationStatus.APPLIED,
            cover_letter=("7 years in QA with a proven track record of leading automation initiatives at Flipkart makes me an ideal candidate for QualityFirst QA Lead role."),
            resume_url="seeded",
            timeline=[{"status": "applied", "timestamp": dt(2026, 2, 22).isoformat(), "note": "Applied via portal"}],
            pipeline_stage_id=get_applied_stage(J7),
            rating=None,
        ),
        Application(
            id=uuid.uuid4(),
            job_id=J8, candidate_id=CP7,
            status=ApplicationStatus.HIRED,
            cover_letter=("10 years of .NET and React full stack experience combined with remote work expertise and Azure cloud skills align perfectly with RemoteCo."),
            resume_url="seeded",
            timeline=[{"status": "applied", "timestamp": dt(2026, 1, 20).isoformat(), "note": "Applied via portal"}, {"status": "screening", "timestamp": dt(2026, 1, 22).isoformat(), "note": "Background check passed"}, {"status": "interview", "timestamp": dt(2026, 1, 27).isoformat(), "note": "Technical assessment completed"}, {"status": "offer", "timestamp": dt(2026, 2, 3).isoformat(), "note": "Offer negotiated"}, {"status": "hired", "timestamp": dt(2026, 2, 10).isoformat(), "note": "Offer accepted - joining March 1"}],
            pipeline_stage_id=get_applied_stage(J8),
            rating=5,
        ),
        Application(
            id=uuid.uuid4(),
            job_id=J9, candidate_id=CP10,
            status=ApplicationStatus.SCREENING,
            cover_letter=("6 years of Apache Spark and Kafka data engineering experience at Amazon makes me a strong candidate for DataOps Inc Data Engineer position in Chennai."),
            resume_url="seeded",
            timeline=[{"status": "applied", "timestamp": dt(2026, 2, 16).isoformat(), "note": "Applied via portal"}, {"status": "screening", "timestamp": dt(2026, 2, 18).isoformat(), "note": "Resume shortlisted"}],
            pipeline_stage_id=get_applied_stage(J9),
            rating=4,
        ),
        Application(
            id=uuid.uuid4(),
            job_id=J10, candidate_id=CP4,
            status=ApplicationStatus.REJECTED,
            cover_letter=("I am eager to transition into ML engineering and believe my strong data science foundation in Python and scikit-learn will be valuable to AICorp."),
            resume_url="seeded",
            timeline=[{"status": "applied", "timestamp": dt(2026, 2, 3).isoformat(), "note": "Applied via portal"}, {"status": "screening", "timestamp": dt(2026, 2, 5).isoformat(), "note": "Reviewed"}, {"status": "rejected", "timestamp": dt(2026, 2, 8).isoformat(), "note": "Insufficient MLOps experience for senior role"}],
            pipeline_stage_id=get_applied_stage(J10),
            rating=2,
        ),
    ]
    session.add_all(applications)
    await session.flush()
    log.info("seed2_applications_created", count=len(applications))

    await session.commit()
    log.info(
        "seed2_complete",
        hr_users=len(hr_users), dev_users=len(dev_users), companies=len(companies),
        jobs=len(jobs), pipeline_stages=len(all_stages), profiles=len(all_profiles),
        work_experiences=len(work_experiences), educations=len(educations),
        skills=len(candidate_skills), applications=len(applications),
    )



async def seed3(session) -> None:
    """Idempotent: add CandidateProfile + applications for the original
    candidate@donehr.com test account (U_CAND / CP0)."""
    existing_profile = await session.scalar(
        select(CandidateProfile).where(CandidateProfile.user_id == U_CAND)
    )
    if existing_profile:
        log.info("seed3_skipped", reason="candidate@donehr.com profile already exists")
        return

    # Require jobs to exist
    job_count = await session.scalar(select(func.count()).select_from(Job))
    if job_count == 0:
        log.info("seed3_skipped", reason="no jobs in DB — run seed2 first")
        return

    profile = CandidateProfile(
        id=CP0,
        user_id=U_CAND,
        full_name="Demo Candidate",
        headline="Full Stack Developer | 5 Years Experience",
        summary=(
            "Passionate full stack developer with 5 years of experience building "
            "scalable web applications. Proficient in Python, React, and PostgreSQL."
        ),
        location="Bangalore, India",
        phone="+91-9876543200",
        years_of_experience=5.0,
        desired_role="Full Stack Developer",
        desired_salary_min=800000,
        desired_salary_max=1500000,
        notice_period_days=30,
        open_to_remote=True,
        work_preference="hybrid",
        profile_strength=78,
    )
    session.add(profile)
    await session.flush()

    skills = [
        CandidateSkill(id=uuid.uuid4(), candidate_id=CP0, skill_name="Python",     proficiency=80, years_exp=4.0),
        CandidateSkill(id=uuid.uuid4(), candidate_id=CP0, skill_name="React",      proficiency=75, years_exp=3.0),
        CandidateSkill(id=uuid.uuid4(), candidate_id=CP0, skill_name="Node.js",    proficiency=70, years_exp=3.0),
        CandidateSkill(id=uuid.uuid4(), candidate_id=CP0, skill_name="PostgreSQL", proficiency=72, years_exp=4.0),
        CandidateSkill(id=uuid.uuid4(), candidate_id=CP0, skill_name="Docker",     proficiency=65, years_exp=2.0),
    ]
    session.add_all(skills)

    edu = Education(
        id=uuid.uuid4(), candidate_id=CP0,
        institution="Mumbai University",
        degree="B.Tech", field_of_study="Computer Science",
        grade="7.5 CGPA", start_year=2016, end_year=2020,
    )
    session.add(edu)

    exp = WorkExperience(
        id=uuid.uuid4(), candidate_id=CP0,
        company_name="Infosys Ltd", job_title="Software Developer",
        location="Bangalore, India", is_current=True,
        start_date=dt(2020, 7, 1), end_date=None,
        description="Building enterprise web apps with React and Python.",
        achievements=["Reduced API response time by 40%", "Led Docker migration"],
    )
    session.add(exp)
    await session.flush()

    # Get pipeline stage IDs for J1 and J3
    stage_j1 = await session.scalar(
        select(PipelineStage).where(PipelineStage.job_id == J1, PipelineStage.stage_order == 0)
    )
    stage_j3 = await session.scalar(
        select(PipelineStage).where(PipelineStage.job_id == J3, PipelineStage.stage_order == 1)
    )

    apps = []
    if stage_j1:
        apps.append(Application(
            id=uuid.uuid4(), job_id=J1, candidate_id=CP0,
            status=ApplicationStatus.APPLIED,
            cover_letter="5+ years full stack experience in Python and React. Eager to contribute to TechCorp.",
            resume_url="seeded",
            timeline=[{"status": "applied", "timestamp": dt(2026, 2, 20).isoformat(), "note": "Applied via portal"}],
            pipeline_stage_id=stage_j1.id,
        ))
    if stage_j3:
        apps.append(Application(
            id=uuid.uuid4(), job_id=J3, candidate_id=CP0,
            status=ApplicationStatus.SCREENING,
            cover_letter="Strong Python background and ML interest make me a great fit for this role.",
            resume_url="seeded",
            timeline=[
                {"status": "applied",   "timestamp": dt(2026, 2, 15).isoformat(), "note": "Applied via portal"},
                {"status": "screening", "timestamp": dt(2026, 2, 17).isoformat(), "note": "Resume shortlisted"},
            ],
            pipeline_stage_id=stage_j3.id,
        ))

    if apps:
        session.add_all(apps)
    await session.commit()
    log.info("seed3_complete", profile_id=str(CP0), applications=len(apps))


# ---------------------------------------------------------------------------
# Module 8: Admin portal seed
# ---------------------------------------------------------------------------

async def seed_admin_users() -> None:
    """Seed the three default admin portal users (idempotent)."""
    from app.models.admin import AdminRole, AdminUser
    from sqlalchemy import select

    ADMIN_SEEDS = [
        {
            "id": uuid.UUID("00000000-0000-0000-0000-a00000000001"),
            "email": "superadmin@donehr.com",
            "password": "SuperAdmin@2024!",
            "pin": "123456",
            "full_name": "Super Admin",
            "role": AdminRole.SUPERADMIN,
        },
        {
            "id": uuid.UUID("00000000-0000-0000-0000-a00000000002"),
            "email": "admin@donehr.com",
            "password": "Admin@2024!",
            "pin": "654321",
            "full_name": "Platform Admin",
            "role": AdminRole.ADMIN,
        },
        {
            "id": uuid.UUID("00000000-0000-0000-0000-a00000000003"),
            "email": "elite@donehr.com",
            "password": "Elite@2024!",
            "pin": "111111",
            "full_name": "Elite Viewer",
            "role": AdminRole.ELITE_ADMIN,
        },
    ]

    async with AsyncSessionLocal() as session:
        for seed_data in ADMIN_SEEDS:
            result = await session.execute(
                select(AdminUser).where(AdminUser.email == seed_data["email"])
            )
            existing = result.scalar_one_or_none()
            if existing:
                log.info("admin_seed_skipped", email=seed_data["email"])
                continue
            admin = AdminUser(
                id=seed_data["id"],
                email=seed_data["email"],
                password_hash=hash_password(seed_data["password"]),
                pin_hash=hash_password(seed_data["pin"]),
                full_name=seed_data["full_name"],
                role=seed_data["role"],
                is_active=True,
            )
            session.add(admin)
            log.info("admin_seed_created", email=seed_data["email"], role=seed_data["role"].value)
        await session.commit()
    log.info("admin_seed_complete")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def seed() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count()).select_from(User))
        user_count = result.scalar_one()

        if user_count == 0:
            log.info("seed_running", phase="seed1+seed2")
            await seed1(session)
            await session.flush()
            await seed2(session)
        elif user_count <= 4:
            log.info("seed_running", phase="seed2_only", existing_users=user_count)
            await seed2(session)
        else:
            log.info(
                "seed_skipped",
                reason="extended seed already ran",
                user_count=user_count,
            )

    # seed3 always runs — idempotent (adds data for candidate@donehr.com if missing)
    async with AsyncSessionLocal() as session:
        await seed3(session)

    # seed admin portal users (Module 8) — always idempotent
    await seed_admin_users()


if __name__ == "__main__":
    asyncio.run(seed())
