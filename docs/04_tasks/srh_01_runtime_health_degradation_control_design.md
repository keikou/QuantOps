# SRH-01 Runtime Health & Degradation Control

## Purpose

SRH-01 monitors runtime health, detects degradation, and connects the system to safe control and recovery behavior.

## Scope

```text
- runtime health observation
- degradation detection
- safe mode trigger
- recovery protocol selection
```

## Non-Goals

```text
- alpha improvement
- governance change
- policy enforcement reimplementation
- RBAC change
- trading logic change
```

## Runtime Health Definition

```text
Runtime health is a quantitative view of whether the system is operating within expected latency, freshness, error, queue, execution, dependency, and heartbeat bounds.
```

## Degradation Classification

```text
S0_HEALTHY: normal
S1_MINOR_DEGRADATION: minor degradation
S2_MODERATE_DEGRADATION: moderate degradation
S3_MAJOR_DEGRADATION_SAFE_MODE: major degradation requiring safe mode
S4_CRITICAL_HALT: critical failure requiring halt posture
```

## Safe Mode

```text
- execution restriction
- capital reduction
- operator-visible degradation event
- recovery attempt creation
```

## Recovery Protocol

```text
- observe only
- retry and throttle
- safe mode then recover
- halt and operator escalation
```

## Checkpoint Complete Conditions

```text
- degradation can be detected
- safe mode can be triggered
- recovery action can be persisted
- state transition logs are queryable
```

