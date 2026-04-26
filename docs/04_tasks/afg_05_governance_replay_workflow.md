# AFG-05 Governance Replay Workflow

## Purpose

Replay historical governance decisions without mutating live systems.

## Input

```text
incident_id
or
bundle_id
```

## Replay Flow

```text
1. load latest audit bundle for incident
2. verify content_hash
3. verify chain_hash
4. load incident evidence
5. rebuild RCA and action trace
6. rebuild approval trace
7. rebuild feedback trace
8. rebuild dispatch trace
9. persist replay log
10. persist decision trace rows
```

## Output

```text
- replay status
- validation errors
- decision trace
- approval trace
- feedback trace
- dispatch trace
- system impact summary
```

## Verification

```text
- replay result matches original evidence bundle
- dispatch trace matches original dispatch evidence
- approval trace exists for approval-gated feedback
- AFG-04 source table counts do not change during replay
```

## Failure Modes

```text
- missing incident evidence
- missing RCA evidence
- missing approval evidence
- content hash mismatch
- chain hash mismatch
```

