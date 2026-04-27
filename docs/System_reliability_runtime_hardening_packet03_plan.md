# System Reliability / Runtime Hardening Packet 03 Plan

Date: `2026-04-26`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `System Reliability / Runtime Hardening`
Packet: `SRH-03: Runtime Incident Escalation & Operator Notification`

## Purpose

Connect severe runtime degradation and dependency outage events to escalation decisions, operator notifications, acknowledgement tracking, AFG-04 incident handoff, and append-only escalation audit evidence.

## Scope

- escalation rule registry
- severity-based routing
- operator notification queue
- notification lifecycle
- dedup / cooldown
- acknowledgement tracking
- AFG-04 incident handoff
- escalation audit log

## Non-Goals

- SRH-01 health scoring reimplementation
- SRH-02 circuit breaker reimplementation
- AFG-04 RCA / postmortem logic reimplementation
- direct AFG audit or replay table mutation
- policy enforcement change
- trading strategy change
- execution adapter change

## Canonical Surface

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

## Definition of Done

- S3/S4 degradation creates escalation
- dependency outage creates escalation
- escalation rule registry works
- operator notification is created
- CRITICAL / EMERGENCY notification requires acknowledgement
- acknowledgement changes notification status
- duplicate notification is suppressed within cooldown
- suppressed duplicate is audit logged
- AFG-04 incident handoff is created for critical escalation
- failed handoff is persisted
- frozen AFG audit tables are not mutated
