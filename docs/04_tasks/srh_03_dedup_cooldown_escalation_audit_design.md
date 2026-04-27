# SRH-03 Dedup Cooldown Escalation Audit Design

## Purpose

Dedup and cooldown prevent repeated runtime events from flooding operators while still recording every suppression in an audit-safe log.

## Dedup Key

```text
{source_type}:{component}:{dependency_id}:{severity}
```

## Behavior

```text
no active dedup key:
  create escalation
  create notification
  maybe create AFG-04 handoff

active dedup key within cooldown:
  suppress duplicate
  increment suppressed_count
  write audit log
```

## Audit Events

- `RULE_EVALUATED`
- `ESCALATION_CREATED`
- `NOTIFICATION_CREATED`
- `DUPLICATE_SUPPRESSED`
- `ACK_RECEIVED`
- `ACK_EXPIRED`
- `HANDOFF_CREATED`
- `HANDOFF_FAILED`
- `HANDOFF_INGESTED`

## Invariants

- suppressed duplicate is audit logged
- dedup does not mutate source event
- audit records are append-only
- severity escalation can use a distinct dedup key
