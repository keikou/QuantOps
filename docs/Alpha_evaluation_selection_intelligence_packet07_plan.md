# Alpha Evaluation / Selection Intelligence Packet 07 Plan

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Evaluation / Selection Intelligence v1`
Packet: `AES-07: Alpha Kill Switch / Retirement Engine`
Status: `implemented`

## Purpose

`AES-07` stops, freezes, reduces, or retires deteriorating alpha after dynamic weighting has surfaced live evidence.

It answers:

- when alpha deterioration should trigger a kill-switch action
- how retirement decisions should become operator-visible
- how lifecycle updates should flow back into `AAE`
- how `MPI` and `LCC` should consume deactivation state

## Core Invariant

```text
The system must stop or retire deteriorating alpha before it causes persistent portfolio damage.
```

## Canonical Surfaces

- `POST /system/alpha-kill-switch/run`
- `GET /system/alpha-kill-switch/latest`
- `GET /system/alpha-kill-switch/alpha/{alpha_id}`
- `GET /system/alpha-retirement/latest`
- `GET /system/alpha-retirement/alpha/{alpha_id}`
- `GET /system/alpha-deactivation-decisions/latest`
- `GET /system/alpha-kill-switch-events/latest`
- `POST /system/alpha-kill-switch/override`

## Implementation Boundary

`AES-07` consumes `AES-06` dynamic weights and live state. It does not evaluate alpha quality, compute portfolio allocations, or execute orders.

It produces:

- live health score
- kill-switch action
- retirement decision
- lifecycle update payload for `AAE`
- MPI/LCC notification metadata
- operator override record

## Storage

- `alpha_retirement_runs`
- `alpha_live_health`
- `alpha_kill_switch_events`
- `alpha_retirement_decisions`
- `alpha_lifecycle_updates`
- `alpha_kill_switch_overrides`

## Definition Of Done

- kill-switch run materializes from latest dynamic weights
- alpha health is operator-visible
- per-alpha kill-switch and retirement lookups are queryable
- deactivation decisions and events are explicit
- manual override is recorded
- docs and contract inventories include AES-07 surfaces

