# AES-07 Alpha Kill Switch / Retirement Task

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Evaluation / Selection Intelligence v1`
Packet: `AES-07`
Status: `implemented`

## Active Boundary

Implement alpha-level stop, freeze, reduce, retire, lifecycle update, and operator override visibility after `AES-06`.

## Required Surfaces

- `POST /system/alpha-kill-switch/run`
- `GET /system/alpha-kill-switch/latest`
- `GET /system/alpha-kill-switch/alpha/{alpha_id}`
- `GET /system/alpha-retirement/latest`
- `GET /system/alpha-retirement/alpha/{alpha_id}`
- `GET /system/alpha-deactivation-decisions/latest`
- `GET /system/alpha-kill-switch-events/latest`
- `POST /system/alpha-kill-switch/override`

## Non-Goals

- do not regenerate alpha
- do not rerun AES-01 evaluation
- do not replace AES-06 dynamic weighting
- do not implement execution order cancellation
- do not replay completed AES-01 through AES-06 packets

## Completion Evidence

- `alpha_retirement` package exists
- runtime tables exist for retirement runs, live health, events, decisions, lifecycle updates, and overrides
- `/system/*` routes expose kill switch, retirement, deactivation, event, and override surfaces
- verifier checks the plan and task surfaces

