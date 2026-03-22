# PhaseH Sprint4 Confirmation Checklist

- [ ] `python -m pytest -q` passes
- [ ] `/alpha/overview` returns status=ok
- [ ] `/alpha/generate` registers a generated alpha
- [ ] `/alpha/test` produces execution-aware evaluation metrics
- [ ] `/alpha/evaluate` appends ranking and promotion/demotion events
- [ ] `/alpha/ranking` returns ranked rows
- [ ] `/alpha/library` returns alpha library rows
- [ ] `/dashboard/alpha-factory` returns summary cards
- [ ] `/dashboard/global` includes alpha factory cards
- [ ] FastAPI uses lifespan, not on_event
