# AES-03 Alpha Ensemble Selection

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Evaluation / Selection Intelligence`
Packet: `AES-03`
Status: `implemented`

## Goal

Select a portfolio-ready ensemble from the `AES-02` validated alpha pool rather than promoting isolated alpha one by one.

## Scope

`AES-03` should add:

- validated alpha loading
- ensemble candidate generation
- pairwise correlation and redundancy checks
- marginal contribution scoring
- ensemble scoring and selection
- initial weight allocation
- MPI / LCC-ready payload

## Canonical Outputs

1. `POST /system/alpha-ensemble/run`
2. `GET /system/alpha-ensemble/latest`
3. `GET /system/alpha-ensemble/candidates/latest`
4. `GET /system/alpha-ensemble/candidate/{ensemble_id}`
5. `GET /system/alpha-ensemble-correlation/latest`
6. `GET /system/alpha-marginal-contribution/latest`
7. `GET /system/alpha-ensemble-selection/latest`
8. `GET /system/alpha-ensemble-weights/latest`

## Supporting Drafts

- `docs/AES-03_Alpha_Ensemble_Selection_Engine_Design.md`
- `docs/AES-03_GitHub_Issues_Implementation.md`
- `docs/AES-03_Weight_Optimization_Algorithms.md`
- `docs/AES-03_Portfolio_Integration_MPI_LCC.md`
