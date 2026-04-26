# SRH-01 Runtime Health Model Design

## Purpose

Convert runtime signals into component and system health scores for control decisions.

## Health Signals

```text
- latency_ms
- error_rate
- data_freshness_sec
- queue_lag
- execution_failure_rate
- heartbeat_age_sec
```

## Component Health

```text
EXECUTION
DATA_FEED
ALPHA
RISK
INFRA
GOVERNANCE
```

## Health Score

```text
component_health_score = weighted normalized signal score
system_health_score = minimum component score
```

## Thresholds

```text
>= 0.90: S0_HEALTHY
>= 0.70: S1_MINOR_DEGRADATION
>= 0.50: S2_MODERATE_DEGRADATION
>= 0.30: S3_MAJOR_DEGRADATION_SAFE_MODE
< 0.30: S4_CRITICAL_HALT
```

## Dependency Health

```text
Dependency health is represented through component-scoped signals such as heartbeat age, queue lag, data freshness, and error rate.
```

## Output

```text
- component health scores
- system health snapshot
- severity level
```

