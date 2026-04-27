# SRH-03 Runtime Incident Escalation & Operator Notification Design

## Purpose

SRH-03 routes severe runtime events from SRH-01 and SRH-02 into operator-visible notification, acknowledgement, audit, and AFG-04 incident handoff workflows.

## Boundary

```text
runtime degradation / dependency outage
-> escalation rule evaluation
-> operator notification
-> acknowledgement tracking
-> AFG-04 incident handoff
-> escalation audit log
```

## Sources

- S3 / S4 runtime degradation
- safe mode trigger
- halt action
- dependency outage
- critical circuit breaker open
- fallback unavailable
- recovery probe failure

## Escalation Levels

- `INFO`
- `WARNING`
- `CRITICAL`
- `EMERGENCY`

## Invariants

- SRH-03 does not re-score health.
- SRH-03 does not reimplement circuit breaker state.
- SRH-03 creates AFG-04 incident handoff only through the allowed ingestion boundary.
- SRH-03 does not mutate frozen AFG audit / replay evidence tables.
