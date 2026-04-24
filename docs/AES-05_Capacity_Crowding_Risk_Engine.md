# AES-05 Capacity & Crowding Risk Engine

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Evaluation / Selection Intelligence v1`
Packet: `AES-05`
Status: `draft`

## Purpose

`AES-05` defines the capacity and crowding control layer after `AES-04`.

It answers:

- how much capital each selected alpha can absorb
- whether impact, liquidity, turnover, or crowding should cap scaling
- what ensemble-level capacity limit should be passed to `MPI` and `LCC`

## Core Invariant

```text
Capital allocation must respect liquidity, impact, and crowding constraints before scaling alpha.
```

## Canonical Surfaces

1. `POST /system/alpha-capacity/run`
2. `GET /system/alpha-capacity/latest`
3. `GET /system/alpha-capacity/candidate/{alpha_id}`
4. `GET /system/alpha-crowding/latest`
5. `GET /system/alpha-impact/latest`
6. `GET /system/alpha-capacity/ensemble/{ensemble_id}`

## Main Outputs

- per-alpha capacity limit
- ensemble capacity limit
- impact-adjusted return view
- crowding score
- liquidity risk score
- scaling recommendation

## Data Model Draft

- `alpha_capacity`
- `ensemble_capacity`

## Integrations

- consumes `AES-03` weights and `AES-04` factor concentration
- emits capital caps for `MPI` and hard guardrail metadata for `LCC`

## Next Packet

`AES-06: Dynamic Alpha Weighting Engine`
