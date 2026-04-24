# AES-02 Walk-Forward Validation

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Evaluation / Selection Intelligence`
Packet: `AES-02`
Status: `implemented`

## Goal

Require out-of-sample survival before a candidate alpha can be considered production-promotable.

## Scope

`AES-02` adds:

- walk-forward window generation
- per-window train/test metrics
- OOS pass and degradation evaluation
- stability analysis
- validation decision and failure surfaces

## Canonical Outputs

1. `POST /system/alpha-walk-forward/run`
2. `GET /system/alpha-walk-forward/latest`
3. `GET /system/alpha-walk-forward/candidate/{alpha_id}`
4. `GET /system/alpha-oos-validation/latest`
5. `GET /system/alpha-validation-decisions/latest`
6. `GET /system/alpha-validation-failures/latest`

## Supporting Draft

- `docs/AES-02_Walk_Forward_Validation_Design.md`

## Verifier

- `test_bundle/scripts/verify_alpha_evaluation_selection_intelligence_packet02.py`
