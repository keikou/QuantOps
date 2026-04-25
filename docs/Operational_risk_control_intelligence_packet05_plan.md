# Operational Risk & Control Intelligence Packet 05 Plan

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Operational Risk & Control Intelligence`
Packet: `ORC-05: Incident Audit / Operator Governance Bridge`

## Purpose

Make ORC incidents auditable, policy-gated, and operator-controllable without requiring the full AFG lane to exist yet.

## Core Invariant

```text
Every operational risk response must be auditable, policy-gated, and operator-controllable when required.
```

## Scope

- collect ORC-01, ORC-03, and ORC-04 incidents into governance-visible records
- create AFG-compatible pending approval links for high-risk actions
- write local audit events for incident detection, recommendation, approval creation, dispatch, and recovery
- stage dispatch audit records for ORC local policy or future AFG/LCC/Execution consumers
- expose recovery governance requests

## Canonical Surface

- `POST /system/orc-governance/sync`
- `GET /system/orc-governance/latest`
- `GET /system/orc-governance/incidents/latest`
- `GET /system/orc-governance/incident/{incident_id}`
- `GET /system/orc-governance/pending-approvals/latest`
- `GET /system/orc-governance/audit/latest`
- `POST /system/orc-governance/recovery/request`
- `GET /system/orc-governance/recovery/latest`

## Runtime Tables

- `orc_governance_sync_runs`
- `orc_governance_incidents`
- `orc_governance_audit_events`
- `orc_afg_approval_links`
- `orc_response_dispatch_audit`
- `orc_recovery_governance`

## Definition of Done

- ORC incidents are governance-visible.
- L4/L5 actions create local AFG-compatible pending approval links.
- L1/L2/L3 actions are audit-visible and locally policy-applied.
- Dispatch attempts are audited.
- Recovery approval bridge exists.
- Override sync path reads active ORC overrides.
- APIs and verifier pass.
- Completed lanes are not replayed.

