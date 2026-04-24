# Alpha Evaluation / Selection Intelligence Packet 01 Plan

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `AES-01`
Status: `implemented`

## Intent

Establish the first evaluation lane that distinguishes real alpha from noise by making:

- alpha evaluation summary
- alpha decay analysis
- alpha correlation matrix
- alpha robustness ranking
- alpha selection decisions

explicit at the system surface.

## Canonical Surfaces

1. `GET /system/alpha-evaluation/latest`
2. `GET /system/alpha-decay-analysis/latest`
3. `GET /system/alpha-correlation-matrix/latest`
4. `GET /system/alpha-robustness-ranking/latest`
5. `GET /system/alpha-selection-decisions/latest`
6. `POST /system/alpha-evaluation/run`
7. `GET /system/alpha-evaluation/candidate/{alpha_id}`

## Dependencies

- `AAE v1 checkpoint through AAE-05`
- `ASD v1 checkpoint through ASD-05`
- `SERI-05`
- `MPI-05`
- `LCC-05`

## Verifier

- `test_bundle/scripts/verify_alpha_evaluation_selection_intelligence_packet01.py`
