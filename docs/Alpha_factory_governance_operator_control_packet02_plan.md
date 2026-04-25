# Alpha Factory Governance / Operator Control Packet 02 Plan

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Factory Governance / Operator Control`
Packet: `AFG-02: Policy Enforcement Engine`

## Purpose

Turn AFG policy, approvals, overrides, and ORC safe-mode into runtime enforcement gates before dispatch, allocation, execution, lifecycle mutation, or policy application.

## Core Invariant

```text
No action, allocation, or order may bypass governance policy enforcement.
```

## Scope

- enforcement contract
- pre-dispatch enforcement
- pre-allocation enforcement
- pre-execution enforcement
- pre-lifecycle enforcement
- pre-policy-apply enforcement
- hard safety lock
- cross-system consistency validation
- enforcement violation audit
- runtime constraint visibility

## Canonical Surface

- `POST /system/policy-enforcement/check`
- `POST /system/policy-enforcement/pre-dispatch`
- `POST /system/policy-enforcement/pre-allocation`
- `POST /system/policy-enforcement/pre-execution`
- `POST /system/policy-enforcement/pre-lifecycle`
- `POST /system/policy-enforcement/pre-policy-apply`
- `GET /system/policy-enforcement/latest`
- `GET /system/policy-enforcement/violations/latest`
- `GET /system/policy-enforcement/constraints/latest`
- `GET /system/policy-enforcement/state/latest`

## Runtime Tables

- `policy_enforcement_checks`
- `policy_enforcement_violations`
- `runtime_enforcement_constraints`
- `enforcement_consistency_state`

## Definition of Done

- enforcement checks exist
- pre-dispatch guard works
- pre-allocation guard works
- pre-execution guard works
- lifecycle guard works
- policy apply guard works
- hard safety lock exists
- cross-system consistency validator exists
- violations are audited
- canonical API and verifier pass

