# Alpha Evaluation / Selection Intelligence Packet 06 Plan

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Evaluation / Selection Intelligence v1`
Packet: `AES-06: Dynamic Alpha Weighting Engine`
Status: `implemented`

## Purpose

`AES-06` adapts alpha weights after capacity and crowding have been made explicit.

It answers:

- how alpha weights should react to live evidence
- how smoothing should prevent noisy overreaction
- how turnover and capacity constraints should cap weight changes
- what MPI-ready proposal and LCC review metadata should be exposed

## Core Invariant

```text
Alpha weights must adapt to live evidence while avoiding overreaction to noise.
```

## Canonical Surfaces

- `POST /system/alpha-dynamic-weights/run`
- `GET /system/alpha-dynamic-weights/latest`
- `GET /system/alpha-dynamic-weights/ensemble/{ensemble_id}`
- `GET /system/alpha-weight-adjustments/latest`
- `GET /system/alpha-weight-drift/latest`
- `GET /system/alpha-weight-constraints/latest`
- `GET /system/alpha-weight-proposals/latest`

## Implementation Boundary

`AES-06` consumes `AES-05` capacity outputs and does not reimplement alpha generation, evaluation, validation, attribution, or portfolio allocation.

It produces:

- live evidence score
- target weight
- smoothed weight
- constrained final weight
- weight drift and adjustment reason
- MPI intent
- LCC review reason

## Storage

- `alpha_weighting_runs`
- `alpha_live_state`
- `alpha_weight_signals`
- `alpha_dynamic_weights`
- `alpha_weight_constraints`
- `alpha_weight_proposals`

## Definition Of Done

- dynamic weight run can materialize from latest capacity rows
- latest dynamic weights are operator-visible
- per-ensemble weight proposal is queryable
- weight drift and constraints are explicit
- MPI/LCC proposal metadata is explicit
- docs and contract inventories include AES-06 surfaces

