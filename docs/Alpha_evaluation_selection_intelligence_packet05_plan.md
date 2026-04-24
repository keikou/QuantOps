# Alpha Evaluation / Selection Intelligence Packet 05 Plan

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `AES-05`
Status: `implemented`

## Intent

Extend `AES-04` attribution into capacity and crowding risk control by making:

- alpha capacity latest
- per-alpha capacity detail
- crowding risk
- market impact
- ensemble capacity

visible at the system surface.

## Canonical Surfaces

1. `POST /system/alpha-capacity/run`
2. `GET /system/alpha-capacity/latest`
3. `GET /system/alpha-capacity/candidate/{alpha_id}`
4. `GET /system/alpha-crowding/latest`
5. `GET /system/alpha-impact/latest`
6. `GET /system/alpha-capacity/ensemble/{ensemble_id}`

## Dependencies

- `AES-03`
- `AES-04`
- `MPI-05`
- `LCC-05`

## Verifier

- `test_bundle/scripts/verify_alpha_evaluation_selection_intelligence_packet05.py`
