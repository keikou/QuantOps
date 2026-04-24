# Operational Risk & Control Intelligence Packet 01 Plan

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Operational Risk & Control Intelligence v1`
Packet: `ORC-01: Operational Risk Control Plane`
Status: `implemented`

## Purpose

`ORC-01` adds a system-level survival layer after `AES v1` checkpoint completion.

It answers:

- whether data, execution, portfolio, alpha-system, or infrastructure telemetry is unsafe
- which anomalies and incidents should become operator-visible
- what risk level and response recommendation should be emitted
- how a global kill-switch event and override record should be audited

## Core Invariant

```text
The system must detect and respond to system-level risk before capital is irreversibly damaged.
```

## Canonical Surfaces

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

## Implementation Boundary

`ORC-01` consumes system telemetry and prior lane outputs. It does not replay `AES`, `LCC`, `MPI`, execution, or alpha factory logic.

It produces:

- operational risk metrics
- statistical anomaly records
- domain incidents
- global risk state
- risk response recommendation
- global kill-switch event
- operational risk override

## Risk Levels

- `L0_NORMAL`
- `L1_WATCH`
- `L2_REDUCE`
- `L3_FREEZE`
- `L4_PARTIAL_HALT`
- `L5_GLOBAL_HALT`

## Storage

- `operational_risk_runs`
- `operational_risk_metrics`
- `operational_anomalies`
- `operational_incidents`
- `operational_risk_state`
- `risk_response_actions`
- `global_kill_switch_events`
- `operational_risk_overrides`

## Definition Of Done

- telemetry ingestion works with conservative fallback
- risk metrics are computed
- anomalies are detected
- incidents are classified
- global risk state is produced
- risk response is recommended
- global kill-switch and override surfaces exist
- docs and contract inventories include ORC-01 surfaces

