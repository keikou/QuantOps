# PhaseH Sprint1 Confirmation Checklist

- [ ] `pytest -q` passes with PhaseH Sprint1 tests
- [ ] `docker compose up --build` starts the API on port 8000
- [ ] `GET /system/health` returns `phase=H` and `sprint=1`
- [ ] `GET /strategy/registry` returns at least 3 seeded strategies
- [ ] `POST /strategy/allocate-capital` returns allocations, netting, and risk blocks
- [ ] `GET /strategy/risk-budget` returns latest per-strategy risk usage
- [ ] `GET /analytics/strategy-summary` returns strategy aggregate metrics
- [ ] `GET /dashboard/global` includes strategy cards
- [ ] `runtime/verification_logs/` contains JSON outputs and checklist markdown after verification
