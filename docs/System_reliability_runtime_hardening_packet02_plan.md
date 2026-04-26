# System Reliability / Runtime Hardening Packet 02 Plan

Date: `2026-04-26`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `System Reliability / Runtime Hardening`
Packet: `SRH-02: Dependency Failure Isolation & Circuit Breaker System`

## Purpose

Detect internal and external dependency failure, isolate blast radius, and route through circuit breaker, fallback, degraded routing, and recovery probe controls.

## Scope

- dependency registry
- dependency health observations
- failure detection
- circuit breaker state transitions
- fallback route selection
- isolation events
- recovery probe lifecycle
- SRH-01 health and degradation integration boundary

## Non-Goals

- SRH-01 health scoring reimplementation
- AFG audit or governance mutation
- ORC risk rule change
- AES alpha logic change
- execution strategy change
- broker adapter rewrite
- live trading decision engine change

## Canonical Surface

- `GET /system/dependencies`
- `GET /system/dependencies/{dependency_id}`
- `POST /system/dependencies/register`
- `GET /system/dependencies/health/latest`
- `POST /system/dependencies/{dependency_id}/record-success`
- `POST /system/dependencies/{dependency_id}/record-failure`
- `GET /system/circuit-breakers/latest`
- `GET /system/circuit-breakers/{dependency_id}`
- `POST /system/circuit-breakers/{dependency_id}/open`
- `POST /system/circuit-breakers/{dependency_id}/half-open`
- `POST /system/circuit-breakers/{dependency_id}/close`
- `GET /system/dependency-isolation/latest`
- `GET /system/fallback-routes/latest`
- `POST /system/recovery-probes/{dependency_id}/schedule`
- `POST /system/recovery-probes/{probe_id}/complete`
- `GET /system/recovery-probes/latest`

## Runtime Tables

- `runtime_dependency_registry`
- `runtime_dependency_health`
- `runtime_dependency_events`
- `runtime_circuit_breakers`
- `runtime_circuit_transitions`
- `runtime_fallback_routes`
- `runtime_recovery_probes`

## Definition of Done

- one dependency can be registered
- success observation keeps the circuit `CLOSED`
- repeated failure opens the circuit
- open circuit selects fallback when configured
- open circuit creates isolation event when no fallback exists
- recovery probe can move `OPEN` to `HALF_OPEN` and then `CLOSED`
- failed probe reopens the circuit
- illegal transition is blocked and persisted
- SRH-02 does not mutate frozen AFG audit tables
