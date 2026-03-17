# BharatAI ðŸ‡®ðŸ‡³

> India's first AI-powered academic opportunity intelligence platform for college students.

## What is BharatAI?

BharatAI aggregates real-time academic opportunities (hackathons, scholarships, research internships, workshops, fellowships) from Indian institutions, personalises them using AI, assists with applications, and ranks students using the **InCoScore** engine.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.11, async) |
| Frontend | Next.js 14 (TypeScript, App Router) |
| Database | PostgreSQL 15 |
| Cache / Queue | Redis 7 |
| Search | Elasticsearch 8 |
| AI/NLP | HuggingFace Transformers + Sentence Transformers |
| Vector Search | FAISS |
| Scraping | Playwright + BeautifulSoup |
| Background Jobs | Celery + Celery Beat |
| Auth | JWT (RS256) + Google OAuth2 |
| Infrastructure | Docker Desktop + Docker Compose |
| Monitoring | Prometheus + Grafana |
| Logging | ELK Stack |
| Tracing | OpenTelemetry + Jaeger |

---

## Quick Start (Local Dev with Docker Desktop)

### Prerequisites
- Docker Desktop (running)
- Python 3.11+
- Node.js 18+
- Git

### 1. Clone & configure
```bash
git clone <repo-url>
cd BharatAI
cp .env.example .env
# Edit .env with your values (see Environment Variables section)
```

### 2. Generate JWT key pair
```bash
make gen-keys
```

### 3. Start all services
```bash
make dev
```

### 4. Seed development data
```bash
make seed
```

### 5. Access the app
| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Flower (Celery monitor) | http://localhost:5555 |
| Grafana | http://localhost:3001 |
| Kibana | http://localhost:5601 |
| Jaeger | http://localhost:16686 |

---

## Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `JWT_PRIVATE_KEY_PATH` | Path to RS256 private key |
| `GOOGLE_CLIENT_ID` | Google OAuth2 Client ID |
| `GEMINI_API_KEY` | Google Gemini API key |
| `SMTP_HOST` | Email server for notifications |

---

## API Versioning

All HTTP endpoints are versioned under:

- `/api/v1/...`

Example:

- `GET /api/v1/opportunities`
- `POST /api/v1/auth/login`

---

## Developer Commands

```bash
make dev          # Start full stack with Docker Compose
make stop         # Stop all containers
make logs         # Tail logs from all services
make migrate      # Run Alembic DB migrations
make seed         # Seed development data
make test         # Run all backend tests
make test-cov     # Run tests with coverage report
make lint         # Run black + isort + ruff
make gen-keys     # Generate RSA key pair for JWT
make shell        # Open a shell in the backend container
```

---

## Project Structure

```
BharatAI/
â”œâ”€â”€ backend/          # FastAPI application
â”‚   â”œâ”€â”€ app/
â”‚   â”‚   â”œâ”€â”€ api/v1/   # REST endpoints
â”‚   â”‚   â”œâ”€â”€ core/     # Config, DB, security
â”‚   â”‚   â”œâ”€â”€ models/   # SQLAlchemy models
â”‚   â”‚   â”œâ”€â”€ schemas/  # Pydantic schemas
â”‚   â”‚   â”œâ”€â”€ services/ # Business logic
â”‚   â”‚   â””â”€â”€ workers/  # Celery tasks
â”‚   â”œâ”€â”€ alembic/      # Migrations
â”‚   â”œâ”€â”€ tests/        # Unit + integration tests
â”‚   â””â”€â”€ scripts/      # Seed, backup, utility scripts
â”œâ”€â”€ frontend/         # Next.js application
â”‚   â”œâ”€â”€ app/          # App Router pages
â”‚   â”œâ”€â”€ components/   # Reusable UI components
â”‚   â””â”€â”€ lib/          # API client, store
â”œâ”€â”€ infra/            # Nginx, Prometheus config
â”œâ”€â”€ docs/             # API guide, runbooks, specs
â””â”€â”€ .github/          # CI/CD workflows
```

---

## Phases

Last verified: 2026-02-22

| Phase | Status | Description |
|---|---|---|
| 0 | [x] Done | Pre-build setup |
| 1 | [x] Done | Infrastructure foundation |
| 2 | [x] Done | Backend auth + core models |
| 3 | [ ] In progress | Opportunity monitoring engine |
| 4 | [ ] Pending | AI classification + personalization |
| 5 | [ ] Pending | Application assistance |
| 6 | [ ] Pending | Community + InCoScore |
| 7 | [ ] Pending | Notification engine |
| 8-13 | [ ] Pending | Docs, security, performance, launch |
---

## Contributing

1. Branch off `main`: `git checkout -b feature/your-feature`
2. All PRs require: passing CI + code review
3. Run `make lint` and `make test` before pushing
