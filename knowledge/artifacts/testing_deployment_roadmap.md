# Testing, Security & Deployment Roadmap (`BharatAI`)

## 1. Testing Framework & Verification Protocols

* **Backend Unit & Integration Tests**: Executed via `pytest` (`backend/tests/`).
  * `test_security.py` & `test_auth.py`: Cryptographic key verification, password hashing, JWT expiration, refresh rotation.
  * `test_classifier.py` & `test_resume_parser.py`: Zero-shot domain classifier thresholds, PDF text extraction, spaCy skill extraction.
  * `test_incoscore.py` & `test_anti_gaming.py`: Point accumulation tables, domain weight multipliers, 1000-point capping, velocity checks.
  * `test_feed.py` & `test_applications.py`: Personalization relevance formula, cold-start fallbacks, status state machine transitions.
  * `test_notifications.py` & `test_sources.py`: Template rendering, email preferences, source scraping trigger handlers.

* **Frontend & E2E Testing**:
  * Playwright E2E integration test suite (`frontend/e2e/`) verifying registration, login, feed navigation, application creation, and leaderboard rendering.

* **Load & Performance Benchmark (`locustfile.py`)**:
  * Locust load testing scenarios evaluating 500 virtual user traffic over 30-minute steady states.
  * **Service Level Objectives (SLOs)**: Auth P95 latency $< 200\text{ms}$, Feed P95 latency $< 500\text{ms}$, Opportunities P95 latency $< 300\text{ms}$.

---

## 2. Security Audit & Hardening Matrix

* **Authentication Security**: RS256 RSA asymmetric signatures prevent token forgery. Dual-key decode fallback supports zero-downtime key rotation.
* **Database & Query Protection**: All database interactions use SQLAlchemy ORM parameter binding—0 raw SQL string concatenations exist.
* **Input Sanitization**: All user-submitted Markdown, HTML, and text fields are sanitized via `bleach.clean()` prior to DB persistence.
* **Rate Limiting**: Sliding-window Redis limiter blocks aggressive automated crawling (60 requests/min unauthenticated, 300 requests/min authenticated).
* **Cross-Site Protection**: Strict CORS origin whitelisting matching frontend deployment domain. HSTS header (`max-age=31536000; includeSubDomains`) enforced in production environments.

---

## 3. Disaster Recovery & Backup Protocols (`scripts/backup.sh`)

* **PostgreSQL Backup**: Daily automated `pg_dump` compressed with `gzip` and uploaded to S3-compatible object storage. Retention policy enforces 7 daily, 4 weekly, and 3 monthly snapshots.
* **Redis Persistence**: Both Append-Only File (AOF) logging and RDB snapshotting enabled in `redis.conf` for zero data-loss cache recovery.
* **Elasticsearch Snapshots**: Daily snapshot repository repository synchronization to cloud storage.

---

## 4. Phase Completion Matrix

| Phase | Description | Status |
| :---: | :--- | :---: |
| **0** | Pre-Build Monorepo Setup & CI Configuration | ✅ Completed |
| **1** | Infrastructure Foundation (Docker, Postgres, Redis, Nginx) | ✅ Completed |
| **2** | Backend Foundation, Async ORM Models & JWT RS256 Auth | ✅ Completed |
| **3** | Opportunity Scraping Engine & Source Adapters | ✅ Completed |
| **4** | AI Zero-Shot Domain Classifier & Personalization Feed | ✅ Completed |
| **5** | Application Assistance Engine & NLP Form Autofill | ✅ Completed |
| **6** | Community Features & InCoScore Merit Scoring Engine | ✅ Completed |
| **7** | Multi-Channel Notification Engine (Email + WebSockets) | ✅ Completed |
| **8** | OpenAPI Specification & API Documentation Export | ✅ Completed |
| **9** | Next.js 14 Web Frontend Application (App Router) | ✅ Completed |
| **10** | Production Security Hardening, Caching & Observability | ✅ Completed |
| **11** | Dynamic Feature Flag Rollout & Canary Engine | ✅ Completed |
| **12** | Locust Load Testing & GitHub Actions CI/CD Pipeline | ✅ Completed |
| **13** | Final QA Regression & Production Launch Readiness | ⏳ In Progress |
