# Operational Risk & Control Intelligence Packet 03 Plan

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Operational Risk & Control Intelligence v1`
Packet: `ORC-03: Execution Anomaly & Broker Health Engine`
Status: `implemented`

## Purpose

`ORC-03` adds domain-specific execution and broker health intelligence to improve ORC trigger precision.

It answers:

- whether broker, venue, or order lifecycle health is degraded
- whether reject bursts, slippage spikes, latency spikes, cancel failures, or duplicate orders exist
- what execution-specific safe-mode recommendation should feed ORC-01/02

## Core Invariant

```text
The system must detect execution and broker failures before they create uncontrolled exposure.
```

## Canonical Surfaces

- `POST /system/execution-health/run`
- `GET /system/execution-health/latest`
- `GET /system/broker-health/latest`
- `GET /system/venue-health/latest`
- `GET /system/execution-anomalies/latest`
- `GET /system/execution-incidents/latest`
- `GET /system/execution-safe-mode-recommendation/latest`
- `GET /system/broker-health/{broker_id}`
- `GET /system/venue-health/{venue_id}`

## Implementation Boundary

`ORC-03` consumes execution telemetry and produces execution-domain health, anomalies, incidents, and safe-mode recommendations. It does not implement broker adapters, order routing, or LCC enforcement.

## Storage

- `execution_health_runs`
- `execution_health_metrics`
- `broker_health_state`
- `venue_health_state`
- `execution_anomalies`
- `execution_incidents`
- `execution_safe_mode_recommendations`

## Definition Of Done

- execution telemetry loads with fallback
- broker and venue health states are computed
- order lifecycle, slippage, latency, and cancel/replace anomalies are detected
- execution incidents are classified
- execution safe-mode recommendation is emitted
- canonical API and verifier exist

