#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${BASE_URL:-http://127.0.0.1:8010}"
docker compose up --build -d >/dev/null
sleep 2
cleanup() { docker compose down >/dev/null; }
trap cleanup EXIT
curl -fsS "$BASE_URL/api/v1/health" >/dev/null
curl -fsS -X POST "$BASE_URL/api/v1/monitoring/refresh" >/dev/null
curl -fsS -X POST "$BASE_URL/api/v1/analytics/refresh" >/dev/null
curl -fsS -X POST "$BASE_URL/api/v1/governance/refresh" >/dev/null
curl -fsS -X POST "$BASE_URL/api/v1/approval/request" -H 'content-type: application/json' -d '{"request_type":"promotion","target_id":"s1","requested_by":"operator","summary":{"reason":"qa"}}' >/dev/null
curl -fsS -X POST "$BASE_URL/api/v1/incidents/create" -H 'content-type: application/json' -d '{"incident_type":"service_unhealthy","severity":"medium","title":"Test incident","description":"one-step validation"}' >/dev/null
curl -fsS "$BASE_URL/api/v1/admin/audit-logs" >/dev/null
echo "Sprint2-integrated Sprint3 Docker one-step verification passed."
