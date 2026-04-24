# ORC-01 Operational Risk Control Plane Task

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Operational Risk & Control Intelligence v1`
Packet: `ORC-01`
Status: `implemented`

## Active Boundary

Implement system-level operational risk detection, risk state, response recommendation, global kill-switch event recording, and override auditing.

## Required Surfaces

- `POST /system/operational-risk/run`
- `GET /system/risk-state/latest`
- `GET /system/global-risk-metrics/latest`
- `GET /system/anomaly-detection/latest`
- `GET /system/operational-incidents/latest`
- `GET /system/risk-response/latest`
- `POST /system/risk-response/execute`
- `POST /system/global-kill-switch`
- `GET /system/global-kill-switch/latest`
- `POST /system/operational-risk/override`

## Non-Goals

- do not replay completed AES v1
- do not replace LCC enforcement
- do not replace execution order validation
- do not implement AFG approval workflow
- do not silently auto-apply global halt policy beyond recording and recommendation

## Completion Evidence

- `operational_risk` package exists
- runtime tables exist for ORC-01 run, metrics, anomalies, incidents, state, response, kill-switch, and overrides
- `/system/*` routes expose ORC-01 canonical surfaces
- verifier checks plan and task surfaces

