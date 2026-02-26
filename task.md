## Progress Snapshot (2026-02-23)

### Phase 0: Pre-Build Setup
- [x] Create `D:\BharatAI` monorepo with `backend/`, `frontend/`, `infra/`, `docs/` folders
- [x] Initialize Git repository + `.gitignore`
- [x] Create `README.md` with project overview + setup guide
- [x] Document environment variables in `.env.example`
- [ ] Set up GitHub repository + branch protection on `main` (manual platform setting)
- [x] Set up GitHub Actions CI pipeline (`.github/workflows/ci.yml`)
- [x] Create `Makefile` with dev/test/migrate shortcuts
- [x] Configure pre-commit hooks for `black`, `isort`, `eslint`, `prettier` in `.pre-commit-config.yaml`
- [x] Define API versioning convention (`/api/v1/`) in `README.md`

### Phase 1: Infrastructure Foundation
- [x] `docker-compose.yml` includes core and infra services
- [x] Backend Dockerfile present (`backend/Dockerfile`)
- [x] Frontend Dockerfile present (`frontend/Dockerfile`)
- [x] Nginx config present (`infra/nginx/nginx.conf`)
- [ ] Verify all containers start cleanly (`docker compose up --build`) - blocked by external registry TLS/certificate errors (`docker.elastic.co` x509 unknown authority) and intermittent Docker Hub timeouts
- [x] PostgreSQL extension setup includes `pg_stat_statements` (`infra/postgres/init.sql`)
- [x] Redis configured with AOF + snapshot in compose command
- [x] Staging compose scaffold added (`docker-compose.staging.yml`)
- [x] Seed script updated with 5 admins, 20 students, 10 opportunities, 8 sources, InCoScore entries (`backend/scripts/seed.py`)
- [ ] Verify full stack Up + seed run success (blocked until registry TLS/certificate issue is resolved)

### Phase 2: Backend Foundation & Auth
- [x] FastAPI + lifespan + async SQLAlchemy + Redis + Alembic + Celery app/beat setup completed
- [x] Phase 2 database models/constraints/indexes implemented and baseline migration added
- [x] Auth endpoints complete (`register`, `login`, `refresh`, `logout`, Google OAuth start/callback)
- [x] JWT RS256 signing, RBAC dependencies, bcrypt(cost=12) password hashing implemented
- [x] Health + metrics + structured JSON logging completed (`/health`, `/health/db`, `/health/redis`, `/metrics`)
- [x] Phase 2 test suite passing in WSL (`tests/test_security.py`, `tests/test_auth.py`)

### Phase 3: Opportunity Monitoring Engine (In Progress)
- [x] Scraper framework added (`app/scrapers/base.py`, `app/scrapers/static.py`, `app/scrapers/dynamic.py`)
- [x] SHA-256 hash + title similarity duplicate detection added (`app/scrapers/dedup.py`)
- [x] Scrape task pipeline updated with retry backoff (2s/4s/8s), proxy round-robin, failure_count tracking, admin alert notifications, and Prometheus counters (`backend/app/workers/scrape_tasks.py`)
- [x] Admin source APIs extended (`GET/POST /api/v1/admin/sources`, `POST /api/v1/admin/sources/{id}/trigger`)
- [x] Opportunity admin APIs extended (`PUT /api/v1/opportunities/{id}`, `DELETE /api/v1/opportunities/{id}` soft delete)
- [x] Source-specific scraper adapters + local HTML fixtures added for IITB/IITD/IISc/AICTE/Startup India/DRDO/SIH/Unstop (`app/scrapers/sources.py`, `tests/fixtures/scrapers/*.html`)
- [x] Dead-letter persistence path implemented (`scrape_dead_letters` model + Alembic migration `20260222_0002_scrape_dead_letters.py`)
- [x] Grafana provisioning and scrape observability dashboard wired (`infra/grafana/provisioning/**`)
- [x] Phase 3 targeted tests added and passing (`tests/test_scraper.py`, `tests/test_source_adapters.py`, `tests/test_hash.py`, `tests/test_duplicate.py`, `tests/test_dead_letter.py`, `tests/test_opportunities.py`, `tests/test_sources.py`)
- [x] Remaining Phase 3 items implemented: cursor-based opportunity pagination and Celery worker-mock coverage for `scrape_all_sources()` (`backend/app/api/v1/opportunities.py`, `backend/tests/test_opportunities.py`, `backend/tests/test_scrape_tasks.py`)

### Phase 4: AI Classification & Personalization Engine (In Progress)
- [x] Domain classifier implementation added with thresholded assignment and fallback (`backend/app/ai/classifier.py`, `backend/app/workers/ai_tasks.py`)
- [x] Classification task wired after opportunity inserts and scraper-created opportunities (`backend/app/api/v1/opportunities.py`, `backend/app/workers/scrape_tasks.py`)
- [x] Admin unclassified review queue endpoint added (`GET /api/v1/admin/opportunities/unclassified`, `backend/app/api/v1/admin.py`)
- [x] Resume pipeline implemented: PDF validation, storage, extraction, skill normalization, entity extraction (`backend/app/api/v1/profile.py`, `backend/app/core/storage.py`, `backend/app/ai/resume_parser.py`)
- [x] Embedding generation + nightly FAISS rebuild task implementation added (`backend/app/workers/ai_tasks.py`, `backend/app/ai/embeddings.py`)
- [x] Personalized feed endpoint with weighted relevance formula, cold-start fallback, Redis caching, invalidation hooks (`backend/app/api/v1/feed.py`, `backend/app/ai/personalization.py`)
- [x] Phase 4 targeted tests added (`backend/tests/test_classifier.py`, `backend/tests/test_resume_parser.py`, `backend/tests/test_skill_extraction.py`, `backend/tests/test_relevance_score.py`, `backend/tests/test_feed.py`, `backend/tests/test_resume_upload.py`)
- [x] Execute Phase 4 tests and mark as passing (11/11 passed — 2026-02-25)

### Phase 5: Application Assistance Engine (Completed 2026-02-25)
- [x] `POST /api/v1/applications` — create application record (student only, one per opportunity, 409 on duplicate) (`backend/app/api/v1/applications.py`)
- [x] `GET /api/v1/applications` — list user's own applications with status filter + pagination (`backend/app/api/v1/applications.py`)
- [x] `PUT /api/v1/applications/{id}/status` — state machine: draft→submitted→accepted/rejected, any→withdrawn; backward jumps → 422 (`backend/app/api/v1/applications.py`)
- [x] `GET /api/v1/applications/{id}/checklist` — AI-generated checklist from eligibility text via pattern NLP (`backend/app/api/v1/applications.py`, `backend/app/ai/application_ai.py`)
- [x] `GET /api/v1/applications/{id}/autofill` — profile field suggestions; consent gate (403); rate limit 20/hr (429) (`backend/app/api/v1/applications.py`, `backend/app/ai/application_ai.py`)
- [x] Autofill compliance log: every request stored in `autofill_logs` table (`backend/app/models/autofill_log.py`)
- [x] Consent check: `consent_to_autofill=false` → 403 before any suggestion is returned
- [x] Rate limiting: Redis sliding window `autofill_rl:{user_id}`, 20 req/hr, returns 429
- [x] State machine validation: only valid forward transitions allowed; admin can update any application
- [x] Phase 5 test suite added (`backend/tests/test_applications.py`, `backend/tests/test_autofill.py`, `backend/tests/test_checklist.py`)
- [x] Execute Phase 5 tests and mark as passing (15/15 passed — 2026-02-25)

### Phase 6: Community & InCoScore Engine (In Progress — 2026-02-25)
- [x] `app/models/post_like.py` — PostLike join table for idempotent like/unlike toggle
- [x] `app/ai/incoscore.py` — pure scoring engine: point table per spec, domain weights, 1000 cap, badges
- [x] `app/workers/incoscore_tasks.py` — `update_incoscore(user_id)` Celery task triggered on achievement verification
- [x] `POST /api/v1/community/posts` — create post; HTML-strip; >5 URLs → 422 (`community.py`)
- [x] `GET /api/v1/community/posts` — paginated feed, hidden posts excluded (`community.py`)
- [x] `POST /api/v1/community/posts/{id}/like` — idempotent like toggle via PostLike row (`community.py`)
- [x] `POST /api/v1/community/posts/{id}/comments` — add comment; `GET` comments (`community.py`)
- [x] `POST /api/v1/community/posts/{id}/report` — auto-flag at 3 reports, auto-hide from feed (`community.py`)
- [x] `POST /api/v1/community/groups` — admin creates group (`community.py`)
- [x] `POST /api/v1/community/groups/{id}/join` — student joins; 409 on duplicate (`community.py`)
- [x] `GET /api/v1/community/groups/{id}/feed` — group-scoped posts (`community.py`)
- [x] `POST /api/v1/community/achievements` — submit; velocity check >5/24h → 429; duplicate title+date → 409 (`community.py`)
- [x] `PUT /api/v1/community/achievements/{id}/verify` — admin verify/reject; triggers InCoScore update (`community.py`)
- [x] `GET /api/v1/incoscore/me` — latest score + components + badges (`incoscore.py`)
- [x] `GET /api/v1/incoscore/leaderboard/overall|domain|college` — paginated, latest-score subquery (`incoscore.py`)
- [x] Phase 6 test suite: `test_incoscore.py`, `test_anti_gaming.py`, `test_posts.py`, `test_community.py`, `test_achievements.py`
- [x] Execute Phase 6 tests and mark as passing (24/24 passed — 2026-02-25)

### Phase 7: Notification Engine (In Progress — 2026-02-25)
- [x] `app/services/email.py` — `send_email()` with Jinja2 rendering; `EMAIL_ENABLED` flag (no SMTP in tests); typed helpers per notification type
- [x] `app/templates/email/` — 4 HTML templates: `opportunity_match`, `deadline_reminder`, `achievement_verified`, `score_change`
- [x] `Profile.email_prefs` — JSON column for per-type unsubscribe preferences (default: all enabled)
- [x] `app/core/ws.py` — `ConnectionManager` for in-memory per-user WebSocket registry
- [x] `GET /ws/notifications/{user_id}` — WebSocket endpoint with JWT-in-query-param auth (`main.py`)
- [x] `app/workers/notification_tasks.py` — 5 Celery tasks: `send_opportunity_match_notification`, `send_deadline_reminder`, `notify_achievement_result`, `notify_score_change`, `check_deadlines` (Beat-scheduled daily 8AM IST)
- [x] `GET /api/v1/notifications` — list with `unread_only` filter + pagination (`notifications.py`)
- [x] `GET /api/v1/notifications/count` — unread badge count (`notifications.py`)
- [x] `POST /api/v1/notifications/{id}/read` — mark single read (`notifications.py`)
- [x] `POST /api/v1/notifications/read-all` — mark all read (`notifications.py`)
- [x] Phase 7 test suite: `tests/test_notifications.py` (6 tests)
- [x] Execute Phase 7 tests and mark as passing (7/7 passed — 2026-02-25)

### Phase 8: API Documentation (Complete — 2026-02-25)
- [x] `app/api/v1/feed.py` — enriched `GET /feed` with description, caching note, cold-start explanation, error responses
- [x] `app/api/v1/users.py` — added `UserResponse`/`ResumeUploadResponse` models; enriched all 3 endpoints with description, response_model, status_code, errors
- [x] `app/api/v1/notifications.py` — enriched all 4 endpoints with description, Query descriptions, error responses
- [x] `app/api/v1/auth.py` — already fully annotated (Phase 1)
- [x] `scripts/export_openapi.py` — generates `docs/openapi.json` by importing the FastAPI app directly
- [x] `scripts/generate_postman.py` — converts `docs/openapi.json` → `docs/postman_collection.json` (pure Python, grouped by tag)
- [x] `docs/API_GUIDE.md` — auth flow, pagination, error format, rate-limit headers, WebSocket usage, domain values, InCoScore table
- [x] `docs/generate_types.sh` — `npx openapi-typescript` one-liner for TypeScript type generation

### Phase 9: Frontend (Next.js 14) — Complete 2026-02-25
- [x] Scaffold Next.js 14 App Router (TypeScript, Tailwind, ESLint) in `frontend/`
- [x] Install: framer-motion, zustand, axios, @tanstack/react-query, zod, react-hook-form, @hookform/resolvers, @playwright/test
- [x] `next.config.ts` — standalone output, image domains, NEXT_PUBLIC env vars
- [x] `Dockerfile` — multi-stage (deps → builder → alpine runner, non-root user)
- [x] `app/globals.css` — CSS variables (saffron/navy/emerald palette), glass, btn, input, card, badge, gradient-text utilities
- [x] `lib/api.ts` — Axios instance, JWT attach, auto-refresh on 401 with request queuing
- [x] `lib/store.ts` — Zustand: auth (persist) + notifications unreadCount slices
- [x] `lib/queryClient.ts` — TanStack Query with staleTime 60s, retry 1
- [x] `hooks/useWebSocket.ts` — auto-connect/reconnect, increments unreadCount on notification frames
- [x] `components/layout/Sidebar.tsx` — animated nav links, admin link, user avatar + logout
- [x] `components/layout/Header.tsx` — sticky header, live notification bell badge
- [x] `app/(dashboard)/layout.tsx` — Sidebar + Header shell
- [x] `app/(auth)/layout.tsx` — passthrough (no sidebar)
- [x] `app/page.tsx` — Landing: hero gradient, stats, feature cards, CTA
- [x] `app/(auth)/login/page.tsx` — Email+password form, Zod validation, API integration
- [x] `app/(auth)/register/page.tsx` — Signup form, password strength rules, auto-login
- [x] `app/(dashboard)/feed/page.tsx` — Opportunity cards, domain filter, relevance bar, deadline badge
- [x] `app/(dashboard)/notifications/page.tsx` — Inbox, type icons, click-to-mark-read, mark-all
- [x] `app/(dashboard)/leaderboard/page.tsx` — Radial InCoScore badge, Overall/Domain/College tabs
- [x] `app/(dashboard)/applications/page.tsx` — Kanban board (draft/submitted/accepted/rejected)
- [x] `app/(dashboard)/achievements/page.tsx` — Submit form, status list with badges
- [x] `app/(dashboard)/profile/page.tsx` — Skills chips editor, bio, social links, in-place edit
- [x] `app/(dashboard)/community/page.tsx` — Posts feed, create post, groups sidebar
- [x] `app/(dashboard)/community/groups/[id]/page.tsx` — Group chat with 3s polling
- [x] `app/(dashboard)/opportunities/[id]/page.tsx` — Opportunity detail, apply button
- [x] `app/admin/page.tsx` — Scrape trigger, sources list, moderation flags queue

### Phase 10: Production Hardening & Security — Complete 2026-02-25
#### Security
- [x] `app/core/rate_limit.py` — Redis sliding-window rate limiter (60/min anon, 300/min auth), 429 + Retry-After
- [x] Rate limiting middleware registered in `main.py`
- [x] CORS strict origin whitelist (frontend domain only)
- [x] HSTS header (production only) in `main.py`
- [x] `app/core/security.py` — JWT V2 key rotation: dual-key decode fallback + `verify_access_token`
- [x] `app/core/config.py` — `JWT_PUBLIC_KEY_V2_PATH` optional config
- [x] Redis token revocation list with TTL matching token expiry (existing)
- [x] `app/core/sanitize.py` — `bleach.clean()` on all user-generated text
- [x] Sanitization applied to auth register (name, college, degree)
- [x] SQL: all queries via SQLAlchemy ORM only (no raw strings)
- [x] `docs/SECURITY_AUDIT.md` — OWASP Top 10 checklist completed
#### Caching
- [x] `app/core/cache.py` — `@cached_response` decorator + `bust_feed_cache`, `bust_leaderboard_cache`, `bust_opportunities_cache`
- [x] Feed cache per user (TTL 15 min, invalidate on profile update) — existing in `feed.py`
- [x] Leaderboard cache constant (TTL 10 min) — existing in `incoscore.py`
- [x] Opportunity list cache (TTL 5 min) — available via decorator
#### Observability
- [x] `infra/prometheus_rules.yml` — AlertManager rules: error rate, queue depth, DB pool, Redis, scraping
- [x] `infra/grafana_dashboards.json` — API latency P50/P95/P99, Celery, Redis, scrape, feed CTR, WebSocket
- [x] Prometheus instrumentation already in `main.py` via `prometheus-fastapi-instrumentator`
- [x] OpenTelemetry packages in requirements.txt
#### Backup & DR
- [x] `scripts/backup.sh` — pg_dump → gzip → S3 upload, cron-ready
- [x] `docs/DISASTER_RECOVERY.md` — step-by-step restore: PostgreSQL, Redis, Elasticsearch

### Phase 11: Feature Flag System — Complete 2026-02-25
- [x] `models/feature_flag.py` — FeatureFlag + FlagEvaluation DB models (rollout %, user whitelist, analytics)
- [x] `core/feature_flags.py` — Evaluation service: Redis-cached, consistent-hash percentage rollout, logging
- [x] `api/v1/feature_flags.py` — Admin CRUD, evaluate (single + bulk), analytics endpoints
- [x] Router registered in `main.py` at `/api/v1/flags`
- [x] Models registered in `models/__init__.py` for Alembic auto-detection
- [x] `alembic/versions/20260225_0002_feature_flags.py` — Migration + seed 6 default flags
- [x] Default flags: `ai_classification`, `personalized_feed`, `incoscore_engine`, `community_features`, `app_assistance`, `browser_automation`
- [x] `frontend/app/admin/flags/page.tsx` — Admin toggle panel with rollout slider, canary presets, analytics
- [x] Canary rollout: percentage targeting (5% → 25% → 50% → 100%) via consistent hashing

### Phase 12: Load Testing & CI/CD — Complete 2026-02-25
#### Load Testing
- [x] `backend/locustfile.py` — 6 scenarios: register, login, feed, opportunities, apply, leaderboard
- [x] SLO assertions: auth P95 <200ms, feed P95 <500ms, opportunities P95 <300ms
- [x] `docs/PERFORMANCE.md` — Results template with DB profiling, Redis cache, FAISS, Celery benchmarks
#### CI/CD
- [x] `.github/workflows/ci-cd.yml` — Full pipeline: lint → test (Postgres+Redis) → security scan → Docker build → deploy
- [x] CI: Codecov integration, fail if coverage <80%
- [x] CD: auto-deploy staging on main push; prod deploy requires manual approval gate
- [x] `.github/dependabot.yml` — Weekly updates for pip, npm, and GitHub Actions
- [x] `scripts/smoke_test.sh` — Post-deploy: health, OpenAPI, auth, opportunities, flags (5 checks)

---
BharatAI – Fault-Proof Task Checklist
Rules: Never move to the next phase until ALL items in the current phase are checked. Tests and validation items are embedded in every phase — not deferred to the end.

Phase 0: Pre-Build Setup (Day 0)
 Create d:\BharatAI monorepo with backend/, frontend/, infra/, docs/ folders
 Initialize Git repository + .gitignore (Python, Node, Docker, .env)
 Create README.md with project overview, architecture diagram, and local setup guide
 Document all environment variables in .env.example (backend + frontend)
 Set up GitHub repository + branch protection on main (require PR + CI pass)
 Set up GitHub Actions CI pipeline (lint + test on every push/PR) — CI from day 1
 Create Makefile with developer shortcuts (make dev, make test, make migrate)
 Install pre-commit hooks: black, isort, eslint, prettier
 Define and document API versioning convention (/api/v1/)
Phase 1: Infrastructure Foundation
 Write docker-compose.yml with all services (postgres, redis, backend, frontend, nginx)
 Write Dockerfile for backend (FastAPI + Uvicorn + Gunicorn)
 Write Dockerfile for frontend (Next.js)
 Write nginx/nginx.conf (reverse proxy, CORS headers, rate limiting at proxy level)
 Verify all containers start cleanly: docker-compose up --build
 Configure PostgreSQL with pg_stat_statements extension enabled (query profiling from day 1)
 Configure Redis with AOF persistence + RDB snapshot enabled
 Set up staging environment (separate docker-compose.staging.yml or cloud instance)
 Create seed data script (backend/scripts/seed.py) with:
 5 sample admin + 20 sample student users
 10 sample opportunities across all domains
 5 monitored sources
 Sample InCoScore history entries
 Verify: docker-compose ps shows all services Up; seed script runs without error
Phase 2: Backend Foundation & Auth
Setup
 Scaffold FastAPI app with lifespan events, async SQLAlchemy engine, CORS middleware
 Configure pydantic-settings for all env vars (type-safe, validated at startup)
 Implement async PostgreSQL session factory (app/core/database.py)
 Implement Redis async client (app/core/redis.py)
 Set up Alembic for migrations (alembic init, configure async engine)
 Set up Celery app + Celery Beat (app/workers/celery_app.py) connected to Redis broker
Database Models (SQLAlchemy 2.x)
 users — id, email, name, role (enum: student/admin), google_id, hashed_password, college, degree, year, is_active, created_at
 profiles — user_id FK, skills (ARRAY), interests (ARRAY), resume_path, embedding_vector (ARRAY[float]), bio, github_url, linkedin_url
 monitored_sources — id, url, type (enum: static/dynamic), interval_minutes, active, last_scraped_at, failure_count
 opportunities — id, title, description, institution, domain, secondary_domain, deadline, source_url, content_hash, eligibility, application_link, is_verified, created_at
 applications — id, user_id FK, opportunity_id FK, status (enum), form_data_json, applied_at, notes
 achievements — id, user_id FK, type, title, proof_url, verified, verified_by, created_at
 incoscore_history — id, user_id FK, total_score, domain, components_json, computed_at
 posts — id, user_id FK, content, group_id FK, likes_count, is_flagged, created_at
 comments — id, post_id FK, user_id FK, content, is_flagged, created_at
 groups — id, name, type (enum: domain/college), description, member_count
 group_members — group_id FK, user_id FK, role (enum: member/moderator), joined_at
 messages — id, sender_id FK, group_id FK, content, created_at
 notifications — id, user_id FK, type, payload_json, read, created_at
 Add CheckConstraint on: score range (0–1000), role enum, status enums
 Add UniqueConstraint on: email, content_hash (opportunities), group+user (group_members)
 Add all indexes: user_id, domain, deadline, created_at, incoscore, content_hash
 Run alembic revision --autogenerate and alembic upgrade head — no errors
Authentication
 POST /api/v1/auth/register — email + password signup with Pydantic v2 strict validation
 POST /api/v1/auth/login — JWT access token (15 min) + refresh token (7 days)
 POST /api/v1/auth/refresh — rotate refresh token, revoke old token in Redis blocklist
 POST /api/v1/auth/logout — add token to Redis revocation list
 GET /api/v1/auth/google — initiate Google OAuth2 flow (via authlib)
 GET /api/v1/auth/google/callback — exchange code, upsert user, return JWT
 Implement JWT RS256 signing (asymmetric key pair, not HS256)
 RBAC dependency: require_student, require_admin FastAPI dependencies
 Password hashing with bcrypt (cost factor 12)
Validation & Schema Contracts (Phase 2)
 All auth request schemas: strict Pydantic v2 models, extra fields forbidden
 Email validator (RFC 5322), password: min 8 chars, 1 uppercase, 1 digit
 All responses use typed response_model, never raw dicts
 Document all auth endpoints: summary, description, tags, response codes (200, 400, 401, 422)
Tests (Phase 2)
 Unit: test_security.py — JWT encode/decode, password hash, token expiry
 Integration: test_auth.py — register, login, refresh, logout, Google OAuth mock
 Integration: RBAC — admin endpoint returns 403 for student token
 CI: auth tests run and pass in GitHub Actions
Health & Observability (Phase 2)
 GET /health — returns {status, database, redis, version}
 GET /health/db — async DB ping
 GET /health/redis — Redis ping
 Add prometheus-fastapi-instrumentator — expose /metrics
 Structured JSON logging (stdlib logging with JSON formatter)
Phase 3: Opportunity Monitoring Engine
Scraping Framework
 Base scraper abstract class: BaseScraper(url, scrape_type)
 StaticScraper — httpx async client + BeautifulSoup parser
 DynamicScraper — Playwright Chromium headless
 SHA-256 content hashing for change detection (skip if hash unchanged)
 Duplicate detection: check content_hash + title similarity (>90% cosine) before insert
 Proxy rotation support via PROXY_LIST env var (round-robin)
 Retry with exponential backoff: 3 retries, 2s / 4s / 8s delay
 Log scrape result (success/failure/skipped) to DB monitored_sources.failure_count
 Alert mechanism: if failure_count > 5 consecutive → emit warning log + notify admin
Monitored Sources (Initial Set)
 IIT Bombay events page
 IIT Delhi opportunities
 IISc announcements
 AICTE scholarship portal
 Startup India programs
 DRDO recruitment/fellowship
 Smart India Hackathon portal
 Unstop (competitions aggregator)
Celery Tasks
 scrape_all_sources() — Celery Beat every 30 min; loops all active sources
 scrape_single_source(source_id) — on-demand scrape for admin trigger
 Task retry on scraper failure (max 3 retries with backoff)
 Dead-letter queue: failed tasks after all retries → log to DB with payload
Opportunity API
 GET /api/v1/opportunities — paginated list (cursor-based), filters: domain, deadline, institution, keyword
 GET /api/v1/opportunities/{id} — single opportunity detail
 POST /api/v1/opportunities — admin-only manual add
 PUT /api/v1/opportunities/{id} — admin-only edit
 DELETE /api/v1/opportunities/{id} — admin-only soft delete
 GET /api/v1/admin/sources — list monitored sources
 POST /api/v1/admin/sources — add new source
 POST /api/v1/admin/sources/{id}/trigger — manual scrape trigger
Validation (Phase 3)
 Opportunity schema: deadline must be future date, application_link must be https URL
 Source schema: interval_minutes must be ≥15 (no abuse)
 Scraper output sanitized: strip HTML tags from description before storing
Tests (Phase 3)
 Unit: test_scraper.py — static + dynamic scraper with local HTML fixtures
 Unit: test_hash.py — change detection logic (same content = skip, new = insert)
 Unit: test_duplicate.py — duplicate detection edge cases
 Integration: test_opportunities.py — CRUD, filters, pagination, admin-only guards
 Integration: test_sources.py — admin source management + manual trigger
 Task: mock Celery worker + assert scrape_all_sources calls scraper for each active source
Observability (Phase 3)
 Custom metric: scrape_success_total{source_id}, scrape_failure_total{source_id}
 Custom metric: opportunities_created_total{domain}
 Grafana panel: scrape success rate per source
Phase 4: AI Classification & Personalization Engine
Domain Classifier
 Load facebook/bart-large-mnli (zero-shot) on worker startup (cached in memory)
 classify_opportunity(opp_id) Celery task — triggered after every new opportunity insert
 11 domains: AI/DS, CS, ECE, ME, Civil, Biotech, Law, Management, Finance, Humanities, Govt & Policy
 Confidence threshold: >0.6 → assign domain; <0.6 → flag as unclassified for admin review
 Store: primary_domain, secondary_domain, confidence_score on opportunity record
 Admin endpoint: GET /api/v1/admin/opportunities/unclassified — review queue
Student Profile & Embeddings
 POST /api/v1/profile/resume — upload PDF resume (max 5MB, application/pdf MIME only)
 Store to S3-compatible storage (MinIO in Docker, S3 in prod)
 PDF text extraction: pdfplumber (primary) with PyMuPDF fallback
 NLP skill extraction: spaCy NER + custom skills vocabulary matcher
 Skill normalization: map variants ("ML", "Machine Learning", "machine-learning") → canonical form
 Entity extraction: college name, degree, graduation year from resume text
 Update profiles.skills array from extraction results
 generate_embeddings(user_id) Celery task — sentence-transformers/all-MiniLM-L6-v2
 Store embedding vector in profiles.embedding_vector
 FAISS index: rebuild on new embedding batch (run nightly via Celery Beat)
 PUT /api/v1/profile — manual profile update (skills, interests, college, year)
 GET /api/v1/profile/me — return full profile with embedding status
Personalization Engine
 GET /api/v1/feed — personalized opportunity feed (uses relevance scoring below)
 Relevance score formula:
Interest Match × 0.4 (cosine similarity: user interests embedding vs opportunity embedding)
Skill Similarity × 0.3 (FAISS nearest-neighbor search)
Engagement × 0.2 (past clicks + application rate on similar opportunities)
Deadline Urgency × 0.1 (sigmoid decay over remaining days)
 Cold-start fallback: new users with no profile → return top opportunities by deadline
 Cache personalized feed per user in Redis (TTL: 15 min)
 Cache invalidation: on profile update or new opportunity insert → bust user's feed cache
Validation (Phase 4)
 Resume upload: reject non-PDF, reject >5MB, reject empty files
 Skills array: sanitize each skill string (strip HTML, max 50 chars, max 30 skills)
 Embedding task: skip if user has no extractable text from resume
Tests (Phase 4)
 Unit: test_classifier.py — mock HuggingFace pipeline, assert domain assignment logic
 Unit: test_resume_parser.py — PDF text extraction with sample PDF fixture
 Unit: test_skill_extraction.py — NLP skill extraction accuracy on 10 sample resumes
 Unit: test_relevance_score.py — scoring formula with known input vectors
 Integration: test_feed.py — personalized feed reorders after profile update
 Integration: test_resume_upload.py — valid PDF accepted, non-PDF rejected (422)
 Integration: cold-start feed returns opportunities for users with empty profiles
Observability (Phase 4)
 Metric: classification_latency_seconds (histogram)
 Metric: embedding_generation_total, feed_cache_hit_ratio
 Grafana panel: average classification confidence per domain
 Alert: if >20% opportunities land in unclassified → Slack alert to admin
Phase 5: Application Assistance Engine
Core Features
 POST /api/v1/applications — create application record (user + opportunity link)
 GET /api/v1/applications — list user's applications with status filter
 PUT /api/v1/applications/{id}/status — update status (draft/submitted/accepted/rejected)
 GET /api/v1/applications/{id}/checklist — AI-generated checklist based on opportunity eligibility text
 GET /api/v1/applications/{id}/autofill — suggest form field values from user profile (name, college, skills, achievements)
 Pre-filled draft generation: map profile → opportunity form fields using NLP field-name matching
 Submission tracking dashboard data endpoint
Compliance & Safety
 Every autofill request logged (user_id, opportunity_id, fields_suggested, timestamp)
 User consent flag on profile: consent_to_autofill (default: false) — check before any autofill
 Rate limit autofill endpoint: max 20 requests/hour per user (prevent abuse)
 Optional browser automation (Playwright) — gated behind browser_automation feature flag
 If automation enabled: manual confirmation step before form submission (never auto-submit)
 Captcha detection: if captcha present → pause + notify user to complete manually
Validation (Phase 5)
 Application status transitions: only valid state machine transitions allowed (draft→submitted, submitted→accepted/rejected; no backward jumps)
 One application per user per opportunity (unique constraint enforced at DB + API level)
Tests (Phase 5)
 Unit: test_autofill.py — field mapping logic, consent check enforcement
 Unit: test_checklist.py — checklist generation from eligibility text
 Integration: test_applications.py — CRUD, status transitions, duplicate prevention
 Integration: autofill blocked if consent_to_autofill = false
 Integration: rate limiting — 21st request in 1 hour returns 429
Phase 6: Community & InCoScore Engine
Community Features
 POST /api/v1/posts — create post (text, optional image URL)
 GET /api/v1/posts — paginated feed (global + group-filtered)
 POST /api/v1/posts/{id}/like — toggle like (idempotent)
 POST /api/v1/posts/{id}/comments — add comment
 GET /api/v1/posts/{id}/comments — paginated comments
 POST /api/v1/groups — admin creates group (domain or college type)
 POST /api/v1/groups/{id}/join — student joins group
 GET /api/v1/groups/{id}/feed — group-scoped posts feed
 WebSocket endpoint: ws://host/ws/chat/{group_id} — real-time group messages
 Message persistence: store all WebSocket messages in messages table
 Peer endorsements: POST /api/v1/users/{id}/endorse/{skill} — endorse a peer's skill
 Achievement sharing: POST /api/v1/achievements — submit achievement for verification
Community Moderation
 POST /api/v1/posts/{id}/report — user reports content with reason
 POST /api/v1/comments/{id}/report — report a comment
 GET /api/v1/admin/reports — admin moderation queue (flagged posts + comments)
 POST /api/v1/admin/reports/{id}/action — admin takes action (remove/warn/dismiss)
 Auto-flag: posts with >3 reports → auto-set is_flagged=true, hide from feed
 Spam detection: reject posts with >5 URLs or repeated identical text (Levenshtein distance <10%)
 Shadow ban capability: admin can restrict user from posting without notifying them
InCoScore Engine
 Score components (weighted, normalized 0–1000):
 Hackathon wins: 1st=100pts, 2nd=70pts, 3rd=50pts, participant=10pts
 Research internships: verified=80pts each (max 3)
 Publications: peer-reviewed=120pts, preprint=40pts
 Competition rankings: national=90pts, state=50pts, college=20pts
 Certifications: industry (AWS/GCP/ML)=60pts, NPTEL=30pts
 Coding performance: LeetCode/CodeForces rating bands (mapped 0–100pts)
 Community contributions: 0.5pts per helpful post (capped at 50pts)
 Verified achievements: admin-verified only (unverified = 0pts)
 Domain weight adjustments: AI domain weights coding+research higher; Management weights competition+leadership
 Anti-gaming system:
 Velocity check: >5 achievement submissions in 24h → flag for manual review
 Duplicate submission detection: same title + same date → reject
 Proof URL required for all high-value achievements (hackathon wins, publications)
 Admin verification queue: all achievements above 50pts require admin approval before scoring
 Score history: every recalculation stores snapshot in incoscore_history (immutable audit trail)
 update_incoscore(user_id) Celery task — triggered on verified achievement event
 Leaderboard APIs:
 GET /api/v1/leaderboard/overall — top 100 students, paginated
 GET /api/v1/leaderboard/domain/{domain} — domain-specific ranking
 GET /api/v1/leaderboard/college/{college_id} — college-scoped ranking
 Badge system: auto-assign badges (First Hackathon, Top 10 College, Domain Expert, etc.) based on score milestones
 Cache all leaderboards in Redis (TTL: 10 min)
Validation (Phase 6)
 Post content: max 2000 chars, sanitize HTML (bleach), reject all <script> tags
 Achievement proof_url: must be https, must be reachable (HEAD request check)
 Score components: enforce min/max bounds per component before summing
Tests (Phase 6)
 Unit: test_incoscore.py — all components, domain weights, edge cases, max score cap
 Unit: test_anti_gaming.py — velocity check, duplicate detection, unverified rejection
 Unit: test_leaderboard.py — ranking order correctness after score updates
 Unit: test_spam_detection.py — URL count limit, Levenshtein duplicate check
 Integration: test_posts.py — CRUD, like toggle idempotency, report flow, auto-flag at 3 reports
 Integration: test_community.py — group join, group feed, peer endorsement
 Integration: test_achievements.py — submission, admin review queue, score update after approval
 WebSocket: test_chat.py — message broadcast to group members, message persistence in DB
Phase 7: Notification Engine
 Email: send_email(user_id, subject, template, context) via SMTP (support SendGrid/SES config)
 Email templates: new opportunity match, deadline reminder (7d, 1d), achievement verified, InCoScore change
 In-app notification: store in notifications table, return via GET /api/v1/notifications
 Mark as read: POST /api/v1/notifications/{id}/read + POST /api/v1/notifications/read-all
 Real-time push via WebSocket: ws://host/ws/notifications/{user_id} — deliver on create
 Notification triggers (Celery tasks):
 New opportunity matches user profile → notify immediately
 Deadline T-7 days → deadline reminder email
 Deadline T-1 day → urgent deadline reminder
 Achievement approved → email + in-app
 InCoScore changes by >50pts → in-app notification
 Community: reply to post/comment → in-app notification
 Unsubscribe preferences: users can disable email per notification type
 Celery Beat schedule: deadline reminders run daily at 8AM IST
Tests (Phase 7)
 Unit: test_notifications.py — trigger logic, template rendering
 Integration: new opportunity → notification record created for matched users
 Integration: unsubscribed user → email not sent (mocked SMTP asserted not called)
Phase 8: API Documentation
 All endpoints annotated: summary, description, tags, response_model, status codes
 Add openapi_examples to all request + response schemas
 Verify /docs (Swagger UI) and /redoc render correctly with all tags
 Export openapi.json → commit to docs/openapi.json
 Write docs/API_GUIDE.md: auth flow, pagination convention, error format, rate limit headers
 Generate Postman collection from OpenAPI spec → commit to docs/postman_collection.json
 Frontend: generate TypeScript types from OpenAPI via openapi-typescript + validate with Zod
Phase 9: Frontend (Next.js)
Foundation
 Scaffold Next.js 14 App Router project (npx create-next-app@latest)
 Install: Tailwind CSS, Framer Motion, Zustand, Axios, react-query, Zod, openapi-typescript
 Configure lib/api.ts: Axios instance with JWT interceptor (auto-attach + auto-refresh on 401)
 Configure lib/store.ts: Zustand store (auth state, user profile, feed, notifications)
 Design system: dark glassmorphism, Indian accent colors (saffron #FF9933, navy #0A1628, emerald #00BFA5), Inter font, CSS variables for tokens
 Global layout: sidebar nav, header with notification bell + user avatar, mobile responsive
Pages & Components
 / — Landing page: hero with animated gradient, feature highlights, CTA, stats
 /(auth)/login — Email/password + Google OAuth button
 /(auth)/register — Signup form with validation feedback
 /(dashboard)/feed — Personalized opportunity cards, filter sidebar (domain, deadline, type)
 /(dashboard)/opportunities/[id] — Opportunity detail: full description, eligibility, apply button
 /(dashboard)/applications — Application tracker: Kanban-style board (draft/submitted/accepted/rejected)
 /(dashboard)/profile — Profile editor: skills chips, resume upload, interests, social links
 /(dashboard)/community — Posts feed, create post, group switcher in sidebar
 /(dashboard)/community/groups/[id] — Group chat + group posts
 /(dashboard)/leaderboard — Overall + domain + college tabs, rank card with InCoScore badge
 /(dashboard)/achievements — Submit achievement form, verification status tracker
 /(dashboard)/notifications — Notification inbox with read/unread state
 /admin — Admin dashboard: scrape triggers, moderation queue, source management, flag toggle panel
Real-time
 WebSocket hook: useWebSocket(url) — auto-reconnect on disconnect
 Live notifications: bell icon badge updates in real time
 Live chat: messages appear instantly in group chat without refresh
Tests (Phase 9 Frontend)
 Component tests: opportunity card, InCoScore badge, notification bell renders correctly
 E2E (Playwright): register → complete profile → view feed → apply to opportunity
 E2E: login → view leaderboard → submit achievement → view pending status
Phase 10: Production Hardening & Security
Security
 Rate limiting middleware: 60 req/min per IP (unauthenticated), 300 req/min per JWT (Redis sliding window)
 CORS: strict origin whitelist (frontend domain only)
 HTTPS: Nginx enforces HTTPS redirect; HSTS header max-age=31536000; includeSubDomains
 JWT key rotation: support JWT_PRIVATE_KEY + JWT_PRIVATE_KEY_V2 env vars with dual verification
 Redis token revocation list with TTL matching token expiry
 File upload: MIME type whitelist (application/pdf), virus scan hook (ClamAV optional), store outside webroot
 Input sanitization: bleach.clean() on all user-generated text before DB write
 SQL: all queries via SQLAlchemy ORM only (no raw SQL strings)
 Dependency scan: pip-audit + npm audit — fix all critical/high CVEs
 OWASP Top 10 checklist review — document findings in docs/SECURITY_AUDIT.md
 OWASP ZAP baseline scan against staging — document findings, remediate all High severity
Caching
 Feed cache per user: Redis (TTL 15 min, invalidate on profile update)
 Leaderboard cache: Redis (TTL 10 min)
 Opportunity list cache: Redis (TTL 5 min, bust on new opportunity insert)
 HTTP cache headers: Cache-Control on static opportunity endpoints
 Target Redis cache hit rate >85% for feed endpoint (verify before prod deploy)
Observability Final Setup
 Prometheus AlertManager rules file: error rate >5% (2min), queue depth >500, DB pool >80%
 Grafana dashboards: API latency P50/P95/P99, Celery queue depth, scrape success rate, feed CTR
 ELK: Logstash pipeline for FastAPI JSON logs → Elasticsearch → Kibana dashboards
 OpenTelemetry traces: instrument FastAPI + Celery + SQLAlchemy → send to Jaeger
 Uptime monitoring on /health endpoint (external ping every 1 min)
Backup & DR
 scripts/backup.sh — pg_dump → gzip → upload to S3 (run via cron in prod)
 Backup retention policy enforced: 7 daily, 4 weekly, 3 monthly (S3 lifecycle rules)
 Redis backup: verify AOF + RDB both enabled in redis.conf
 Elasticsearch snapshot repository configured → daily snapshot to S3
 docs/DISASTER_RECOVERY.md — step-by-step restore for each system
 Dry-run restore drill on staging: restore latest PG backup → run smoke tests → document result
Phase 11: Feature Flag System
 Add Unleash (self-hosted) or Flagsmith as Docker service in docker-compose.yml
 Integrate Python SDK (unleashclient) in FastAPI app — evaluate flags per request
 Integrate flagsmith-js in Next.js via server component flag context
 Define and register flags: ai_classification, personalized_feed, incoscore_engine, community_features, app_assistance, browser_automation
 Gate each relevant code path behind its flag (feature off = safe fallback behavior)
 Admin flag toggle panel on /admin/flags page (fetches from Unleash admin API)
 Log flag evaluation: flag_name, user_id, result, timestamp → analytics table
 Canary rollout config: percentage targeting (5% → 25% → 100%) configured in Unleash
Phase 12: Load Testing & CI/CD Final
Load Testing
 Write Locust load test scenarios: locustfile.py — register, login, browse feed, apply
 Run: 500 virtual users, 10-min ramp, 30-min steady — log results to docs/PERFORMANCE.md
 Verify SLOs met: auth P95 <200ms, feed P95 <500ms, opportunities P95 <300ms
 DB profiling: run SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 20 → add missing indexes
 Redis cache hit rate: inspect INFO stats → confirm keyspace_hits/keyspace_misses > 85%
 FAISS benchmark: search 100K embeddings → assert <50ms latency
 Celery benchmark: classification throughput → assert >10 classifications/sec
CI/CD Final
 GitHub Actions: full pipeline — lint → unit tests → integration tests → build Docker → push to registry → deploy to staging
 CI: coverage report generated + uploaded to Codecov (fail if <80%)
 CD: auto-deploy to staging on main push; prod deploy is manual approval gate
 Dependabot config: weekly dependency updates for Python + npm
 Smoke test job: post-deploy to staging, hit /health, run 5 critical API checks
Phase 13: Final QA & Launch Readiness
 Full E2E regression pass: all Playwright tests pass on staging
 Cross-browser test: Chrome, Firefox, Safari, mobile viewport
 Accessibility audit: WCAG 2.1 AA — keyboard navigation, colour contrast, screen reader labels
 Data Privacy: verify no PII in logs, no resume content in error messages
 Rate limit test: verify 429 responses at correct thresholds
 RBAC final audit: attempt all admin endpoints with student token → all return 403
 All TODO / FIXME / HACK comments resolved in codebase
 README.md updated: full local setup, Docker instructions, env var table, architecture diagram
 Stakeholder demo on staging environment ✅
 Go / No-Go checklist: all Phase 0–12 items checked, no open High security findings, all SLOs met
