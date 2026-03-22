#!/usr/bin/env bash
set -euo pipefail

targets=(
  "http://localhost:8000/system/health"
  "http://localhost:8000/runtime/runs"
  "http://localhost:8000/risk/latest"
  "http://localhost:8000/analytics/performance"
  "http://localhost:8000/governance/regime"
  "http://localhost:8000/runtime/modes/current"
  "http://localhost:8000/acceptance/status"
  "http://localhost:8000/incidents/latest"
  "http://localhost:8000/analytics/shadow-summary"
  "http://localhost:8010/api/v1/health"
  "http://localhost:8010/api/v1/modes/current"
  "http://localhost:8010/api/v1/acceptance/status"
  "http://localhost:8010/api/v1/incidents/latest"
  "http://localhost:8010/api/v1/risk/latest"
  "http://localhost:8010/api/v1/analytics/performance"
  "http://localhost:8010/api/v1/governance/regime"
)
for url in "${targets[@]}"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
  if [ "$code" = "200" ]; then
    echo "[PASS] $url 200"
  else
    echo "[FAIL] $url $code"
    exit 1
  fi
done
echo "Sprint5 integrated API check completed."
