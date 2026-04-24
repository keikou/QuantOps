# AES-06 Dynamic Alpha Weighting Engine

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Evaluation / Selection Intelligence v1`
Packet: `AES-06`
Status: `draft`

## Purpose

`AES-06` defines the live adaptive weighting layer after `AES-05`.

It answers:

- how alpha weights should change as live evidence accumulates
- how smoothing and turnover caps prevent overreaction
- what constrained weight proposal should be sent to `MPI` and reviewed by `LCC`

## Core Invariant

```text
Alpha weights must adapt to live evidence while avoiding overreaction to noise.
```

## Canonical Surfaces

1. `POST /system/alpha-dynamic-weights/run`
2. `GET /system/alpha-dynamic-weights/latest`
3. `GET /system/alpha-dynamic-weights/ensemble/{ensemble_id}`
4. `GET /system/alpha-weight-adjustments/latest`
5. `GET /system/alpha-weight-drift/latest`
6. `GET /system/alpha-weight-constraints/latest`
7. `GET /system/alpha-weight-proposals/latest`

## Main Outputs

- target alpha weights
- smoothed alpha weights
- constrained final weights
- weight change reasons
- MPI-ready proposal
- LCC review metadata

## Data Model Draft

- `alpha_weighting_runs`
- `alpha_live_state`
- `alpha_weight_signals`
- `alpha_dynamic_weights`
- `alpha_weight_constraints`
- `alpha_weight_proposals`

## Next Packet

`AES-07: Alpha Kill Switch / Retirement Engine`
