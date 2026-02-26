# BharatAI — Performance Test Results

> Generated from Locust load test: `locustfile.py`

## Test Configuration

| Parameter | Value |
|-----------|-------|
| Virtual users | 500 |
| Ramp-up | 10 min (50 users/sec) |
| Steady-state duration | 30 min |
| Target host | `http://staging.bharatai.in` |
| Tool | Locust 2.23.1 |

## SLO Targets

| Endpoint | SLO (P95) | Target |
|----------|-----------|--------|
| `POST /api/v1/auth/login` | < 200ms | ✅ |
| `POST /api/v1/auth/register` | < 200ms | ✅ |
| `GET /api/v1/feed` | < 500ms | ✅ |
| `GET /api/v1/opportunities` | < 300ms | ✅ |
| `GET /api/v1/incoscore/leaderboard` | < 500ms | ✅ |

## Results Summary

| Endpoint | Requests | Failures | Median (ms) | P95 (ms) | P99 (ms) | RPS |
|----------|----------|----------|-------------|----------|----------|-----|
| `/api/v1/auth/register` | — | — | — | — | — | — |
| `/api/v1/auth/login` | — | — | — | — | — | — |
| `/api/v1/feed` | — | — | — | — | — | — |
| `/api/v1/opportunities` | — | — | — | — | — | — |
| `/api/v1/opportunities/[id]` | — | — | — | — | — | — |
| `/api/v1/applications` | — | — | — | — | — | — |
| `/api/v1/incoscore/leaderboard` | — | — | — | — | — | — |
| `/health` | — | — | — | — | — | — |

> **Note:** Fill in results after running:
> ```bash
> locust -f locustfile.py --host=http://localhost:8000 --users 500 --spawn-rate 50 --run-time 30m --headless --csv=results
> ```

## Database Profiling

Top slow queries from `pg_stat_statements`:

```sql
SELECT query, calls, total_exec_time, mean_exec_time
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;
```

| Query | Calls | Total Time (ms) | Mean Time (ms) | Index Added? |
|-------|-------|-----------------|----------------|-------------|
| — | — | — | — | — |

## Redis Cache Performance

```
redis-cli INFO stats | grep keyspace
```

| Metric | Value | Target |
|--------|-------|--------|
| `keyspace_hits` | — | — |
| `keyspace_misses` | — | — |
| **Hit Rate** | — | > 85% |

## FAISS Vector Search Benchmark

```python
import time, numpy as np, faiss
index = faiss.IndexFlatL2(384)
vectors = np.random.rand(100_000, 384).astype('float32')
index.add(vectors)
query = np.random.rand(1, 384).astype('float32')
start = time.time()
D, I = index.search(query, 10)
elapsed = (time.time() - start) * 1000
print(f"Search latency: {elapsed:.2f}ms")
```

| Vectors | Search Time | Target |
|---------|-------------|--------|
| 100,000 | — ms | < 50ms |

## Celery Throughput Benchmark

| Metric | Value | Target |
|--------|-------|--------|
| Classification throughput | — tasks/sec | > 10/sec |

## Recommendations

1. Add database indexes for any queries with mean time > 50ms
2. Enable Redis pipeline batching for bulk cache operations
3. Consider read replicas if DB pool utilization exceeds 60% under load
