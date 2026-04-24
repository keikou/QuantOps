# AES-05 Capacity & Crowding Risk

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Evaluation / Selection Intelligence`
Packet: `AES-05`
Status: `implemented`

## Goal

Estimate how much capital each selected alpha and ensemble can absorb before liquidity, impact, turnover, or crowding makes scaling unsafe.

## Scope

`AES-05` adds:

- liquidity scoring
- market impact estimation
- crowding detection
- per-alpha capacity limits
- ensemble capacity limits
- scaling recommendations for `MPI` and `LCC`

## Canonical Outputs

1. `POST /system/alpha-capacity/run`
2. `GET /system/alpha-capacity/latest`
3. `GET /system/alpha-capacity/candidate/{alpha_id}`
4. `GET /system/alpha-crowding/latest`
5. `GET /system/alpha-impact/latest`
6. `GET /system/alpha-capacity/ensemble/{ensemble_id}`

## Supporting Drafts

- `docs/AES-05_Capacity_Crowding_Risk_Engine.md`
- `docs/AES-06_Dynamic_Alpha_Weighting_Engine.md`
- `docs/AES-07_Alpha_Kill_Switch_Retirement_Engine.md`
- `docs/AES-08_Self_Improving_Alpha_Loop.md`
