# SRH-02 GitHub Issue Breakdown

## Runtime Tables

- `runtime_dependency_registry`
- `runtime_dependency_health`
- `runtime_dependency_events`
- `runtime_circuit_breakers`
- `runtime_circuit_transitions`
- `runtime_fallback_routes`
- `runtime_recovery_probes`

## Services

- `RuntimeDependencyService`
- dependency registry
- failure detector
- circuit breaker state machine
- fallback route selector
- recovery probe lifecycle

## APIs

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

## Verifier

- `test_bundle/scripts/verify_runtime_dependency_packet02.py`

## Acceptance Criteria

- dependency registration works
- repeated failure opens circuit
- fallback route is selected when configured
- isolation event is created when no fallback exists
- recovery probe can close the circuit
- failed recovery probe reopens the circuit
- illegal transition is blocked
- frozen AFG audit tables are not mutated

## Non-Goals

- SRH-01 health scoring rewrite
- AFG governance mutation
- ORC risk rule change
- AES alpha logic change
- execution strategy change
