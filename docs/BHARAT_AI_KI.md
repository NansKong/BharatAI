# BharatAI — Complete Master Knowledge Item (KI)

> **Location**: Local Disk D (`d:\BharatAI\docs\BHARAT_AI_KI.md`)
> **Repository**: `NansKong/BharatAI`
> **Version**: 1.0.0 (Updated 2026-09-04)

---

## 1. System Overview & Core Mission
**BharatAI** (`d:\BharatAI`) is India's first AI-powered academic opportunity intelligence platform for college students. The system automatically ingests, classifies, personalizes, and ranks academic opportunities (hackathons, scholarships, research internships, fellowships, workshops) from top Indian institutions and portals (IIT Bombay, IIT Delhi, IISc, AICTE, Startup India, DRDO, SIH, Unstop).

It assists students with application tracking and NLP form autofilling, and ranks student merit using the **InCoScore** engine (0–1000 scale).

---

## 2. Technical Architecture & Component Layout

```
                                  ┌───────────────────────────┐
                                  │       Nginx Proxy         │
                                  └─────────────┬─────────────┘
                                                │
                         ┌──────────────────────┴──────────────────────┐
                         ▼                                             ▼
             ┌───────────────────────┐                     ┌───────────────────────┐
             │ Next.js Frontend App  │                     │  FastAPI Backend App  │
             │      (:3000)          │                     │      (:8000)          │
             └───────────────────────┘                     └───────────┬───────────┘
                                                                       │
                    ┌───────────────────┬──────────────────┬───────────┴───────┐
                    ▼                   ▼                  ▼                   ▼
             ┌──────────────┐    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
             │ PostgreSQL   │    │   Redis 7    │   │ Elasticsearch│   │ Celery Worker│
             │  (Port 5432) │    │  (Port 6379) │   │  (Port 9200) │   │  + Beat      │
             └──────────────┘    └──────────────┘   └──────────────┘   └──────────────┘
```

---

## 3. Technology Stack & Key Dependencies

* **Backend**: FastAPI (Python 3.11, async/await), SQLAlchemy 2.x async ORM, Alembic migrations, Pydantic v2.
* **Database & Caching**: PostgreSQL 15 (`pg_stat_statements` enabled), Redis 7 (rate limiting, queues, JWT revocation blocklist).
* **AI & NLP**:
  * Zero-shot domain classifier: `facebook/bart-large-mnli` (11 domain labels).
  * Embeddings & Vector Search: `sentence-transformers/all-MiniLM-L6-v2` + FAISS index.
  * Resume Extraction: `pdfplumber`/`PyMuPDF` + spaCy NER skill normalization.
* **Background Tasks**: Celery + Celery Beat (web scraping, AI tasks, nightly FAISS rebuild, daily email dispatch).
* **Frontend**: Next.js 14 App Router (TypeScript, Tailwind CSS, Zustand, TanStack Query, Framer Motion, lucide-react).
* **Observability & Security**: Prometheus + Grafana dashboarding, structlog JSON logging, JWT RS256 asymmetric signing, dual-key rotation, sliding-window Redis rate-limiter, `bleach` HTML sanitization.

---

## 4. Key Subsystems & Core Engines

### A. Opportunity Scraping & Monitoring (`app/scrapers/`)
* **Scraper Adapters**: Static (httpx + BeautifulSoup) and Dynamic (Playwright Chromium) scrapers.
* **Deduplication**: SHA-256 content hashing + title cosine similarity ($>90\%$).
* **Dead-letter Queue**: Failed scrape attempts after 3 retries are logged to `scrape_dead_letters`.

### B. AI Domain Classifier (`app/ai/classifier.py`)
* Zero-shot classification into 11 domains: `AI/DS`, `Computer Science`, `Electronics and Communication`, `Mechanical Engineering`, `Civil Engineering`, `Biotechnology`, `Law`, `Management`, `Finance`, `Humanities`, `Government and Policy`.
* Primary score threshold $> 0.60$; unclassified items sent to admin moderation queue (`GET /api/v1/admin/opportunities/unclassified`).

### C. Personalization & Relevance Feed (`app/ai/personalization.py`)
* Dynamic relevance scoring formula:
  $$\text{Relevance Score} = 0.4 \times \text{Interest Match} + 0.3 \times \text{Skill Match} + 0.2 \times \text{Engagement} + 0.1 \times \text{Deadline Urgency}$$
* Cached per user in Redis (TTL 15 minutes) with invalidation hooks on profile updates (`bust_feed_cache`). Cold-start fallback sorts by deadline.

### D. InCoScore Merit Scoring Engine (`app/ai/incoscore.py`)
* Deterministic score computation (0–1000 points):
  * **Hackathons**: 1st (100 pts), 2nd (70 pts), 3rd (50 pts), participant (10 pts).
  * **Research Internships**: Verified internships at 80 pts each (max 3 $\rightarrow$ 240 pts).
  * **Publications**: Peer-reviewed (120 pts), preprint (40 pts).
  * **Competitions**: National (90 pts), State (50 pts), College (20 pts).
  * **Certifications**: Industry (60 pts), NPTEL (30 pts).
  * **Coding Ratings**: LeetCode/CodeForces rating bands (0–100 pts).
  * **Community**: 0.5 pts per post (max 50 pts).
* **Anti-Gaming Safety**: Only `verified=True` achievements earn points; $>5$ submissions in 24h triggers 429 rate limit; duplicate check on title + date.

---

## 5. Development & Operations Shortcuts (`Makefile`)

```bash
make dev          # Start full stack with Docker Compose
make stop         # Stop all active containers
make logs         # Tail logs across all services
make migrate      # Run Alembic migrations
make seed         # Seed development database
make test         # Run backend pytest suite
make test-cov     # Run tests with coverage report
make lint         # Run ruff, black, isort, and eslint linters
make gen-keys     # Generate RS256 RSA key pair
```
