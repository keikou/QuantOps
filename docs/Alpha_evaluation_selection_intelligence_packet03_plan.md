# Alpha Evaluation / Selection Intelligence Packet 03 Plan

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `AES-03`
Status: `implemented`

## Intent

Extend evaluation and validation into ensemble construction by making:

- alpha ensemble latest
- alpha ensemble candidates
- alpha ensemble correlation
- alpha marginal contribution
- alpha ensemble selection
- alpha ensemble weights

explicit at the system surface.

## Canonical Surfaces

1. `POST /system/alpha-ensemble/run`
2. `GET /system/alpha-ensemble/latest`
3. `GET /system/alpha-ensemble/candidates/latest`
4. `GET /system/alpha-ensemble/candidate/{ensemble_id}`
5. `GET /system/alpha-ensemble-correlation/latest`
6. `GET /system/alpha-marginal-contribution/latest`
7. `GET /system/alpha-ensemble-selection/latest`
8. `GET /system/alpha-ensemble-weights/latest`

## Dependencies

- `AES-02`
- `MPI-05`
- `LCC-05`

## Verifier

- `test_bundle/scripts/verify_alpha_evaluation_selection_intelligence_packet03.py`
