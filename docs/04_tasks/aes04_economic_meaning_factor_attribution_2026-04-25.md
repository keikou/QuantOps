# AES-04 Economic Meaning / Factor Attribution

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Evaluation / Selection Intelligence`
Packet: `AES-04`
Status: `implemented`

## Goal

Explain why `AES-03` selected alpha and ensembles work by making factor exposure, residual alpha, regime dependency, and concentration risk explicit before production scaling.

## Scope

`AES-04` should add:

- factor exposure estimation
- residual alpha scoring
- regime dependency profiling
- hidden common driver detection
- ensemble factor concentration
- economic meaning labels
- production scaling recommendation

## Canonical Outputs

1. `POST /system/alpha-factor-attribution/run`
2. `GET /system/alpha-factor-attribution/latest`
3. `GET /system/alpha-factor-attribution/candidate/{alpha_id}`
4. `GET /system/alpha-factor-exposure/latest`
5. `GET /system/alpha-residual-alpha/latest`
6. `GET /system/alpha-economic-risk/latest`
7. `GET /system/alpha-factor-concentration/latest`
8. `GET /system/alpha-economic-meaning/latest`
9. `GET /system/alpha-factor-attribution/ensemble/{ensemble_id}`

## Supporting Drafts

- `docs/AES-04_Economic_Meaning_Factor_Attribution_Design.md`
- `docs/AES-05_Capacity_Crowding_Risk_Engine.md`
- `docs/AES-06_Dynamic_Alpha_Weighting_Engine.md`
- `docs/AES-07_Alpha_Kill_Switch_Retirement_Engine.md`
- `docs/AES-08_Self_Improving_Alpha_Loop.md`
