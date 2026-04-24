# Operational Risk & Control Intelligence Packet 04 Plan

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Operational Risk & Control Intelligence v1`
Packet: `ORC-04: Data Integrity & Market Feed Reliability Engine`
Status: `implemented`

## Purpose

`ORC-04` adds domain-specific data integrity and market feed reliability monitoring.

It answers:

- whether market feed freshness, missing data, bad ticks, OHLCV integrity, and mark reliability are safe
- which symbols or feeds should be halted or frozen
- what data-specific safe-mode recommendation should feed ORC-01/02

## Core Invariant

```text
The system must not trade on stale, missing, corrupted, or inconsistent market data.
```

## Canonical Surfaces

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

## Implementation Boundary

`ORC-04` consumes configured symbols and market-data health inputs. It does not implement market data vendor adapters, feature engineering, alpha generation, or historical data backfill.

## Storage

- `data_integrity_runs`
- `market_feed_health`
- `symbol_data_health`
- `data_anomalies`
- `data_incidents`
- `mark_reliability_state`
- `data_safe_mode_recommendations`

## Definition Of Done

- feed freshness is monitored
- missing data and bad ticks are detected
- OHLCV and mark reliability are checked
- data incidents are classified
- data safe-mode recommendation is emitted
- canonical API and verifier exist

