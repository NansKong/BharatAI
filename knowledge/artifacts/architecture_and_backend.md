# Architecture & Backend Foundation Guide (`BharatAI`)

## 1. Executive Summary & Core Mission
**BharatAI** (`d:\BharatAI`) is India's first AI-powered academic opportunity intelligence platform designed specifically for Indian college students. The platform aggregates real-time academic opportunities (hackathons, scholarships, research internships, fellowships, workshops) from premier Indian institutions and portals (e.g., IIT Bombay, IIT Delhi, IISc, AICTE, Startup India, DRDO, Smart India Hackathon, Unstop), classifies and personalizes them using zero-shot NLP models and FAISS vector embeddings, assists with application drafting and form autofilling, and ranks student achievements using the custom **InCoScore** engine.

---

## 2. Monorepo Directory Structure

```
d:\BharatAI\
├── backend/                  # FastAPI Application (Python 3.11, Async SQLAlchemy)
│   ├── app/
│   │   ├── api/v1/          # REST & WebSocket endpoints (auth, opportunities, feed, incoscore, etc.)
│   │   ├── ai/              # AI classifiers, resume parsers, embeddings, InCoScore logic
│   │   ├── core/            # Config, database engine, Redis client, security, rate-limiter, WS manager
│   │   ├── models/          # SQLAlchemy 2.x Async ORM models
│   │   ├── schemas/         # Strict Pydantic v2 schemas
│   │   ├── scrapers/        # Static & Dynamic BeautifulSoup/Playwright scraper adapters
│   │   ├── services/        # Business logic & email services
│   │   └── workers/         # Celery app, Beat schedules, and background worker tasks
│   ├── alembic/             # Async database migration scripts
│   ├── scripts/             # Database seeding, OpenAPI export, backup utilities
│   └── tests/               # Pytest suite (unit, integration, load)
├── frontend/                 # Next.js 14 Web Application (TypeScript, App Router, Tailwind CSS)
│   ├── app/                 # App router pages (dashboard, auth, feed, leaderboard, community, admin)
│   ├── components/          # Reusable UI components & Layouts
│   ├── hooks/               # Custom React hooks (e.g., useWebSocket)
│   └── lib/                 # Axios client, Zustand store, TanStack Query client
├── infra/                    # Docker, Nginx, Prometheus, Grafana, AlertManager configurations
├── docs/                     # API documentation, OpenAPI JSON, Postman collection, Security Audit
└── knowledge/                # Project Knowledge Base (KI artifacts & metadata)
```

---

## 3. Backend Technical Stack

* **Framework**: FastAPI (Python 3.11, async/await throughout).
* **Database & ORM**: PostgreSQL 15 managed with SQLAlchemy 2.x async engine & Alembic migrations.
* **Cache & Queues**: Redis 7 for sliding-window rate limiting, feed caching, JWT revocation blocklist, and Celery broker.
* **Background Processing**: Celery + Celery Beat for scraping scheduled runs, AI task queues, nightly FAISS re-indexing, and daily email reminders.
* **Authentication**: JWT RS256 asymmetric signing (RSA key pair), bcrypt password hashing (cost factor 12), Google OAuth2 integration, and dual-key rotation support (`JWT_PUBLIC_KEY_V2_PATH`).
* **Security & Hardening**: Sliding-window Redis rate-limiter (60 req/min anon, 300 req/min auth), `bleach` HTML sanitization, strict CORS origin whitelisting, and production HSTS headers.

---

## 4. Primary Data Models & Constraints

| Model Name | Core Columns / Attributes | Constraints & Indexes |
| :--- | :--- | :--- |
| `User` | `id`, `email`, `name`, `role` (`student`/`admin`), `google_id`, `hashed_password`, `college`, `degree`, `year` | Unique: `email`. Index: `user_id`, `created_at`. |
| `Profile` | `user_id`, `skills` (Array), `interests` (Array), `resume_path`, `embedding_vector` (Array[float]), `bio` | FK: `user_id`. Index on skills and interests. |
| `MonitoredSource` | `id`, `url`, `type` (`static`/`dynamic`), `interval_minutes`, `active`, `last_scraped_at`, `failure_count` | Constraint: `interval_minutes >= 15`. |
| `Opportunity` | `id`, `title`, `description`, `institution`, `domain`, `secondary_domain`, `deadline`, `source_url`, `content_hash` | Unique: `content_hash`. Indexes: `domain`, `deadline`, `created_at`. |
| `Application` | `id`, `user_id`, `opportunity_id`, `status` (`draft`/`submitted`/`accepted`/`rejected`/`withdrawn`) | Unique constraint: `(user_id, opportunity_id)`. |
| `Achievement` | `id`, `user_id`, `type` (`hackathon`, `internship`, `publication`, `competition`, `certification`, `coding`), `verified` | Admin verification gate before point accumulation. |
| `InCoScoreHistory` | `id`, `user_id`, `total_score`, `domain`, `components_json`, `computed_at` | Immutable score audit snapshot log. |

---

## 5. API Routing Taxonomy (`/api/v1/`)

* `/api/v1/auth`: `register`, `login`, `refresh`, `logout`, `google` OAuth start and callback.
* `/api/v1/users` & `/api/v1/profile`: Student profile management, skill tagging, resume upload (`POST /profile/resume`).
* `/api/v1/opportunities`: Cursor-paginated opportunity feed, domain/deadline filters, detail view, admin CRUD.
* `/api/v1/feed`: Personalized opportunity feed with user-level Redis caching and invalidation hooks.
* `/api/v1/applications`: Application submission tracking, state machine status updates, AI-generated checklist, autofill suggestions.
* `/api/v1/community`: Posts, groups, group chat, post likes (`PostLike` table), content reports, and moderation flags.
* `/api/v1/incoscore`: Personal InCoScore breakdown, badges, and paginated leaderboards (`overall`, `domain`, `college`).
* `/api/v1/notifications`: List notifications, unread count badge, mark as read, and WebSocket push stream (`/ws/notifications/{user_id}`).
* `/api/v1/flags`: Feature flag administrative controls and rollout percentage toggles.
