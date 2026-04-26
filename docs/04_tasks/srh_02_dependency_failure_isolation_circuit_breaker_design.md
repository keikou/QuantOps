# SRH-02 Dependency Failure Isolation & Circuit Breaker Design

## Purpose

SRH-02 adds dependency failure isolation after SRH-01 runtime health detection. It detects a dependency failure, opens the circuit breaker, selects fallback or isolation, and validates recovery through probes.

## Scope

- dependency registry
- dependency health state
- failure detector
- circuit breaker state machine
- fallback route selector
- dependency isolation event
- recovery probe

## Dependency Types

- `DATA_FEED`
- `EXECUTION_VENUE`
- `BROKER_ADAPTER`
- `MODEL_SERVICE`
- `STORAGE`
- `QUEUE`
- `SCHEDULER`
- `INTERNAL_API`
- `EXTERNAL_API`

## Boundary

```text
dependency failure
-> failure observation
-> circuit transition
-> fallback or isolation
-> recovery probe
-> half-open
-> closed
```

## Non-Goals

- do not reimplement SRH-01 health scoring
- do not mutate AFG audit or governance
- do not change ORC risk rules
- do not change AES alpha logic
- do not rewrite broker adapters
- do not touch the live trading decision engine

## Checkpoint Complete

One dependency failure can be detected, circuit opened, fallback or isolation selected, recovery probe scheduled, and successful probe returned to `CLOSED`.
