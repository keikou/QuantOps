# Alpha Evaluation / Selection Intelligence Packet 02 Plan

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `AES-02`
Status: `implemented`

## Intent

Extend the evaluation lane into walk-forward and out-of-sample validation by making:

- alpha walk-forward latest
- per-candidate walk-forward detail
- OOS validation summary
- validation decisions
- validation failures

explicit at the system surface.

## Canonical Surfaces

1. `POST /system/alpha-walk-forward/run`
2. `GET /system/alpha-walk-forward/latest`
3. `GET /system/alpha-walk-forward/candidate/{alpha_id}`
4. `GET /system/alpha-oos-validation/latest`
5. `GET /system/alpha-validation-decisions/latest`
6. `GET /system/alpha-validation-failures/latest`

## Dependencies

- `AES-01`
- `AAE v1 checkpoint through AAE-05`
- `ASD v1 checkpoint through ASD-05`

## Verifier

- `test_bundle/scripts/verify_alpha_evaluation_selection_intelligence_packet02.py`
