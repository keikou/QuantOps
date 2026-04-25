# Alpha Factory Governance / Operator Control Packet 03 Plan

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Factory Governance / Operator Control`
Packet: `AFG-03: RBAC / Permission Model`

## Purpose

Add role-based authorization so no operator or service actor can perform governance actions outside its permission boundary.

## Core Invariant

```text
No operator may perform a governance action outside their authorized permission boundary.
```

## Scope

- actor registry
- role registry
- permission registry
- role-permission mapping
- actor-role assignment
- action authorization
- target-scope authorization
- risk-level cap authorization
- service actor restrictions
- hard safety authorization rule
- authorization decision audit
- AFG-01 mutation authorization hook

## Canonical Surface

- `POST /system/authorization/check`
- `GET /system/authorization/latest`
- `GET /system/authorization/denials/latest`
- `GET /system/roles/latest`
- `GET /system/permissions/latest`
- `POST /system/roles/assign`
- `POST /system/roles/revoke`
- `GET /system/actor-permissions/{actor_id}`
- `GET /system/authorization/audit/latest`

## Runtime Tables

- `authorization_actors`
- `authorization_roles`
- `authorization_permissions`
- `authorization_role_permissions`
- `authorization_actor_roles`
- `authorization_decisions`
- `authorization_audit_log`

## Definition of Done

- actor, role, and permission registries exist
- default roles and permissions seed idempotently
- actor-role assignment and revoke work
- action permission, scope, and risk cap checks work
- service actor restrictions exist
- hard safety authorization rule exists
- authorization decisions are audited
- AFG-01 approve/reject/override/dispatch can call authorization
- canonical API and verifier pass

