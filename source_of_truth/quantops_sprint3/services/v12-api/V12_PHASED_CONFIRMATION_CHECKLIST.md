# V12 PhaseD Confirmation Checklist

- [ ] Docker image builds successfully
- [ ] API `/health` returns phase `D`
- [ ] `/run-once` returns `phase_c` and `phase_d`
- [ ] `/analytics/shadow-summary` returns non-null summary after one run
- [ ] `/execution/shadow-orders` returns at least one row after one run
- [ ] `/execution/shadow-fills` returns at least one row after one run
- [ ] `/analytics/order-lifecycle` returns transitions
- [ ] `/execution/latency` returns latency snapshots
- [ ] `pytest -q` passes
- [ ] PowerShell one-command Docker verification passes
