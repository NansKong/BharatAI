# BharatAI 🇮🇳

> **India's First AI-Powered Academic Opportunity Intelligence & Merit Platform for College Students.**

BharatAI aggregates real-time academic opportunities (hackathons, research internships, scholarships, fellowships, and workshops) across premier Indian institutions and national portals, personalizes them through AI domain classification and semantic embeddings, assists students with application tracking and autofilling, and computes an official **InCoScore** (0–1000 merit rating).

---

## 📑 Table of Contents

- [System Architecture](#system-architecture)
- [Key Features & Engines](#key-features--engines)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start Guide](#quick-start-guide)
- [Environment Configuration](#environment-configuration)
- [Live Ingestion & Data Pipeline](#live-ingestion--data-pipeline)
- [Developer & Ops Commands](#developer--ops-commands)
- [API Reference](#api-reference)
- [Roadmap & Phase Progress](#roadmap--phase-progress)
- [Contributing](#contributing)
- [License](#license)

---

## 🏛 System Architecture

```
                                  ┌───────────────────────────┐
                                  │   Nginx (Reverse Proxy)   │
                                  │        :80 / :443         │
                                  └─────────────┬─────────────┘
                                                │
                         ┌──────────────────────┴──────────────────────┐
                         ▼                                             ▼
             ┌───────────────────────┐                     ┌───────────────────────┐
             │   Next.js Frontend    │                     │    FastAPI Backend    │
             │   (App Router, :3000) │                     │   (Python 3.11, :8000)│
             └───────────────────────┘                     └───────────┬───────────┘
                                                                       │
                    ┌───────────────────┬──────────────────┬───────────┴───────┐
                    ▼                   ▼                  ▼                   ▼
             ┌──────────────┐    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
             │  PostgreSQL  │    │   Redis 7    │   │Elasticsearch │   │Celery Worker │
             │  (Port 5432) │    │ (Cache/Queue)│   │ (Vector/Full)│   │  + Beat      │
             └──────────────┘    └──────────────┘   └──────────────┘   └──────┬───────┘
                                                                              │
                                                                       ┌──────┴───────┐
                                                                       │  Flower UI   │
                                                                       │ (Monitor)    │
                                                                       └──────────────┘
```

---

## 🚀 Key Features & Engines

### 1. Opportunity Scraper & Monitoring Engine (`backend/app/scrapers/`)
- **Live Scraper Adapters**:
  - **Devfolio API**: Direct API consumer for ongoing hackathons, deadlines, and prizes.
  - **Unstop API**: Automated pagination and ingestion of national competitions, hackathons, and challenges.
  - **Indian Research Portals**: Scrapes opportunities from IIT Bombay, IIT Delhi, IISc, CSIR, DST, and SERB.
  - **Internships Engine**: Real-time aggregation of technical, research, and corporate internships.
  - **National RSS Scrapers**: Continuous ingestion from research institute newsfeeds and academic bulletins.
  - **Playwright & Dynamic Scraping**: Headless Chromium runner for JavaScript-rendered portals.
- **Deduplication**: SHA-256 content hashing + cosine title similarity checks ($>90\%$).
- **Dead-Letter Queue**: Transient failures retry with exponential backoff (2s / 4s / 8s); unresolved failures persist to `scrape_dead_letters` for admin review.

### 2. AI Domain Classifier & Personalization (`backend/app/ai/`)
- **Zero-Shot Domain Classification**: Categorizes ingested opportunities into 11 Indian academic disciplines using `facebook/bart-large-mnli`:
  - *AI/DS, Computer Science, Electronics & Communication, Mechanical Engineering, Civil Engineering, Biotechnology, Law, Management, Finance, Humanities, Government & Policy*.
- **FAISS Semantic Search**: Vector embeddings generated via `sentence-transformers/all-MiniLM-L6-v2` with scheduled FAISS index rebuilds.
- **Resume Intelligence**: Parses uploaded resumes (`pdfplumber` / `PyMuPDF`) and normalizes skills via spaCy NER.
- **4-Factor Personalized Relevance Feed**:
  $$\text{Relevance Score} = 0.4 \times \text{Interest} + 0.3 \times \text{Skills} + 0.2 \times \text{Engagement} + 0.1 \times \text{Urgency}$$
  Feeds are cached in Redis (15-min TTL) with automatic invalidation on student profile updates.

### 3. Application Assistance Engine (`backend/app/api/v1/applications.py`)
- **State Machine Workflow**: Enforces strict application progression:
  `draft` $\rightarrow$ `submitted` $\rightarrow$ `accepted` / `rejected` (or `withdrawn`).
- **AI Checklist Generator**: Parses opportunity eligibility criteria and generates tailored application checklists.
- **Profile Autofill**: Suggests profile data for external portal applications with strict user consent verification, audit logging (`autofill_logs`), and Redis sliding-window rate limiting (20 requests/hour).

### 4. InCoScore Merit Scoring Engine (`backend/app/ai/incoscore.py`)
Deterministic merit scoring engine (0–1000 scale) benchmarking academic, coding, and leadership achievements:
- **Hackathons**: 1st (100 pts), 2nd (70 pts), 3rd (50 pts), Participant (10 pts)
- **Research Internships**: Verified internships (80 pts each, capped at 240 pts)
- **Publications**: Peer-reviewed (120 pts), Preprint (40 pts)
- **Competitions**: National (90 pts), State (50 pts), College (20 pts)
- **Certifications**: Industry (60 pts), NPTEL / Academic (30 pts)
- **Coding Profiles**: Rating bands from LeetCode, CodeChef, CodeForces (up to 100 pts)
- **Anti-Gaming Protections**: Submissions capped at 5 per 24 hours (HTTP 429), title+date uniqueness checks, and manual admin verification.
- **Leaderboards**: Filterable by Overall, Specific Academic Domain, or College.

### 5. Notification & WebSocket Engine (`backend/app/core/ws.py`, `backend/app/workers/notification_tasks.py`)
- **Real-Time In-App Alerts**: WebSockets connection manager (`/ws/notifications/{user_id}`) with JWT authentication.
- **Automated Celery Beat Jobs**:
  - Daily 8:00 AM IST deadline reminders for shortlisted and tracked applications.
  - High-confidence opportunity match broadcasts.
  - Achievement verification and InCoScore change notifications.
- **Email Delivery**: Responsive HTML email templates via Jinja2 with granular user opt-in preferences.

### 6. Modern Frontend Dashboard (`frontend/`)
- Next.js 14 App Router, TypeScript, Tailwind CSS, Framer Motion, and Lucide React.
- Dedicated interfaces for:
  - Personalized Opportunity Feed & Smart Filters
  - Internships Directory & Application Links
  - InCoScore Leaderboard & Badge Showcase
  - Application Management Pipeline
  - Community Discussions, Groups & Achievement Verification
  - Profile, Resume Parser & Skill Management
  - Notifications Center & Admin Moderation Queues

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | FastAPI (Python 3.11, async/await) |
| **ORM & Migrations** | SQLAlchemy 2.0 (asyncpg), Alembic |
| **Frontend Framework** | Next.js 14 (TypeScript, App Router, Tailwind CSS, Zustand, React Query) |
| **Primary Database** | PostgreSQL 15 (`pg_stat_statements`) |
| **Cache & Message Broker** | Redis 7 (AOF + snapshotting) |
| **Search & Indexing** | Elasticsearch 8, FAISS vector index |
| **AI / NLP Models** | HuggingFace (`bart-large-mnli`), `all-MiniLM-L6-v2`, spaCy |
| **Task Queue & Scheduler** | Celery 5 + Celery Beat + Flower |
| **Web Scraping** | Playwright (Chromium), HTTPX, BeautifulSoup4 |
| **Auth & Security** | Asymmetric JWT RS256, bcrypt, Bleach sanitization, Redis token blocklist |
| **Observability** | Prometheus, Grafana, OpenTelemetry, structlog |

---

## 📂 Project Structure

```
BharatAI/
├── backend/
│   ├── alembic/              # Database migration scripts
│   ├── app/
│   │   ├── ai/               # Classifier, embeddings, InCoScore, resume parser
│   │   ├── api/v1/           # REST endpoints (auth, feed, opportunities, applications, etc.)
│   │   ├── core/             # Database, Redis, security, storage, websockets, logging
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── scrapers/         # Unstop, Devfolio, Research, RSS, Static, Dynamic scrapers
│   │   ├── services/         # Email delivery, background integrations
│   │   ├── templates/        # Jinja2 email templates
│   │   └── workers/          # Celery tasks (scrapers, AI tasks, notifications, InCoScore)
│   ├── data/                 # Sample resumes and local storage
│   ├── scripts/              # Ingestion, seeding, and maintenance utilities
│   ├── tests/                # Comprehensive unit and integration test suite
│   ├── Dockerfile            # Backend production container
│   ├── requirements.txt      # Python dependencies
│   └── alembic.ini           # Alembic configuration
├── frontend/
│   ├── app/                  # Next.js App Router (feed, opportunities, leaderboard, etc.)
│   ├── components/           # Reusable UI elements, navigation, and sidebar
│   ├── hooks/                # WebSocket and client-side hooks
│   ├── lib/                  # API client, Zustand stores, React Query client
│   ├── public/               # Static assets and icons
│   ├── Dockerfile            # Frontend production container
│   └── package.json          # Node dependencies and scripts
├── infra/
│   ├── grafana/              # Dashboards and data source provisioning
│   ├── nginx/                # Reverse proxy configuration
│   ├── postgres/             # Database initialization scripts
│   └── prometheus/           # Prometheus metrics scraping rules
├── docs/                     # API Guide, Architecture KIs, Security & Performance Docs
├── knowledge/                # Architecture and engine artifacts
├── scripts/                  # Operational backup and smoke test shell scripts
├── docker-compose.yml        # Full-stack Docker orchestration
├── docker-compose.staging.yml# Staging environment configuration
├── Makefile                  # Developer workflow shortcuts
└── README.md                 # Project documentation
```

---

## ⚡ Quick Start Guide

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (running)
- Python 3.11+
- Node.js 18+ and npm
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/NansKong/BharatAI.git
cd BharatAI
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
# Configure your secrets in .env (or keep defaults for local development)
```

### 3. Generate RS256 JWT Key Pair
```bash
make gen-keys
```

### 4. Start Infrastructure & Application
```bash
make dev
```
*This spins up PostgreSQL, Redis, Elasticsearch, Backend, Celery Worker, Celery Beat, Flower, and Frontend.*

### 5. Run Migrations & Seed Sample Data
```bash
make migrate
make seed
```

### 6. Access Services
| Service | URL | Default Credentials / Note |
|---|---|---|
| **Frontend Application** | [http://localhost:3000](http://localhost:3000) | Student & Admin Portal |
| **FastAPI Swagger UI** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive API docs |
| **FastAPI ReDoc** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Alternative API spec |
| **Flower (Celery Monitor)**| [http://localhost:5555](http://localhost:5555) | Background worker metrics |
| **Grafana Dashboards** | [http://localhost:3001](http://localhost:3001) | Scraper & infra observability |
| **Kibana (Search Logs)** | [http://localhost:5601](http://localhost:5601) | Centralized ELK logging |

---

## ⚙️ Environment Configuration

Key configuration parameters (see `.env.example` for the complete list):

| Parameter | Default / Example | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@postgres:5432/bharatai` | Async PostgreSQL connection |
| `REDIS_URL` | `redis://redis:6379/0` | Cache and rate-limiter store |
| `CELERY_BROKER_URL` | `redis://redis:6379/1` | Background task broker |
| `JWT_PRIVATE_KEY_PATH` | `jwt_private.pem` | RS256 private signing key |
| `JWT_PUBLIC_KEY_PATH` | `jwt_public.pem` | RS256 public verification key |
| `GEMINI_API_KEY` | `your-gemini-key` | Google Gemini API (optional LLM tasks) |
| `SMTP_HOST` | `smtp.gmail.com` | Outgoing email notifications |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API base URL for frontend |

---

## 🔄 Live Ingestion & Data Pipeline

To trigger real-time scraping and domain classification across Indian portals without waiting for scheduled Celery jobs:

```bash
# Run full live ingestion pipeline across all active sources
python backend/scripts/run_ingestion.py

# Ingest genuine, high-quality opportunities
python backend/scripts/ingest_high_quality_real.py

# Verify live scraped items in the database
python backend/scripts/check_ingested.py

# Purge expired opportunities or reset demo seeds
python backend/scripts/purge_expired_opportunities.py
```

---

## 🛠 Developer & Ops Commands

All common tasks are accessible via the root `Makefile`:

```bash
make dev          # Start full stack with Docker Compose
make stop         # Stop all running containers
make logs         # Tail unified logs across all containers
make migrate      # Run Alembic migrations
make seed         # Seed sample database entities
make test         # Run backend pytest suite
make test-cov     # Run tests with HTML coverage report
make lint         # Run ruff, black, isort, and eslint
make gen-keys     # Generate RS256 RSA key pair for JWT auth
make shell        # Open a bash shell inside the backend container
```

---

## 📡 API Reference

All HTTP endpoints are versioned under `/api/v1/`:

- **Auth**: `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/refresh`, `/api/v1/auth/google`
- **Opportunities**: `/api/v1/opportunities`, `/api/v1/opportunities/{id}`
- **Feed**: `/api/v1/feed` (personalized multi-factor scoring)
- **Applications**: `/api/v1/applications`, `/api/v1/applications/{id}/checklist`, `/api/v1/applications/{id}/autofill`
- **InCoScore**: `/api/v1/incoscore/me`, `/api/v1/incoscore/leaderboard`
- **Community**: `/api/v1/community/posts`, `/api/v1/community/groups`, `/api/v1/community/achievements`
- **Notifications**: `/api/v1/notifications`, `/api/v1/notifications/count`, `/ws/notifications/{user_id}`
- **Admin**: `/api/v1/admin/sources`, `/api/v1/admin/opportunities/unclassified`, `/api/v1/admin/flags`

Complete interactive schema and parameter definitions are available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 📈 Roadmap & Phase Progress

| Phase | Description | Status |
|---|---|---|
| **Phase 0** | Monorepo Setup, Tooling & CI/CD Pipelines | ✅ Completed |
| **Phase 1** | Docker Infrastructure, PostgreSQL, Redis, Elasticsearch | ✅ Completed |
| **Phase 2** | FastAPI Core, Async SQLAlchemy, JWT RS256 Auth & RBAC | ✅ Completed |
| **Phase 3** | Scraper Framework (Unstop, Devfolio, Research portals, Deduplication, Dead-letters) | ✅ Completed |
| **Phase 4** | AI Classifier (`bart-large-mnli`), FAISS Embeddings, Resume Parser, Smart Feed | ✅ Completed |
| **Phase 5** | Application Tracker, State Machine, AI Checklist, Consent Autofill | ✅ Completed |
| **Phase 6** | InCoScore Merit Rating Engine (0–1000), Anti-Gaming, Leaderboards | ✅ Completed |
| **Phase 7** | Notification Engine, Celery Beat Scheduling, WebSockets, Email Templates | ✅ Completed |
| **Phase 8** | Next.js 14 App Router UI, Dashboard Suite & Frontend Integration | ✅ Completed |
| **Phase 9** | Comprehensive Test Suites (Pytest, Mock Scrapers, Ingestion Integration) | ✅ Completed |
| **Phase 10** | Live Data Ingestion, URL Normalization & Production Readiness | ✅ Completed |

---

## 🤝 Contributing

1. Fork the repository and create your feature branch:
   ```bash
   git checkout -b feature/amazing-feature
   ```
2. Ensure all linting and test checks pass:
   ```bash
   make lint
   make test
   ```
3. Commit your changes following conventional commits:
   ```bash
   git commit -m "feat: add support for new research portal scraper"
   ```
4. Push to your branch and open a Pull Request.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
