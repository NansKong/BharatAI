#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# BharatAI — Post-Deploy Smoke Tests
# Usage: bash scripts/smoke_test.sh https://staging.bharatai.in
# ─────────────────────────────────────────────────────────────
set -euo pipefail

BASE_URL="${1:?Usage: smoke_test.sh <BASE_URL>}"
PASS=0
FAIL=0

check() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"

    status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" || echo "000")

    if [ "$status" = "$expected_status" ]; then
        echo "  ✅ $name (HTTP $status)"
        PASS=$((PASS + 1))
    else
        echo "  ❌ $name (HTTP $status, expected $expected_status)"
        FAIL=$((FAIL + 1))
    fi
}

echo "🔍 Running smoke tests against $BASE_URL"
echo ""

# 1. Health endpoint
check "Health check" "$BASE_URL/health"

# 2. API docs (non-production only)
check "OpenAPI schema" "$BASE_URL/openapi.json"

# 3. Auth endpoint exists (should return 422 without body, not 500)
check "Auth register (validation)" "$BASE_URL/api/v1/auth/register" "422"

# 4. Opportunities list (requires auth → 401)
check "Opportunities (auth required)" "$BASE_URL/api/v1/opportunities" "401"

# 5. Feature flags (admin required → 401)
check "Feature flags (auth required)" "$BASE_URL/api/v1/flags" "401"

echo ""
echo "─────────────────────────────────"
echo "Results: $PASS passed, $FAIL failed"
echo "─────────────────────────────────"

if [ "$FAIL" -gt 0 ]; then
    echo "❌ Smoke tests FAILED"
    exit 1
else
    echo "✅ All smoke tests passed!"
    exit 0
fi
