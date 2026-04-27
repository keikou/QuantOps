# SRH-03 AFG-04 Incident Handoff Design

## Purpose

AFG-04 incident handoff maps severe SRH escalation into a postmortem incident candidate without reimplementing RCA, action tracking, or feedback generation.

## Boundary

```text
SRH escalation
-> incident handoff candidate
-> AFG-04 incident ingestion
-> AFG-04 review / RCA / action / feedback lifecycle
```

## Handoff Status

- `PENDING_INGEST`
- `INGESTED`
- `FAILED`
- `DUPLICATE_SUPPRESSED`

## Incident Type Mapping

- `RUNTIME_DEGRADATION`
- `RUNTIME_SAFE_MODE`
- `RUNTIME_HALT`
- `RUNTIME_DEPENDENCY_OUTAGE`
- `RUNTIME_FALLBACK_FAILURE`
- `RUNTIME_RECOVERY_FAILURE`

## Invariants

- one escalation creates at most one handoff within the dedup window
- SRH-03 does not write RCA directly
- SRH-03 does not emit AFG-04 feedback directly
- failed handoff is persisted and retryable
