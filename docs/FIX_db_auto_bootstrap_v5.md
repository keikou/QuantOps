# Sprint4 FINAL DB auto-bootstrap fix

This version adds automatic DuckDB schema creation for the QuantOps worker.

## Added / changed
- `apps/quantops-api/app/db/init_db.py`
  - creates the required tables at worker startup
- `apps/quantops-api/app/repositories/risk_repository.py`
  - ensures `risk_snapshots`
- `apps/quantops-api/app/repositories/analytics_repository.py`
  - ensures `alpha_performance_snapshots`
  - ensures `execution_quality_snapshots`
  - ensures `portfolio_diagnostics_snapshots`
- `apps/quantops-api/app/worker.py`
  - calls `init_db()` before entering the run loop

## Goal
Eliminate worker crashes caused by missing empty-volume DuckDB tables.
