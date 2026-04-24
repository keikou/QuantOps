# AES-07 Alpha Kill Switch / Retirement Engine

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Evaluation / Selection Intelligence v1`
Packet: `AES-07`
Status: `draft`

## Purpose

`AES-07` defines the alpha-level stop, freeze, retire, and archive layer after `AES-06`.

It answers:

- when live alpha deterioration should trigger reduce, freeze, or retire actions
- how lifecycle updates should flow back into `AAE`
- how `AES-06`, `MPI`, and `LCC` should consume alpha deactivation state

## Core Invariant

```text
The system must stop or retire deteriorating alpha before it causes persistent portfolio damage.
```

## Canonical Surfaces

1. `POST /system/alpha-kill-switch/run`
2. `GET /system/alpha-kill-switch/latest`
3. `GET /system/alpha-kill-switch/alpha/{alpha_id}`
4. `GET /system/alpha-retirement/latest`
5. `GET /system/alpha-retirement/alpha/{alpha_id}`
6. `GET /system/alpha-deactivation-decisions/latest`
7. `GET /system/alpha-kill-switch-events/latest`
8. `POST /system/alpha-kill-switch/override`

## Main Outputs

- kill switch decision
- retirement decision
- lifecycle update payload
- MPI/LCC notification payload
- operator override record

## Data Model Draft

- `alpha_retirement_runs`
- `alpha_live_health`
- `alpha_kill_switch_events`
- `alpha_retirement_decisions`
- `alpha_lifecycle_updates`
- `alpha_kill_switch_overrides`

## Next Packet

`AES-08: Self-Improving Alpha Loop`
