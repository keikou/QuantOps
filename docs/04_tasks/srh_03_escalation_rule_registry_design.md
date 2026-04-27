# SRH-03 Escalation Rule Registry Design

## Purpose

The escalation rule registry maps source events to escalation level, notification routing, acknowledgement requirement, cooldown policy, and AFG-04 handoff requirement.

## Rule Fields

- `rule_id`
- `source_type`
- `source_severity_min`
- `target_escalation_level`
- `notification_channel`
- `requires_ack`
- `handoff_to_afg04`
- `cooldown_seconds`
- `dedup_key_template`
- `enabled`

## Source Types

- `RUNTIME_DEGRADATION`
- `SAFE_MODE_TRIGGERED`
- `SYSTEM_HALTED`
- `DEPENDENCY_OUTAGE`
- `CIRCUIT_OPEN_CRITICAL`
- `FALLBACK_UNAVAILABLE`
- `RECOVERY_PROBE_FAILED`

## Rule Evaluation

```text
load source event
-> match enabled rule
-> check severity threshold
-> compute dedup key
-> apply cooldown
-> create escalation / notification / handoff
```

## Invariants

- disabled rules are not evaluated
- every escalation references a `rule_id`
- CRITICAL / EMERGENCY escalations require acknowledgement
- duplicate events within cooldown do not create duplicate notifications
