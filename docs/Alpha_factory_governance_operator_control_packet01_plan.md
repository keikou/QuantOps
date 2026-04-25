# Alpha Factory Governance / Operator Control Packet 01 Plan

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Factory Governance / Operator Control`
Packet: `AFG-01: Alpha Factory Operator Control Plane`

## Purpose

Create the operator control plane that governs production-impacting alpha factory actions through policy, approval, override, audit, and dispatch staging.

## Core Invariant

```text
No production-impacting decision should be applied without explicit policy, auditability, and, when required, operator approval.
```

## Scope

- operator action registry
- pending approval queue
- policy gate
- time-limited operator overrides
- governance audit log
- governance state view
- ORC governance staging sync
- dispatch staging / dry-run
- operator-facing API

## Canonical Surface

- `POST /system/operator-action/submit`
- `GET /system/operator-actions/latest`
- `GET /system/pending-approvals/latest`
- `GET /system/pending-approvals/{approval_id}`
- `POST /system/pending-approvals/{approval_id}/approve`
- `POST /system/pending-approvals/{approval_id}/reject`
- `POST /system/operator-override`
- `GET /system/operator-overrides/latest`
- `POST /system/operator-overrides/{override_id}/expire`
- `GET /system/audit-log/latest`
- `GET /system/governance-state/latest`
- `POST /system/governance/sync`
- `POST /system/governance/dispatch`
- `GET /system/governance/dispatch/latest`

## Runtime Tables

- `operator_actions`
- `pending_approvals`
- `governance_audit_log`
- `operator_overrides`
- `governance_state`
- `governance_dispatch_log`

## Definition of Done

- approval queue exists
- operator actions are persisted
- policy gate returns `AUTO_RECORD`, `AUTO_APPLY`, `REQUIRE_APPROVAL`, or `BLOCK`
- overrides require reason/operator/expiry and are audited
- governance state is visible
- ORC recommendations can enter governance
- approved actions can dispatch or stage
- canonical API and verifier pass

