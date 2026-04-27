# SRH-03 GitHub Issue Breakdown

## Runtime Tables

- `runtime_escalation_rules`
- `runtime_escalation_events`
- `runtime_escalation_dedup`
- `runtime_escalation_audit_log`
- `runtime_operator_notifications`
- `runtime_operator_notification_acks`
- `runtime_operator_notification_delivery`
- `runtime_incident_handoffs`
- `runtime_incident_handoff_attempts`

## Services

- `RuntimeEscalationService`
- escalation rule registry
- escalation rule evaluator
- operator notification queue
- notification acknowledgement service
- dedup / cooldown service
- incident handoff builder
- incident handoff retry service
- escalation audit log

## APIs

- `GET /system/escalation/rules`
- `POST /system/escalation/rules/register`
- `POST /system/escalation/evaluate/degradation/{event_id}`
- `POST /system/escalation/evaluate/dependency/{event_id}`
- `GET /system/escalations/latest`
- `GET /system/escalations/{escalation_id}`
- `GET /system/operator-notifications/latest`
- `GET /system/operator-notifications/{notification_id}`
- `POST /system/operator-notifications/{notification_id}/ack`
- `GET /system/incident-handoffs/latest`
- `GET /system/incident-handoffs/{handoff_id}`
- `POST /system/incident-handoffs/{handoff_id}/retry`
- `GET /system/escalation-audit/latest`

## Verifier

- `test_bundle/scripts/verify_runtime_escalation_packet03.py`

## Acceptance Criteria

- S3/S4 degradation creates escalation
- dependency outage creates escalation
- operator notification is created
- acknowledgement is required and tracked
- duplicate notification is suppressed
- suppressed duplicate is audit logged
- AFG-04 incident handoff is created
- failed handoff is persisted
- frozen AFG audit tables are not mutated
- SRH-01 / SRH-02 / AFG-01 through AFG-05 verifiers still pass
