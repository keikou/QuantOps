# Sprint4 FINAL v6 fix

This build rewrites `apps/quantops-api/app/repositories/analytics_repository.py`
to fix the indentation error introduced in the previous auto-patch.

## Fixed
- valid `class AnalyticsRepository` indentation
- `_ensure_tables()` defined correctly inside the class
- insert methods call `_ensure_tables(conn)` safely
- `init_db()` retained for worker bootstrap

## Goal
Clean Docker startup for:
- `v12-api`
- `quantops-api`
- `quantops-worker`
