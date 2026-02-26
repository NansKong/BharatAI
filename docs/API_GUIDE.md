# BharatAI API Guide

> **Base URL** `https://api.bharatai.in` · Dev `http://localhost:8000`
> **Swagger UI** `/docs` · **ReDoc** `/redoc` · **OpenAPI JSON** `/openapi.json`

---

## Authentication

BharatAI uses **JWT Bearer tokens** (RS256). All protected endpoints require:

```http
Authorization: Bearer <access_token>
```

### Flow

```
POST /api/v1/auth/register   →  { access_token, refresh_token, token_type, expires_in }
POST /api/v1/auth/login      →  { access_token, refresh_token, token_type, expires_in }
POST /api/v1/auth/refresh    →  new { access_token, refresh_token }  (rotation)
POST /api/v1/auth/logout     →  204 No Content  (blocklists the JTI in Redis)
```

| Token | TTL | Notes |
|-------|-----|-------|
| `access_token` | 30 min | Short-lived; attach to every request |
| `refresh_token` | 7 days | One-time use; rotated on each `/refresh` call |

**Google OAuth:** `GET /api/v1/auth/google` → redirect → `GET /api/v1/auth/google/callback` → tokens.

---

## Pagination

All list endpoints use `limit` / `offset` query parameters:

```
GET /api/v1/opportunities?limit=20&offset=0
GET /api/v1/notifications?limit=20&offset=40&unread_only=true
```

Response containers include `total` for computing page count:

```json
{
  "items": [...],
  "total": 142,
  "limit": 20,
  "offset": 0
}
```

---

## Error Format

All errors follow the standard FastAPI detail format:

```json
{ "detail": "Human-readable error message" }
```

| Status | Meaning |
|--------|---------|
| `400` | Bad request / business rule violation |
| `401` | Missing or invalid JWT |
| `403` | Authenticated but insufficient role |
| `404` | Resource not found |
| `409` | Conflict (duplicate resource) |
| `422` | Validation error (field-level) |
| `429` | Rate limit or anti-gaming threshold exceeded |
| `503` | Database or Redis unavailable |

Validation errors (422) include per-field detail:

```json
{
  "detail": [
    { "loc": ["body", "email"], "msg": "value is not a valid email address", "type": "value_error.email" }
  ]
}
```

---

## Rate Limiting

> Phase 10 implements sliding-window rate limiting via Redis. Headers are returned on every response.

| Header | Meaning |
|--------|---------|
| `X-RateLimit-Limit` | Max requests allowed in the window |
| `X-RateLimit-Remaining` | Requests left in the current window |
| `X-Process-Time` | Server processing time in seconds |
| `X-Request-ID` | Unique request UUID for tracing |

---

## WebSocket — Real-time Notifications

Connect to receive push notifications in real time:

```
ws://localhost:8000/ws/notifications/{user_id}?token=<access_token>
```

- The server sends JSON frames whenever a notification is created for the user:

```json
{
  "type": "notification",
  "id": "uuid",
  "title": "New opportunity match",
  "message": "AI Research Fellowship is available"
}
```

- Reconnect on disconnect (the server does not keep state across reconnects).
- Close codes: `4001` = invalid token, `4003` = token user_id mismatch.

---

## Domains

Valid `domain` values used across opportunities, achievements, and leaderboards:

| Value | Label |
|-------|-------|
| `ai_ds` | AI & Data Science |
| `cs` | Computer Science |
| `management` | Management |
| `research` | Research |
| `engineering` | Engineering |
| `social` | Social Impact |

---

## InCoScore

The InCoScore (1–1000) is computed automatically when an achievement is verified:

| Achievement Type | Base Points |
|-----------------|-------------|
| `hackathon` | 80 pts |
| `internship` | 100 pts |
| `publication` | 150 pts |
| `competition` | 70 pts |
| `certification` | 40 pts |
| `coding` | 30 pts |
| `community` | 20 pts |

Domain weights and a 1000-pt total cap are applied. Leaderboards are cached in Redis (TTL: 10 min).

---

## Generating Client Types (TypeScript)

```bash
# Install
npm install -D openapi-typescript

# Generate types from the exported spec
npx openapi-typescript docs/openapi.json -o frontend/src/types/api.d.ts
```

---

## Postman Collection

```bash
cd backend
python scripts/export_openapi.py      # → docs/openapi.json
python scripts/generate_postman.py    # → docs/postman_collection.json
```

Import `docs/postman_collection.json` into Postman. Set the `base_url` collection variable to `http://localhost:8000` and `access_token` after login.
