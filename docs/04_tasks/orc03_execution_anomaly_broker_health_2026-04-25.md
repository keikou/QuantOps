# ORC-03 Execution Anomaly & Broker Health Task

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Operational Risk & Control Intelligence v1`
Packet: `ORC-03`
Status: `implemented`

## Active Boundary

Implement execution-domain anomaly detection and broker/venue health monitoring after `ORC-01` and `ORC-02`.

## Required Surfaces

- `POST /system/execution-health/run`
- `GET /system/execution-health/latest`
- `GET /system/broker-health/latest`
- `GET /system/venue-health/latest`
- `GET /system/execution-anomalies/latest`
- `GET /system/execution-incidents/latest`
- `GET /system/execution-safe-mode-recommendation/latest`
- `GET /system/broker-health/{broker_id}`
- `GET /system/venue-health/{venue_id}`

## Non-Goals

- do not implement broker API adapters
- do not replace execution routing
- do not replace LCC enforcement
- do not replay ORC-01 or ORC-02
- do not replay completed AES work

## Completion Evidence

- `execution_health` package exists
- runtime tables exist for execution health runs, metrics, broker state, venue state, anomalies, incidents, and safe-mode recommendations
- `/system/*` routes expose ORC-03 canonical surfaces
- verifier checks the plan and task surfaces

