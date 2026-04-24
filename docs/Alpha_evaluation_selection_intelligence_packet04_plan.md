# Alpha Evaluation / Selection Intelligence Packet 04 Plan

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `AES-04`
Status: `planned`

## Intent

Extend `AES-03` ensemble selection into explicit economic meaning and factor attribution by making:

- alpha factor attribution latest
- alpha factor exposure
- alpha residual alpha
- alpha economic risk
- alpha factor concentration
- alpha economic meaning
- per-alpha and per-ensemble attribution detail

visible at the system surface.

## Canonical Surfaces

1. `POST /system/alpha-factor-attribution/run`
2. `GET /system/alpha-factor-attribution/latest`
3. `GET /system/alpha-factor-attribution/candidate/{alpha_id}`
4. `GET /system/alpha-factor-exposure/latest`
5. `GET /system/alpha-residual-alpha/latest`
6. `GET /system/alpha-economic-risk/latest`
7. `GET /system/alpha-factor-concentration/latest`
8. `GET /system/alpha-economic-meaning/latest`
9. `GET /system/alpha-factor-attribution/ensemble/{ensemble_id}`

## Dependencies

- `AES-03`
- `MPI-05`
- `LCC-05`

## Verifier

- `test_bundle/scripts/verify_alpha_evaluation_selection_intelligence_packet04.py`
