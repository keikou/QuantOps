# System Reliability / Runtime Hardening Packet 01 Plan

Date: `2026-04-26`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `System Reliability / Runtime Hardening`
Packet: `SRH-01: Runtime Health & Degradation Control`

## Purpose

Observe runtime health, detect degradation, and connect the result to safe mode and recovery protocol.

## Scope

- runtime health signal ingestion
- component health score
- composite system health score
- degradation detection
- control action selection
- safe mode trigger
- recovery attempt selection

## Non-Goals

- alpha generation improvement
- policy enforcement reimplementation
- RBAC change
- postmortem or replay reimplementation
- live trading strategy change

## Canonical Surface

- `GET /system/health`
- `POST /system/runtime-health/ingest`
- `GET /system/runtime-health/latest`
- `GET /system/runtime-health/components`
- `GET /system/runtime-health/signals/latest`
- `GET /system/degradation/latest`
- `GET /system/runtime-control/actions/latest`
- `POST /system/control/safe-mode`
- `GET /system/runtime-recovery/latest`

## Runtime Tables

- `runtime_health_signals`
- `runtime_health_snapshots`
- `runtime_health_scores`
- `runtime_degradation_events`
- `runtime_control_actions`
- `runtime_recovery_attempts`

## Definition of Done

- healthy runtime state evaluates to `S0_HEALTHY`
- degraded runtime state creates degradation events
- S2/S3/S4 degradation selects throttle, safe mode, or halt action
- recovery attempt is persisted
- source health tables are persisted and queryable
- SRH does not mutate frozen AFG policy / audit / governance surfaces

