# FindUs — AI-Powered HR Portal

> **Module 1 — Foundation** | FastAPI · Next.js 14 · PostgreSQL 15 · Redis 7 · Docker

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
git clone <repo-url> findus
cd findus

# Copy the example env file and fill in your secrets
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY, ADMIN_JWT_SECRET, OPENAI_API_KEY
```

### 2. Build & run

```bash
docker compose up --build
```

Services spin up in dependency order:
`postgres` → `redis` → `backend` → `frontend`

### 3. Verify

| Endpoint | Expected |
|----------|---------|
| `GET http://localhost:8000/health` | `{"status":"ok"}` |
| `GET http://localhost:8000/docs` | Swagger UI |
| `GET http://localhost:3000` | Next.js default page |

### 4. (Optional) SonarQube

```bash
docker compose --profile tools up sonarqube
# Open http://localhost:9000  (admin / admin)
```

---

## Project Structure

```
Portal/
├── docker-compose.yml          # All services
├── .env.example                # Environment template
├── sonar-project.properties    # SonarQube config
│
├── backend/
│   ├── Dockerfile
│   ├── start.sh                # Entrypoint: migrate → seed → workers → uvicorn
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── main.py                 # FastAPI app factory
│   ├── migrations/
│   │   └── env.py              # Async Alembic environment
│   └── app/
│       ├── core/
│       │   ├── config.py       # Pydantic Settings
│       │   └── logging.py      # structlog JSON formatter + middleware
│       └── __init__.py
│
└── frontend/
    ├── Dockerfile              # Multi-stage Node 20 build
    ├── package.json
    ├── next.config.js          # standalone output, env passthrough
    ├── tailwind.config.ts      # FindUs brand colours + shadcn/ui tokens
    ├── tsconfig.json           # strict mode, @/* aliases
    └── src/
        └── types/
            └── index.ts        # All domain TypeScript interfaces
```

---

## Environment Variables

See [.env.example](.env.example) for the full list. Critical vars:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | asyncpg PostgreSQL connection |
| `REDIS_URL` | Redis connection |
| `SECRET_KEY` | JWT signing secret (≥ 32 chars) |
| `ADMIN_JWT_SECRET` | Admin-scoped JWT secret (≥ 32 chars) |
| `OPENAI_API_KEY` | AI resume parsing & chat |
| `FRONTEND_URL` | CORS allow-list for the backend |

---

## Development Workflow

```bash
# Backend hot-reload (volume mount enabled in docker-compose)
docker compose up backend

# Frontend dev server (outside Docker for faster HMR)
cd frontend && npm install && npm run dev

# Run backend tests
docker compose exec backend pytest --cov=app tests/

# Generate a new Alembic migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations manually
docker compose exec backend alembic upgrade head
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI 0.111, Uvicorn, async SQLAlchemy 2.0 |
| DB | PostgreSQL 15 + asyncpg |
| Cache / Queue | Redis 7 + Celery |
| Frontend | Next.js 14 App Router, TypeScript strict |
| UI | Tailwind CSS, shadcn/ui (Radix primitives) |
| State | TanStack Query v5, React Hook Form + Zod |
| Auth | python-jose (HS256 JWT), passlib bcrypt |
| Observability | structlog, OpenTelemetry, Prometheus |
| Testing | pytest-asyncio, httpx, Jest, Playwright |
| Quality | SonarQube community |

---

## Roadmap — Upcoming Modules

- **Module 2** — Auth (register, login, refresh, admin portal)
- **Module 3** — Job management (CRUD, publish, search)
- **Module 4** — Candidate profiles & AI resume parsing
- **Module 5** — Application pipeline & Kanban board
- **Module 6** — AI chat & interview scheduling
- **Module 7** — Notifications, analytics, reporting
