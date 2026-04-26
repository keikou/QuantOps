# SRH-01 GitHub Issue Breakdown

## Runtime Tables

```text
runtime_health_signals
runtime_health_snapshots
runtime_health_scores
runtime_degradation_events
runtime_control_actions
runtime_recovery_attempts
```

## Services

```text
runtime_health.models
runtime_health.health_collector
runtime_health.health_evaluator
runtime_health.degradation_detector
runtime_health.control_engine
runtime_health.recovery_manager
runtime_health.service
```

## APIs

```text
POST /system/runtime-health/ingest
GET /system/runtime-health/latest
GET /system/runtime-health/components
GET /system/runtime-health/signals/latest
GET /system/degradation/latest
GET /system/runtime-control/actions/latest
POST /system/control/safe-mode
GET /system/runtime-recovery/latest
```

## Verifier

```text
test_bundle/scripts/verify_runtime_health_packet01.py
```

## Acceptance Criteria

```text
- healthy state returns S0
- degraded state creates degradation events
- S2/S3/S4 creates throttle / safe mode / halt action
- recovery attempt is persisted
- SRH does not mutate frozen AFG tables
```

## Non-Goals

```text
- governance changes
- alpha improvements
- trading logic changes
```

