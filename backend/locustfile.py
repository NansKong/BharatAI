"""
BharatAI — Locust Load Test Scenarios

Simulates realistic user flows:
  1. Register a new account
  2. Login and get JWT
  3. Browse personalized feed
  4. Browse / filter opportunities
  5. Apply to an opportunity
  6. View leaderboard

Run:
  locust -f locustfile.py --host=http://localhost:8000 \
         --users 500 --spawn-rate 50 --run-time 30m
"""
from __future__ import annotations

import random
import string
import uuid

from locust import HttpUser, between, events, task


def _random_email() -> str:
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"loadtest_{rand}@test.bharatai.in"


def _random_password() -> str:
    return f"Test{uuid.uuid4().hex[:8]}!"


class BharatAIUser(HttpUser):
    """
    Simulates a typical BharatAI student user session.
    Wait 1–3 seconds between requests (realistic pacing).
    """

    wait_time = between(1, 3)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.email = _random_email()
        self.password = _random_password()
        self.access_token = ""
        self.opportunity_ids: list[str] = []

    def on_start(self):
        """Each virtual user registers, then logs in."""
        self._register()
        self._login()

    # ── Auth Flows ──────────────────────────────────────────

    def _register(self):
        with self.client.post(
            "/api/v1/auth/register",
            json={
                "name": f"LoadTest User {uuid.uuid4().hex[:6]}",
                "email": self.email,
                "password": self.password,
                "college": "IIT Bombay",
                "degree": "B.Tech CS",
                "year": random.randint(1, 4),
            },
            name="/api/v1/auth/register",
            catch_response=True,
        ) as resp:
            if resp.status_code == 201:
                data = resp.json()
                self.access_token = data.get("access_token", "")
                resp.success()
            elif resp.status_code == 400:
                # Email already exists — not a failure
                resp.success()
            else:
                resp.failure(f"Register failed: {resp.status_code}")

    def _login(self):
        with self.client.post(
            "/api/v1/auth/login",
            json={"email": self.email, "password": self.password},
            name="/api/v1/auth/login",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                self.access_token = data.get("access_token", "")
                resp.success()
            else:
                resp.failure(f"Login failed: {resp.status_code}")

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}"}

    # ── Core Task Flows ─────────────────────────────────────

    @task(5)
    def browse_feed(self):
        """Most common action: browse the personalized feed."""
        with self.client.get(
            "/api/v1/feed?limit=20",
            headers=self._auth_headers(),
            name="/api/v1/feed",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code == 401:
                self._login()  # Re-auth
                resp.success()
            else:
                resp.failure(f"Feed failed: {resp.status_code}")

    @task(4)
    def list_opportunities(self):
        """Browse / filter opportunities."""
        domains = ["ai_ds", "cs", "ece", "management", ""]
        domain = random.choice(domains)
        params = {"limit": 20}
        if domain:
            params["domain"] = domain

        with self.client.get(
            "/api/v1/opportunities",
            params=params,
            headers=self._auth_headers(),
            name="/api/v1/opportunities",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                self.opportunity_ids = [item["id"] for item in items[:5]]
                resp.success()
            elif resp.status_code == 401:
                self._login()
                resp.success()
            else:
                resp.failure(f"Opportunities list failed: {resp.status_code}")

    @task(2)
    def view_opportunity_detail(self):
        """View a specific opportunity."""
        if not self.opportunity_ids:
            return
        opp_id = random.choice(self.opportunity_ids)
        with self.client.get(
            f"/api/v1/opportunities/{opp_id}",
            headers=self._auth_headers(),
            name="/api/v1/opportunities/[id]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            elif resp.status_code == 401:
                self._login()
                resp.success()
            else:
                resp.failure(f"Opportunity detail failed: {resp.status_code}")

    @task(1)
    def apply_to_opportunity(self):
        """Apply to a random opportunity."""
        if not self.opportunity_ids:
            return
        opp_id = random.choice(self.opportunity_ids)
        with self.client.post(
            "/api/v1/applications",
            json={"opportunity_id": opp_id, "cover_letter": "Load test application."},
            headers=self._auth_headers(),
            name="/api/v1/applications",
            catch_response=True,
        ) as resp:
            if resp.status_code in (201, 400, 409):
                resp.success()  # 400/409 = already applied
            elif resp.status_code == 401:
                self._login()
                resp.success()
            else:
                resp.failure(f"Apply failed: {resp.status_code}")

    @task(2)
    def view_leaderboard(self):
        """View the overall leaderboard."""
        with self.client.get(
            "/api/v1/incoscore/leaderboard/overall?limit=20",
            headers=self._auth_headers(),
            name="/api/v1/incoscore/leaderboard",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code == 401:
                self._login()
                resp.success()
            else:
                resp.failure(f"Leaderboard failed: {resp.status_code}")

    @task(1)
    def health_check(self):
        """Hit the public health endpoint."""
        self.client.get("/health", name="/health")


# ── Performance SLO Assertions ──────────────────────────────────────────────


@events.quitting.add_listener
def check_slos(environment, **kwargs):
    """
    After the load test completes, check if SLOs were met.
    Fails the test run (non-zero exit) if any SLO is violated.
    """
    stats = environment.runner.stats

    slos = {
        "/api/v1/auth/login": 200,  # P95 < 200ms
        "/api/v1/auth/register": 200,  # P95 < 200ms
        "/api/v1/feed": 500,  # P95 < 500ms
        "/api/v1/opportunities": 300,  # P95 < 300ms
    }

    violations = []
    for endpoint, max_p95_ms in slos.items():
        entry = stats.get(endpoint, "GET")
        if entry and entry.num_requests > 0:
            p95 = entry.get_response_time_percentile(0.95)
            if p95 and p95 > max_p95_ms:
                violations.append(f"{endpoint}: P95={p95:.0f}ms (SLO: <{max_p95_ms}ms)")

    if violations:
        print("\n❌ SLO VIOLATIONS:")
        for v in violations:
            print(f"  - {v}")
        environment.process_exit_code = 1
    else:
        print("\n✅ All SLOs met!")
