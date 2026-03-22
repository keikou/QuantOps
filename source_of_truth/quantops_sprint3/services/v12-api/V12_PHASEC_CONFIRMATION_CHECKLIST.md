# V12 PhaseC Confirmation Checklist

- [ ] `docker compose up --build` succeeds
- [ ] `POST /run-once` returns `phase_c`
- [ ] `GET /portfolio/expected-returns` returns rows
- [ ] `GET /portfolio/weights` returns rows
- [ ] `GET /portfolio/allocations` returns rows
- [ ] `GET /portfolio/risk` returns rows
- [ ] `GET /portfolio/summary` returns latest portfolio summary
- [ ] `POST /runner/run-cycle` advances `cycle_count`
- [ ] `python -m pytest -q` passes
- [ ] `scripts/check_v12_phasec_quant_system.ps1` passes
