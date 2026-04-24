# ORC-04 Data Integrity & Market Feed Reliability Task

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Operational Risk & Control Intelligence v1`
Packet: `ORC-04`
Status: `implemented`

## Active Boundary

Implement data integrity and market feed reliability monitoring after `ORC-03`.

## Required Surfaces

- `POST /system/data-integrity/run`
- `GET /system/data-integrity/latest`
- `GET /system/market-feed-health/latest`
- `GET /system/market-feed-health/{feed_id}`
- `GET /system/symbol-data-health/latest`
- `GET /system/symbol-data-health/{symbol}`
- `GET /system/data-anomalies/latest`
- `GET /system/data-incidents/latest`
- `GET /system/mark-reliability/latest`
- `GET /system/data-safe-mode-recommendation/latest`

## Non-Goals

- do not implement market data vendor adapters
- do not implement backfill pipeline
- do not replace alpha feature engineering
- do not replace ORC-01/02 orchestration
- do not replay completed AES work

## Completion Evidence

- `data_integrity` package exists
- runtime tables exist for feed health, symbol health, anomalies, incidents, mark reliability, and safe-mode recommendations
- `/system/*` routes expose ORC-04 canonical surfaces
- verifier checks the plan and task surfaces

