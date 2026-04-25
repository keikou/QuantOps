# Alpha Factory Governance / Operator Control Contracts

Date: `2026-04-25`
Repo: `QuantOps_github`
Status: `afg01_contracts`

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

