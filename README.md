# FindUs (doneHr) — AI-Powered HR Portal

> Full-stack recruiting platform — FastAPI · Next.js 14 · PostgreSQL 15 · Redis 7 · Groq AI · Docker

---

## Quick Start

### Prerequisites

| Tool | Minimum version |
|------|----------------|
| Docker | 24.x |
| Docker Compose | 2.x (`docker compose` CLI) |
| Git | 2.x |

### 1. Clone & configure

```bash
git clone https://github.com/saurabhsrb23/FINDuS-HR-Portal.git
cd FINDuS-HR-Portal

# Copy the example env and fill in your secrets
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY, ADMIN_JWT_SECRET, GROQ_API_KEY
```

### 2. Build & run

```bash
docker compose up --build -d
```

Services spin up in dependency order:
`postgres` → `redis` → `backend` → `frontend`

### 3. Seed test data

```bash
docker compose exec backend python seed.py
```

### 4. Verify

| Endpoint | Expected |
|----------|---------|
| `GET http://localhost:8001/health` | `{"status":"ok"}` |
| `GET http://localhost:8001/docs` | Swagger UI |
| `GET http://localhost:3000` | Next.js login page |

### 5. Apply migrations

```bash
docker compose exec backend alembic upgrade head
```

---

## Test Credentials

| Role | Email | Password |
|------|-------|----------|
| Elite Admin | elite@donehr.com | Elite@Admin1! |
| Admin | admin@donehr.com | Admin@1234! |
| HR Admin | hr@donehr.com | Hr@123456! |
| Candidate | candidate@donehr.com | Candidate@1! |

---

## Project Structure

```
Portal/
├── docker-compose.yml              # All services (postgres, redis, backend, frontend)
├── .env                            # Runtime secrets (not committed)
├── .env.example                    # Template
│
├── backend/
│   ├── Dockerfile
│   ├── start.sh                    # migrate → seed → celery worker → uvicorn
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── main.py                     # FastAPI app factory, router registration
│   ├── seed.py                     # Seeds 4 test users
│   ├── migrations/
│   │   ├── env.py                  # Async Alembic environment
│   │   └── versions/
│   │       ├── 001_users_companies_audit.py
│   │       ├── 002_jobs.py
│   │       ├── 003_candidates.py
│   │       └── 004_ai_summaries.py
│   └── app/
│       ├── core/
│       │   ├── config.py           # Pydantic Settings (GROQ_API_KEY etc.)
│       │   ├── security.py         # JWT create/verify, bcrypt
│       │   ├── dependencies.py     # get_db, get_current_user, require_role
│       │   ├── redis_client.py     # Redis singleton + token blacklist
│       │   └── rate_limiter.py     # slowapi (5/min login, 3/min forgot-password)
│       ├── models/                 # SQLAlchemy ORM models
│       │   ├── user.py
│       │   ├── company.py
│       │   ├── job.py
│       │   ├── candidate.py
│       │   ├── application.py
│       │   └── ai_summary.py       # Cached AI responses
│       ├── schemas/                # Pydantic v2 request/response schemas
│       │   ├── auth.py
│       │   ├── job.py
│       │   ├── candidate.py
│       │   ├── application.py
│       │   └── ai.py
│       ├── repositories/           # DB access layer
│       ├── services/               # Business logic
│       │   ├── auth_service.py
│       │   ├── job_service.py
│       │   ├── candidate_service.py
│       │   ├── application_service.py
│       │   └── ai_service.py       # All Groq operations
│       ├── routers/                # FastAPI route handlers
│       │   ├── auth.py
│       │   ├── jobs.py
│       │   ├── candidates.py
│       │   ├── applications.py
│       │   └── ai.py
│       └── tasks/                  # Celery background tasks
│           ├── email_tasks.py
│           ├── job_tasks.py
│           ├── job_alert_tasks.py
│           └── ai_tasks.py
│
└── frontend/
    ├── Dockerfile                  # Multi-stage Node 20 build
    ├── package.json
    ├── next.config.js
    └── src/
        ├── middleware.ts           # Edge auth + role guard
        ├── lib/
        │   ├── api.ts              # axios instance + 401 auto-refresh
        │   ├── auth.ts             # setToken/getToken/clearToken
        │   ├── jobsAPI.ts
        │   ├── candidateAPI.ts
        │   ├── applicationAPI.ts
        │   └── aiAPI.ts            # All AI endpoint wrappers
        ├── types/
        │   ├── job.ts
        │   ├── candidate.ts
        │   ├── application.ts
        │   └── ai.ts
        ├── components/
        │   ├── ai/
        │   │   ├── MatchScoreBadge.tsx      # Color-coded match score
        │   │   ├── AISummaryPanel.tsx       # HR candidate summary card
        │   │   ├── ComparisonModal.tsx      # Side-by-side candidate compare
        │   │   └── ChatbotWidget.tsx        # Floating AI career chatbot
        │   ├── jobs/
        │   └── analytics/
        └── app/
            ├── (auth)/login/               # Login page
            ├── (auth)/register/            # Register page
            ├── api/set-cookie/             # httpOnly JWT cookie handler
            └── (dashboard)/
                ├── layout.tsx              # Sidebar + chatbot injection
                └── dashboard/
                    ├── page.tsx            # Dashboard home
                    ├── profile/            # Candidate profile editor
                    ├── browse-jobs/        # Job search + apply flow
                    ├── my-applications/    # Application tracker
                    ├── job-alerts/         # Job alert CRUD
                    ├── resume-optimizer/   # AI resume analysis (candidate)
                    ├── jobs/               # HR job management
                    │   └── [id]/
                    │       ├── edit/
                    │       ├── pipeline/
                    │       ├── questionnaire/
                    │       └── ai-tools/   # HR AI tools (ranking, JD gen, rejection)
                    └── analytics/          # Recruiter analytics
```

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | asyncpg PostgreSQL connection |
| `REDIS_URL` | Redis connection |
| `SECRET_KEY` | JWT signing secret (≥ 32 chars) |
| `ADMIN_JWT_SECRET` | Admin-scoped JWT secret (≥ 32 chars) |
| `GROQ_API_KEY` | Groq AI API key (`gsk_...`) — all AI features |
| `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` | Email delivery |
| `FRONTEND_URL` | CORS allow-list |
| `NEXT_PUBLIC_API_URL` | Frontend → backend URL |

---

## Modules

### ✅ Module 1 — Foundation
Docker Compose orchestration, PostgreSQL + Redis setup, Pydantic Settings, structlog JSON logging, OpenTelemetry hooks, base models and health endpoint.

### ✅ Module 2 — Authentication
- JWT (HS256) access + refresh tokens stored in httpOnly cookies
- Register, login, logout, token refresh, email verification, password reset
- Redis token blacklist for immediate invalidation
- Rate limiting: 5/min on login, 3/min on forgot-password
- Admin portal with separate JWT secret (`aud=admin_portal`)
- Soft-delete users (never hard-deleted)

### ✅ Module 3 — Job Management
- Full CRUD for job postings (draft → published → paused → closed)
- Clone jobs, auto-archive expired postings via Celery
- 6-stage recruitment pipeline with drag-and-drop reordering
- Custom questionnaire builder per job (text, multiple-choice, yes/no, rating)
- Analytics: applications funnel, source breakdown, time-to-hire

### ✅ Module 4 — Candidate Features
- Candidate profile: personal info, work experience, education, certifications, projects, skills
- PDF resume upload with magic-bytes validation (5 MB limit)
- Profile strength score 0–100 (auto-recalculated on every mutation)
- Naukri-style job search with filters (role, location, job type, salary)
- Apply flow: cover letter + job-specific questionnaire answers
- Application tracker with visual timeline (JSONB event log)
- Duplicate application prevention (`UNIQUE(job_id, candidate_id)`)
- Job alerts: keyword/location subscriptions, Celery daily digest at 07:00 UTC
- Salary benchmark data (22 Indian IT roles/locations)
- Skill-based job recommendations

### ✅ Module 5 — AI Features (Groq)
All AI calls use **Groq** (`llama3-8b-8192` for speed, `llama-3.3-70b-versatile` for quality).
Results are cached in the `ai_summaries` table — `UNIQUE(entity_id, summary_type)`.
Groq failures return HTTP 503 gracefully and never crash the app.

| Feature | Who | Endpoint |
|---------|-----|---------|
| **Resume Parser** | Candidate | `POST /ai/parse-resume` — PDF → pdfplumber → Groq → auto-fills profile fields |
| **Resume Summarizer** | HR | `GET /ai/resume-summary/{candidate_id}` — 4-line summary, strengths, top skills |
| **Match Score** | HR | `GET /ai/match-score/{application_id}` — 0–100% score + grade A–F + skill breakdown |
| **Match Score (async)** | HR | `POST /ai/match-score/{application_id}/enqueue` — Celery background task |
| **Candidate Comparison** | HR | `POST /ai/compare-candidates` — side-by-side pros/cons table for 2–3 candidates |
| **Auto Ranking** | HR | `POST /ai/rank-applicants/{job_id}` — Celery ranks all applicants; `GET` fetches result |
| **JD Generator** | HR | `POST /ai/generate-jd` — role + keywords → full structured job description |
| **Rejection Email** | HR | `POST /ai/rejection-email` — empathetic rejection email draft |
| **Resume Optimizer** | Candidate | `GET /ai/optimize-resume` — overall/ATS/impact scores + tips + section feedback |
| **Career Chatbot** | Candidate | `POST /ai/chat` — context-aware floating chatbot (last 10 messages) |

**Frontend AI components:**
- `MatchScoreBadge` — color-coded grade badge with skill chips, auto-loads
- `AISummaryPanel` — HR summary card with regenerate button
- `ComparisonModal` — full-screen side-by-side candidate comparison
- `ChatbotWidget` — floating bottom-right chatbot for candidates
- `/dashboard/resume-optimizer` — score rings (Overall/ATS/Impact) + tips
- `/dashboard/jobs/[id]/ai-tools` — tabbed HR tools: Ranking, JD Generator, Rejection Email

---

## API Reference

Interactive Swagger docs: **http://localhost:8001/docs**

### Auth
| Method | Path | Auth |
|--------|------|------|
| POST | `/auth/register` | public |
| POST | `/auth/login` | public |
| POST | `/auth/refresh` | cookie |
| POST | `/auth/logout` | bearer |
| GET | `/auth/me` | bearer |
| POST | `/auth/verify-email` | public |
| POST | `/auth/forgot-password` | public |
| POST | `/auth/reset-password` | public |

### Jobs
| Method | Path | Auth |
|--------|------|------|
| GET | `/jobs/search` | public |
| POST | `/jobs` | HR |
| GET/PATCH/DELETE | `/jobs/{id}` | HR |
| POST | `/jobs/{id}/publish` | HR |
| GET | `/analytics/jobs/summary` | HR |

### Candidates
| Method | Path | Auth |
|--------|------|------|
| GET/PATCH | `/candidates/profile` | candidate |
| POST | `/candidates/profile/resume` | candidate |
| GET | `/candidates/profile/strength` | candidate |
| POST/DELETE | `/candidates/profile/work-experience/{id}` | candidate |

### Applications
| Method | Path | Auth |
|--------|------|------|
| POST | `/jobs/{id}/apply` | candidate |
| GET | `/candidates/applications` | candidate |
| DELETE | `/candidates/applications/{id}` | candidate |
| GET | `/candidates/recommendations` | candidate |
| GET | `/candidates/salary-benchmark` | candidate |
| POST/GET/DELETE | `/candidates/alerts` | candidate |

### AI
| Method | Path | Auth |
|--------|------|------|
| POST | `/ai/parse-resume` | candidate |
| GET | `/ai/optimize-resume` | candidate |
| POST | `/ai/chat` | candidate |
| GET | `/ai/resume-summary/{id}` | HR |
| GET/POST | `/ai/match-score/{id}` | HR |
| POST | `/ai/compare-candidates` | HR |
| POST/GET | `/ai/rank-applicants/{job_id}` | HR |
| POST | `/ai/generate-jd` | HR |
| POST | `/ai/rejection-email` | HR |

---

## Development Workflow

```bash
# Rebuild after code changes
docker compose up --build -d

# Run migrations
docker compose exec backend alembic upgrade head

# Backend unit tests
docker compose exec backend pytest tests/ -v

# Generate a new migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Tail backend logs
docker compose logs -f backend

# Tail celery worker logs
docker compose logs -f worker
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI 0.111, Uvicorn, async SQLAlchemy 2.0, Pydantic v2 |
| DB | PostgreSQL 15 + asyncpg, Alembic migrations |
| Cache / Queue | Redis 7 + Celery (beat scheduler) |
| AI | Groq (`llama3-8b-8192`, `llama-3.3-70b-versatile`), pdfplumber |
| Frontend | Next.js 14 App Router, TypeScript strict |
| UI | Tailwind CSS, shadcn/ui (Radix primitives), Lucide icons |
| State | TanStack Query v5, React Hook Form + Zod |
| Auth | python-jose (HS256 JWT), passlib bcrypt, httpOnly cookies |
| Email | Celery tasks → SMTP (Gmail / SendGrid) |
| Observability | structlog JSON logs, OpenTelemetry |
| Testing | pytest-asyncio, httpx, Jest + React Testing Library |

---

## Role Hierarchy

```
elite_admin
  └── admin
        └── superadmin
              ├── hr_admin
              │     ├── hiring_manager
              │     └── recruiter
              └── hr
candidate  (separate track)
```

HR roles (`hr`, `hr_admin`, `hiring_manager`, `recruiter`, `superadmin`, `admin`, `elite_admin`) access:
- Job postings, pipeline management, analytics
- AI tools: resume summaries, match scores, candidate comparison, ranking, JD generator, rejection emails

Candidates access:
- Profile, job search, apply, application tracker, job alerts
- AI tools: resume parser, resume optimizer, career chatbot
