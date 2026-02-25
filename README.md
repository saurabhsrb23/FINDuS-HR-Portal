# FindUs (DoneHR) — AI-Powered HR Portal

> Full-stack recruiting platform — FastAPI · Next.js 14 · PostgreSQL 15 · Redis 7 · Groq AI · Docker

---

## Login URLs

| Portal | URL |
|--------|-----|
| **Main Application** | http://localhost:3000/login |
| **Admin Portal** | http://localhost:3000/admin/login |

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

cp .env.example .env
# Edit .env — set SECRET_KEY, ADMIN_JWT_SECRET, GROQ_API_KEY
```

> **Minimum required changes in `.env`:**
> - `SECRET_KEY` — any random string (32+ chars)
> - `ADMIN_JWT_SECRET` — a different random string (32+ chars)
> - `GROQ_API_KEY` — get free at https://console.groq.com
>
> Everything else works out-of-the-box for local development.

### 2. Build & run (recommended: use `make fresh`)

**With make (easiest):**
```bash
make fresh
```
This wipes any old state, builds images, starts all services, and follows the backend log so you can watch migrations + seed happen in real time.

**Without make:**
```bash
# Stop any previously running instance first (frees ports 3000, 8001)
docker compose down -v

# Build and start everything
docker compose up --build -d

# Watch the backend until you see "Seed complete"
docker compose logs -f backend
```

> **The terminal returns to the prompt immediately — this is normal.** The `-d` flag runs in the background. Seed data loads automatically. Watch with `docker compose logs -f backend` and wait for `==> [start.sh] Seed complete.` before opening the browser. First run takes ~30–60 seconds.

Services spin up automatically: `postgres` → `redis` → `backend` (migrate + seed) → `frontend`

### 3. Verify seed completed

```bash
docker compose logs backend | grep -E "Seed|seed|Migrat"
```

Expected output:
```
==> [start.sh] Running database migrations...
==> [start.sh] Migrations complete.
==> [start.sh] No users found — running seed...
==> [start.sh] Seed complete — all demo data loaded.
```

### 4. Open the app

| URL | Expected |
|-----|---------|
| http://localhost:3000 | Login page |
| http://localhost:8001/health | `{"status":"ok"}` |
| http://localhost:8001/docs | Swagger UI |
| http://localhost:8001/metrics | Prometheus metrics |
| http://localhost:3000/admin/login | Admin portal login |

---

## Test Credentials

### Main Application (http://localhost:3000/login)

| Role | Email | Password |
|------|-------|----------|
| HR Admin | hr@donehr.com | Hr@123456! |
| Candidate | candidate@donehr.com | Candidate@1! |
| Elite Admin | elite@donehr.com | Elite@Admin1! |
| Admin | admin@donehr.com | Admin@1234! |

### Seeded Developer Accounts (all password: `Dev@123456!`)

| Name | Email | Skills |
|------|-------|--------|
| Arjun Sharma | arjun.sharma@gmail.com | Python, Django, FastAPI, AWS |
| Priya Patel | priya.patel@gmail.com | React, TypeScript, Next.js |
| Rahul Verma | rahul.verma@gmail.com | Java, Spring Boot, Kafka |
| Sneha Kumar | sneha.kumar@gmail.com | Python, Machine Learning, TensorFlow |
| Vikram Singh | vikram.singh@gmail.com | Docker, Kubernetes, AWS, Terraform |
| Ananya Roy | ananya.roy@gmail.com | React, Node.js, MongoDB |
| Karthik Nair | karthik.nair@gmail.com | AWS, Azure, Cloud Architecture |
| Pooja Desai | pooja.desai@gmail.com | Android, Kotlin, Jetpack Compose |
| Rohit Gupta | rohit.gupta@gmail.com | Selenium, TestNG, Java |
| Divya Menon | divya.menon@gmail.com | Product Management, Agile, Analytics |

### Admin Portal (http://localhost:3000/admin/login)

| Role | Email | Password | PIN |
|------|-------|----------|-----|
| Superadmin | superadmin@donehr.com | SuperAdmin@2024! | 123456 |
| Admin | admin@donehr.com | Admin@2024! | 654321 |
| Elite (view-only) | elite@donehr.com | Elite@2024! | 111111 |

---

## Final Validation Checklist

Run after `docker compose up --build -d && alembic upgrade head && python seed.py`:

```
✅ http://localhost:3000              → Login page loads
✅ http://localhost:8001/health       → {"status":"ok"}
✅ http://localhost:8001/docs         → Swagger UI with all endpoints
✅ http://localhost:8001/metrics      → Prometheus metrics output
✅ Login as hr@donehr.com / Hr@123456!               → HR dashboard
✅ Login as candidate@donehr.com / Candidate@1!      → Candidate dashboard
✅ Login as superadmin@donehr.com / SuperAdmin@2024! / PIN 123456 → /admin
✅ WebSocket dot in sidebar is green (connected)
✅ AI summary loads on Resume Optimizer page
✅ Kanban drag-and-drop works on Pipeline page
✅ Chat works between HR and candidate (/dashboard/messages)
✅ Find Candidates search returns results (HR only)
✅ Certifications and Projects sections have Add button in profile
✅ Download Resume button works in My Profile (candidate)
✅ Download CV button works in Find Candidates (HR)
```

---

## Running Tests

```bash
# Backend unit tests with coverage
docker compose exec backend pytest tests/ -v --cov=app --cov-report=term-missing

# Individual unit test files
docker compose exec backend pytest tests/unit/test_notification_service.py -v
docker compose exec backend pytest tests/unit/test_chat_service.py -v
docker compose exec backend pytest tests/unit/test_admin_service.py -v

# Frontend E2E tests (requires running stack)
cd frontend && npx playwright test

# Run a specific E2E spec
cd frontend && npx playwright test tests/e2e/e2e_auth_security.spec.ts
```

---

## Project Structure

```
Portal/
├── docker-compose.yml
├── .env.example
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── start.sh                    # migrate → seed → celery → uvicorn
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── main.py                     # FastAPI app + /health + /metrics
│   ├── seed.py                     # Idempotent seed (all tables, 10 records each)
│   ├── migrations/versions/
│   │   ├── 001_users_companies_audit.py
│   │   ├── 002_jobs.py
│   │   ├── 003_candidates.py
│   │   ├── 004_ai_summaries.py
│   │   ├── 005_resume_url_text.py
│   │   ├── 006_search.py
│   │   ├── 007_applications_resume_url_text.py
│   │   ├── 008_admin.py
│   │   ├── 009_chat.py
│   │   └── 010_indexes.py          # Performance indexes (GIN, composite)
│   └── app/
│       ├── core/
│       │   ├── config.py
│       │   ├── security.py
│       │   ├── dependencies.py
│       │   ├── redis_client.py
│       │   ├── rate_limiter.py
│       │   ├── telemetry.py        # Prometheus counters/gauges + OTel spans
│       │   ├── event_emitter.py    # WebSocket event broadcasting
│       │   ├── websocket_manager.py
│       │   └── chat_manager.py
│       ├── models/
│       │   ├── user.py, company.py, job.py, candidate.py
│       │   ├── application.py, ai_summary.py, saved_search.py
│       │   ├── audit_log.py, admin.py, chat.py
│       ├── schemas/
│       ├── repositories/
│       ├── services/
│       │   ├── auth_service.py, job_service.py, candidate_service.py
│       │   ├── application_service.py, ai_service.py, search_service.py
│       │   ├── admin_service.py, chat_service.py
│       │   └── notification_service.py  # WS + email notifications
│       ├── routers/
│       │   ├── auth.py, jobs.py, candidates.py, applications.py
│       │   ├── ai.py, search.py, ws.py, admin.py, chat.py
│       └── tasks/
│           ├── email_tasks.py, job_tasks.py, job_alert_tasks.py, ai_tasks.py
│
└── frontend/
    ├── Dockerfile
    └── src/
        ├── middleware.ts
        ├── lib/
        │   └── api.ts, auth.ts, jobsAPI.ts, candidateAPI.ts, aiAPI.ts,
        │       chatAPI.ts, adminAPI.ts, applicationAPI.ts
        ├── types/
        │   └── job.ts, candidate.ts, application.ts, ai.ts, chat.ts, admin.ts
        ├── components/
        │   ├── ai/    (MatchScoreBadge, AISummaryPanel, ComparisonModal, ChatbotWidget)
        │   ├── chat/  (ChatInbox, ChatWindow, MessageBubble, TypingIndicator)
        │   ├── search/ (CandidateCard, FilterPanel)
        │   ├── shared/ (LiveActivityFeed, LiveCounterBadge)
        │   └── admin/  (LiveMetricsGrid, RealTimeEventFeed)
        └── app/
            ├── (auth)/login, register
            ├── (dashboard)/
            │   ├── layout.tsx              # Sidebar + WS connection + chat badge
            │   └── dashboard/
            │       ├── profile/            # Candidate: skills, exp, edu, certs, projects
            │       ├── browse-jobs/        # Naukri-style job search
            │       ├── my-applications/
            │       ├── job-alerts/
            │       ├── resume-optimizer/   # Score Analysis + AI Summary tabs
            │       ├── messages/           # Chat inbox + conversation window
            │       ├── jobs/               # HR job management
            │       │   └── [id]/ (edit, pipeline, questionnaire, ai-tools)
            │       ├── analytics/
            │       └── search/             # Find Candidates (HR)
            └── admin/
                ├── login, dashboard, users, companies, admins
                └── events, monitoring, chat
    └── tests/
        └── e2e/
            ├── e2e_candidate_full_flow.spec.ts
            ├── e2e_hr_full_flow.spec.ts
            ├── e2e_ai_features.spec.ts
            ├── e2e_auth_security.spec.ts
            ├── e2e_realtime.spec.ts
            ├── e2e_admin_portal.spec.ts
            ├── e2e_candidate_filter.spec.ts
            └── e2e_chat.spec.ts
```

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | asyncpg PostgreSQL connection |
| `REDIS_URL` | Redis connection |
| `SECRET_KEY` | JWT signing secret (≥ 32 chars) |
| `ADMIN_JWT_SECRET` | Admin-scoped JWT (≥ 32 chars) |
| `GROQ_API_KEY` | Groq AI API key (`gsk_...`) |
| `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` | Email delivery |
| `FRONTEND_URL` | CORS allow-list |
| `NEXT_PUBLIC_API_URL` | Frontend → backend URL |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL (default `ws://localhost:8001`) |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry collector (optional) |

---

## Modules

| Module | Description |
|--------|-------------|
| ✅ 1 — Foundation | Docker, config, logging, health endpoint |
| ✅ 2 — Auth | JWT, register, login, refresh, email verify, password reset, Redis blacklist |
| ✅ 3 — Job Management | CRUD, publish/pause/close/clone, pipeline, questionnaire, analytics |
| ✅ 4 — Candidate | Profile, resume upload, job search, apply, tracker, alerts, salary benchmark |
| ✅ 5 — AI (Groq) | Resume parser, summarizer, match score, comparison, ranking, JD gen, rejection email, optimizer, chatbot |
| ✅ 6 — Advanced Search | Boolean search, GIN/tsvector, saved searches, talent pools, CSV export |
| ✅ 7 — WebSocket | Real-time events, Redis Pub/Sub, live dashboard, auto-reconnect |
| ✅ 8 — Admin Portal | Separate admin JWT, PIN login, platform events log, monitoring |
| ✅ 9 — Chat System | Direct/group/broadcast, reactions, file upload, reports, bans |
| ✅ 10 — Production | Seed (10 records/table), Prometheus /metrics, OTel spans, indexes, E2E tests |

---

### Module 1 — Foundation
Docker Compose orchestration, PostgreSQL + Redis setup, Pydantic Settings, structlog JSON logging, OpenTelemetry hooks, base models and `/health` endpoint.

### Module 2 — Authentication
- JWT (HS256) access + refresh tokens in httpOnly cookies
- Register, login, logout, token refresh, email verification, password reset
- Redis token blacklist for immediate invalidation
- Rate limiting: 5/min on login, 3/min on forgot-password
- Admin portal JWT with separate secret (`aud=admin_portal`)
- Soft-delete users (never hard-deleted)

### Module 3 — Job Management
- Full CRUD: draft → published → paused → closed
- Clone jobs, auto-archive expired postings via Celery
- 6-stage recruitment pipeline with drag-and-drop reordering
- Custom questionnaire builder per job (text, MCQ, yes/no, rating)
- Analytics: funnel, source breakdown, time-to-hire

### Module 4 — Candidate Features
- Profile: personal info, work experience, education, certifications, projects, skills
- PDF resume upload with magic-bytes validation (5 MB limit)
- Profile strength score 0–100 (auto-recalculated on every mutation)
- Naukri-style job search with filters (role, location, type, salary)
- Apply flow: cover letter + per-job questionnaire answers
- Application tracker with visual JSONB event timeline
- `UNIQUE(job_id, candidate_id)` duplicate prevention
- Job alerts: keyword/location subscriptions, Celery daily digest at 07:00 UTC
- Salary benchmark (22 Indian IT roles/locations)
- Skill-based job recommendations

### Module 5 — AI Features (Groq)
All AI calls use **Groq** (`llama-3.1-8b-instant` for speed, `llama-3.3-70b-versatile` for quality).
Results cached in `ai_summaries` — `UNIQUE(entity_id, summary_type)`. Groq failures return HTTP 503 gracefully.

| Feature | Who | Endpoint |
|---------|-----|---------|
| Resume Parser | Candidate | `POST /ai/parse-resume` |
| Resume Summarizer | HR | `GET /ai/resume-summary/{candidate_id}` |
| Match Score | HR | `GET /ai/match-score/{application_id}` |
| Match Score (async) | HR | `POST /ai/match-score/{application_id}/enqueue` |
| Candidate Comparison | HR | `POST /ai/compare-candidates` |
| Auto Ranking | HR | `POST /ai/rank-applicants/{job_id}` |
| JD Generator | HR | `POST /ai/generate-jd` |
| Rejection Email | HR | `POST /ai/rejection-email` |
| Resume Optimizer | Candidate | `GET /ai/optimize-resume` |
| Career Chatbot | Candidate | `POST /ai/chat` |

### Module 6 — Advanced Search
- Full-text GIN/tsvector search on candidate profiles
- Boolean parser: `"python AND (django OR fastapi) NOT junior"`
- Saved searches + talent pools with candidate collections
- Redis-cached search results (5-min TTL)
- CSV export of search results (HR only)

### Module 7 — WebSocket Real-Time
- `ConnectionManager` — per-process registry of active WS connections
- Redis Pub/Sub channel `donehr:events` — cross-process fan-out
- `emit_event()` — target by `user_id` or `role`
- `target_role="hr_all"` broadcasts to all 7 HR roles simultaneously
- Auto-reconnect hook with exponential backoff in frontend
- Live status dot in sidebar: green/yellow/gray
- HR dashboard: live KPI counters + activity feed
- Candidate dashboard: toast notifications (profile viewed, shortlisted, interview scheduled)

### Module 8 — Admin Portal
- Separate `admin_users` table; login at `/admin/login`
- 6-digit PIN with bcrypt hash; 3 failed attempts → 15-min lockout
- Role hierarchy: `elite_admin` (view-only) < `admin` < `superadmin`
- Platform events log with real-time feed (polls every 10s)
- Live metrics: active jobs, total users, applications today, active sessions
- Superadmin-only: create/delete admin users at `/admin/admins`
- Elite admin: read-only — no deactivate, no CSV export, no admin management

### Module 9 — Chat System
- Conversation types: direct (1-on-1), group, broadcast
- Real-time delivery via `/ws/chat?token=JWT` + Redis `donehr:chat` channel
- Features: typing indicators, read receipts, message reactions, file uploads
- Moderation: report message, ban user (admin only)
- Admin chat monitor at `/admin/chat`
- Unread badge in sidebar (updates on every WS message)
- Only chat roles: candidate, hr, hr_admin, hiring_manager, recruiter

### Module 10 — Production Hardening
- **Seed**: 10 records per table — users, companies, jobs, candidates, applications, certifications, projects, job alerts, AI summaries, saved searches, talent pools, audit logs, platform events, chat conversations/messages
- **Prometheus `/metrics`**: `total_requests_total`, `failed_requests_total`, `ai_tokens_used_total`, `db_query_duration_seconds`, `active_websocket_connections`, `active_jobs_total`, `total_candidates_total`
- **OpenTelemetry**: FastAPI + SQLAlchemy auto-instrumentation; manual spans for Groq calls and Celery tasks
- **DB Indexes**: GIN on `search_vector`, composite indexes on jobs/applications/users/chat/platform_events
- **E2E Tests**: 8 Playwright spec files covering candidate flow, HR flow, AI features, auth/security, real-time, admin portal, search filters, chat

---

## API Reference

Interactive Swagger: **http://localhost:8001/docs**

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
| GET / PATCH / DELETE | `/jobs/{id}` | HR |
| POST | `/jobs/{id}/publish` | HR |
| POST | `/jobs/{id}/pause` | HR |
| POST | `/jobs/{id}/close` | HR |
| POST | `/jobs/{id}/clone` | HR |
| GET | `/analytics/jobs/summary` | HR |

### Candidates
| Method | Path | Auth |
|--------|------|------|
| GET / PATCH | `/candidates/profile` | candidate |
| POST | `/candidates/profile/resume` | candidate |
| GET | `/candidates/profile/strength` | candidate |
| POST / DELETE | `/candidates/profile/work-experience/{id}` | candidate |
| POST / DELETE | `/candidates/profile/education/{id}` | candidate |
| POST / DELETE | `/candidates/profile/certification/{id}` | candidate |
| POST / DELETE | `/candidates/profile/project/{id}` | candidate |
| POST / DELETE | `/candidates/profile/skills` | candidate |

### Applications
| Method | Path | Auth |
|--------|------|------|
| POST | `/jobs/{id}/apply` | candidate |
| GET | `/candidates/applications` | candidate |
| DELETE | `/candidates/applications/{id}` | candidate |
| PATCH | `/applications/{id}/status` | HR |
| GET | `/candidates/recommendations` | candidate |
| GET | `/candidates/salary-benchmark` | candidate |
| POST / GET / DELETE | `/candidates/alerts` | candidate |

### AI
| Method | Path | Auth |
|--------|------|------|
| POST | `/ai/parse-resume` | candidate |
| GET | `/ai/optimize-resume` | candidate |
| POST | `/ai/chat` | candidate |
| GET | `/ai/resume-summary/{id}` | HR |
| GET / POST | `/ai/match-score/{id}` | HR |
| POST | `/ai/compare-candidates` | HR |
| POST / GET | `/ai/rank-applicants/{job_id}` | HR |
| POST | `/ai/generate-jd` | HR |
| POST | `/ai/rejection-email` | HR |

### Search
| Method | Path | Auth |
|--------|------|------|
| POST | `/api/v1/search/candidates` | HR |
| POST | `/api/v1/search/saved` | HR |
| GET / DELETE | `/api/v1/search/saved/{id}` | HR |
| POST | `/api/v1/search/pools` | HR |
| POST | `/api/v1/search/pools/{id}/candidates` | HR |
| GET | `/api/v1/search/export/csv` | HR |

### WebSocket
| Method | Path | Auth |
|--------|------|------|
| GET | `/ws` | JWT query param |
| GET | `/ws/chat` | JWT query param |

### Admin
| Method | Path | Auth |
|--------|------|------|
| POST | `/admin/login` | public |
| GET | `/admin/users` | admin |
| PATCH | `/admin/users/{id}/deactivate` | admin |
| GET | `/admin/companies` | admin |
| GET | `/admin/events` | admin |
| GET | `/admin/monitoring-metrics` | admin |
| GET / POST / DELETE | `/admin/admins` | superadmin |

### Chat
| Method | Path | Auth |
|--------|------|------|
| GET / POST | `/chat/conversations` | bearer |
| GET | `/chat/conversations/{id}/messages` | bearer |
| POST | `/chat/messages` | bearer |
| POST | `/chat/messages/{id}/react` | bearer |
| POST | `/chat/messages/{id}/report` | bearer |
| GET | `/chat/admin/conversations` | admin |
| POST | `/chat/admin/ban` | admin |

### System
| Method | Path | Auth |
|--------|------|------|
| GET | `/health` | public |
| GET | `/metrics` | public |

---

## Troubleshooting

### "Login failed. Please try again."

This almost always means seed data didn't load. Work through this checklist in order:

**Step 1 — Check backend logs:**
```bash
docker compose logs backend | grep -E "Seed|seed|ERROR|WARNING|error"
```
Look for `Seed complete` (good) or `seed.py exited with code` (bad — error is printed just above that line).

**Step 2 — Check all containers started:**
```bash
docker compose ps
```
Every service should show `running`. If `backend` is `exited`, it crashed — check `docker compose logs backend` for the full error.

**Step 3 — Port conflict (most common cause)**
Only one Docker Compose project can use ports 3000 and 8001 at a time. If you have another clone or project running:
```bash
# In the OTHER project directory, stop it first:
docker compose down

# Then in this directory, do a full fresh start:
make fresh          # with make
# OR
docker compose down -v && docker compose up --build -d && docker compose logs -f backend
```

**Step 4 — Force re-seed (if containers are running but users missing):**
```bash
make seed
# OR
docker compose exec backend python seed.py
```

**Step 5 — Nuclear option (wipe everything and start clean):**
```bash
make reset && make fresh
# OR
docker compose down -v --remove-orphans
docker compose up --build -d
docker compose logs -f backend
```

---

## Development Workflow

```bash
# Fresh start (wipe + rebuild + follow logs)
make fresh

# Start in background (keeps existing data)
make up

# Stop (keeps data)
make down

# Wipe all data and stop
make reset

# Follow backend logs
make logs

# Re-run seed manually (idempotent — safe anytime)
make seed

# Run backend tests
make test

# Open backend shell
make shell

# Rebuild after code changes
docker compose up --build -d

# Run migrations only
docker compose exec backend alembic upgrade head

# Generate a new Alembic migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Flush Redis cache
docker compose exec redis redis-cli FLUSHDB
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI 0.111, Uvicorn, async SQLAlchemy 2.0, Pydantic v2 |
| DB | PostgreSQL 15 + asyncpg, Alembic migrations |
| Cache / Queue | Redis 7 + Celery (beat scheduler) |
| AI | Groq (`llama-3.1-8b-instant`, `llama-3.3-70b-versatile`), pdfplumber |
| Frontend | Next.js 14 App Router, TypeScript strict |
| UI | Tailwind CSS, shadcn/ui (Radix), Lucide icons |
| Auth | python-jose (HS256 JWT), passlib bcrypt, httpOnly cookies |
| Observability | structlog JSON, OpenTelemetry, Prometheus (`/metrics`) |
| Testing | pytest-asyncio, httpx, Playwright E2E |

---

## Role Hierarchy

```
Admin Portal (separate login):
  elite_admin (view-only) < admin < superadmin

Main App:
  elite_admin → admin → superadmin
                           ├── hr_admin → hiring_manager / recruiter
                           └── hr
  candidate  (separate track)
```

**HR roles** (`hr`, `hr_admin`, `hiring_manager`, `recruiter`, `superadmin`, `admin`, `elite_admin`):
- Job postings, pipeline management, analytics
- Find Candidates search (boolean + filters + CSV export)
- AI tools: resume summaries, match scores, comparison, ranking, JD generator, rejection emails
- Chat with candidates

**Candidates**:
- Profile (skills, experience, education, certifications, projects)
- Browse jobs, apply, application tracker, job alerts
- AI tools: resume parser, resume optimizer, career chatbot
- Chat with HR
