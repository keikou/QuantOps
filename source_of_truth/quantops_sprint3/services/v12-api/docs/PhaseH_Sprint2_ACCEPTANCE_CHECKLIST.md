# PhaseH Sprint2 Acceptance Checklist

- [ ] `python -m pytest -q` passes
- [ ] FastAPI startup uses lifespan, not `on_event`
- [ ] `POST /research-factory/experiments/register` works
- [ ] `POST /research-factory/datasets/register` works
- [ ] `POST /research-factory/features/register` works
- [ ] `POST /research-factory/validations/register` works
- [ ] `POST /research-factory/models/register` works
- [ ] `GET /research-factory/overview` returns registry counts
- [ ] `GET /dashboard/research` shows research factory cards
- [ ] Docker startup succeeds with `docker compose up --build`
