# AES-06 Dynamic Alpha Weighting Task

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Evaluation / Selection Intelligence v1`
Packet: `AES-06`
Status: `implemented`

## Active Boundary

Implement a dynamic alpha weighting layer after `AES-05`.

## Required Surfaces

- `POST /system/alpha-dynamic-weights/run`
- `GET /system/alpha-dynamic-weights/latest`
- `GET /system/alpha-dynamic-weights/ensemble/{ensemble_id}`
- `GET /system/alpha-weight-adjustments/latest`
- `GET /system/alpha-weight-drift/latest`
- `GET /system/alpha-weight-constraints/latest`
- `GET /system/alpha-weight-proposals/latest`

## Non-Goals

- do not regenerate alpha
- do not reevaluate alpha quality
- do not redo walk-forward validation
- do not replace MPI/LCC allocation logic
- do not replay completed AES-01 through AES-05 packets

## Completion Evidence

- `alpha_weighting` package exists
- runtime tables exist for weighting runs, live state, signals, dynamic weights, constraints, and proposals
- `/system/*` routes expose dynamic weights, drift, constraints, and proposals
- verifier checks the plan and task surfaces

