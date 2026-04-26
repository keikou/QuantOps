# Alpha Factory Governance / Operator Control Contracts

Date: `2026-04-26`
Repo: `QuantOps_github`
Status: `afg04_contracts`

## Contract Intent

```text
No production-impacting decision should be applied without explicit policy, auditability, and, when required, operator approval.
```

## AFG-01 Surfaces

1. `POST /system/operator-action/submit`
2. `GET /system/operator-actions/latest`
3. `GET /system/pending-approvals/latest`
4. `GET /system/pending-approvals/{approval_id}`
5. `POST /system/pending-approvals/{approval_id}/approve`
6. `POST /system/pending-approvals/{approval_id}/reject`
7. `POST /system/operator-override`
8. `GET /system/operator-overrides/latest`
9. `POST /system/operator-overrides/{override_id}/expire`
10. `GET /system/audit-log/latest`
11. `GET /system/governance-state/latest`
12. `POST /system/governance/sync`
13. `POST /system/governance/dispatch`
14. `GET /system/governance/dispatch/latest`

## AFG-01 Contract Progression

- operator action registry
- policy gate decision
- pending approval queue
- approve / reject decision
- time-limited operator override
- audit log
- governance state
- ORC staging sync
- dispatch staging and dry-run

## AFG-02 Surfaces

1. `POST /system/policy-enforcement/check`
2. `POST /system/policy-enforcement/pre-dispatch`
3. `POST /system/policy-enforcement/pre-allocation`
4. `POST /system/policy-enforcement/pre-execution`
5. `POST /system/policy-enforcement/pre-lifecycle`
6. `POST /system/policy-enforcement/pre-policy-apply`
7. `GET /system/policy-enforcement/latest`
8. `GET /system/policy-enforcement/violations/latest`
9. `GET /system/policy-enforcement/constraints/latest`
10. `GET /system/policy-enforcement/state/latest`

## AFG-02 Contract Progression

- generic enforcement check
- pre-dispatch guard
- pre-allocation guard
- pre-execution guard
- lifecycle mutation guard
- policy apply guard
- hard safety lock
- cross-system consistency state
- enforcement violation audit
- runtime enforcement constraints

## AFG-03 Surfaces

1. `POST /system/authorization/check`
2. `GET /system/authorization/latest`
3. `GET /system/authorization/denials/latest`
4. `GET /system/roles/latest`
5. `GET /system/permissions/latest`
6. `POST /system/roles/assign`
7. `POST /system/roles/revoke`
8. `GET /system/actor-permissions/{actor_id}`
9. `GET /system/authorization/audit/latest`

## AFG-03 Contract Progression

- actor registry
- role registry
- permission registry
- role-permission mapping
- actor-role assignment
- action authorization
- target-scope authorization
- risk-level cap authorization
- service actor restrictions
- hard safety authorization
- authorization decision audit
- AFG-01 mutation authorization hook

## AFG-04 Surfaces

1. `POST /system/incidents/ingest`
2. `GET /system/incidents/latest`
3. `POST /system/incidents/{id}/review`
4. `POST /system/incidents/{id}/rca`
5. `POST /system/incidents/{id}/actions`
6. `POST /system/incidents/{id}/close`
7. `GET /system/postmortem/latest`
8. `POST /system/postmortem-feedback/build/{incident_id}`
9. `POST /system/postmortem-feedback/dispatch/{feedback_id}`
10. `GET /system/postmortem-feedback/latest`
11. `GET /system/postmortem-feedback/target/{target_system}`
12. `GET /system/postmortem-feedback/dispatch/latest`

## AFG-04 Contract Progression

- incident ingestion
- severity classification
- review lifecycle
- approved RCA
- action item tracking
- typed postmortem feedback
- feedback adapters for `AES`, `ORC`, `AFG_POLICY`, `LCC`, and `EXECUTION`
- approval-gated feedback dispatch
- idempotent dispatch audit
- no direct live policy mutation
