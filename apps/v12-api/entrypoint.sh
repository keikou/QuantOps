#!/usr/bin/env sh
set -e

mkdir -p /app/runtime /app/runtime/logs /app/runtime/verification_logs /app/runtime/sample_outputs

python -m uvicorn ai_hedge_bot.api.app:app --host 0.0.0.0 --port 8000
