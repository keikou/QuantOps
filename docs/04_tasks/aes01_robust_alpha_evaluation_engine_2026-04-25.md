# AES-01 Robust Alpha Evaluation Engine

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Evaluation / Selection Intelligence`
Packet: `AES-01`
Status: `implemented`

## Goal

Create the first alpha evaluation lane so the system can distinguish real alpha from noise before promotion into the active strategy pool.

## Scope

`AES-01` should make explicit:

- forward return evaluation
- cost-adjusted scoring
- decay detection
- robustness ranking
- redundancy filtering
- selection decision

## Canonical Outputs

1. `GET /system/alpha-evaluation/latest`
2. `GET /system/alpha-decay-analysis/latest`
3. `GET /system/alpha-correlation-matrix/latest`
4. `GET /system/alpha-robustness-ranking/latest`
5. `GET /system/alpha-selection-decisions/latest`
6. `POST /system/alpha-evaluation/run`
7. `GET /system/alpha-evaluation/candidate/{alpha_id}`

## Supporting Drafts

- `docs/AES-01_GitHub_Issues.md`
- `docs/AES_Threshold_Tuning_Strategy.md`
- `docs/AES-02_Walk_Forward_Validation_Design.md`

## Core Rules

- `ASD` generates alpha
- `AES` evaluates alpha
- `AAE` manages alpha lifecycle
- Portfolio consumes only promoted alpha that passed evaluation

## Verifier

- `test_bundle/scripts/verify_alpha_evaluation_selection_intelligence_packet01.py`
