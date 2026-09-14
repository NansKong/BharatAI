# Frontend Architecture, Design System & Infrastructure Operations (`BharatAI`)

## 1. Field Notes Neubrutalist Design System (`frontend/`)

The platform underwent a complete visual transformation from standard AI-SaaS gradient templates to a bespoke **"Field Notes" Neubrutalist Design System** inspired by physical academic print, dense indexes, and editorial field journals.

### Key Visual & Architectural Tokens (`app/globals.css`):
* **Typography**:
  * **Headlines**: *Instrument Serif* (Display & page headers).
  * **Body**: *Inter* (Clean, highly legible interface text).
  * **Metadata/Badges**: *JetBrains Mono* (Code, numbers, tags, timestamp stamps).
* **Colors & Textures**:
  * **Linen Canvas Background**: `#F7F4EE` (`var(--bg-base)`) providing a tactile, non-glare paper texture.
  * **Ink Color**: `#0F0F11` (`var(--text-main)`) for maximum contrast.
  * **Accent Color Palette**: Yellow `#F1C40F`, Cyan/Blue `#3498DB`, Pink `#E91E63`, Emerald `#2ECC71`, Teal `#1ABC9C`.
* **Borders & Shadows**:
  * **Hard Border**: `2px solid #0F0F11` (`var(--border-hard)`).
  * **Hard Shadow**: `4px 4px 0px #0F0F11` (`var(--shadow-hard)`).
* **Components**:
  * `FieldCard`: High-contrast card with linen background, hard borders, and offset shadow.
  * `StickerBadge`: Pill-shaped badge with rotation transforms (`transform: rotate(-2deg)`), bright background fills, and bold monospace labels.
  * `NumCircle`: Circular numerical stamp for merit ranks and avatar initials.

---

## 2. Persistent Navigation Architecture (`components/layout/Sidebar.tsx`)

Navigation is centralized in the sticky header component `<TopNav />` (re-exported as `Sidebar` for layout compatibility). It remains mounted and visible across every single route (landing, public opportunity index, login, and protected dashboard routes).

### Dynamic Navigation Items:
* **Public & Base Links**: `INDEX` (`/`), `OPPORTUNITIES` (`/opportunities`), `INCOSCORE` (`/leaderboard`), `COMMUNITY` (`/community`).
* **Authenticated Links**: `MY FEED` (`/feed`), `APPLICATIONS` (`/applications`), `NOTIFS` (`/notifications` with unread counter badge).
* **Admin Links**: `ADMIN` (`/admin` - visible only when logged in as admin role).
* **User Status & Auth**:
  * **Logged Out**: Displays `LOGIN` button and `JOIN INDEX ↗` sticker button.
  * **Logged In**: Displays initial avatar circle (`B BharatAI`), user first name, and `LOGOUT ↗` button.

---

## 3. App Router Page Hierarchy

* `/`: Editorial landing hero with search bar, live index stats, category filtering, and direct links to public opportunities.
* `/(auth)/login` & `/(auth)/register`: High-contrast, hard-bordered form cards with sticker badges and Zod/FastAPI validation.
* `/opportunities`: Full-page searchable and filterable opportunity index with vectorized match bars and category pills.
* `/(dashboard)/feed`: Personalized opportunity feed with auto-refresh stickers and deadline cards.
* `/(dashboard)/applications`: Application tracker presented as an editorial Kanban board with numbered stage counters.
* `/(dashboard)/profile`: Student merit stamp card with resume upload, skills sticker library, and bio editor.
* `/(dashboard)/leaderboard`: Monotone list rankings featuring InCoScore breakdown cards and merit badges.
* `/(dashboard)/community`: Editorial community feed with discussion cards, category tags, and post creator.
* `/(dashboard)/notifications`: Monotone notification list with sticker classification badges.

---

## 4. Backend Resiliency & Test Seeding

* **Database Seeding (`scripts/seed.py`)**:
  * **Student Accounts**: `student1@example.com` through `student20@example.com` (Password: `Student@123`).
  * **Admin Accounts**: `admin1@bharatai.in` through `admin5@bharatai.in` (Password: `Admin@123`).
  * **Seeded Data**: 8 monitored sources, 10 opportunities, and 20 InCoScore historical score entries.
* **Redis Offline Fallback (`app/core/redis.py`)**:
  * Configured all Redis operations (`cache_set`, `cache_get`, `add_to_blocklist`, etc.) to wrap calls in safe checks.
  * If Redis is uninitialized or unreachable, authentication, JWT token generation, and caching operations fall back gracefully without throwing `AttributeError` exceptions or returning 500 errors.

---

## 5. Infrastructure Operations & Stack

```
                  ┌────────────────────────┐
                  │      Nginx Proxy       │
                  │       (Port 80)        │
                  └───────────┬────────────┘
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
   ┌───────────────────────┐     ┌───────────────────────┐
   │ Next.js Frontend App  │     │  FastAPI Backend App  │
   │      (Port 3000)      │     │      (Port 8000)      │
   └───────────────────────┘     └───────────┬───────────┘
                                             │
      ┌───────────────────┬──────────────────┼───────────────────┐
      ▼                   ▼                  ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ PostgreSQL   │   │   Redis 7    │   │ Elasticsearch│   │ Celery Worker│
│  (Port 5432) │   │  (Port 6379) │   │  (Port 9200) │   │  + Beat      │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
```
