# AFG-01 Alpha Factory Operator Control Plane

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Factory Governance / Operator Control`
Packet: `AFG-01`
Status: `implementation_ready`

## Objective

Implement the first AFG operator control plane for production-impacting actions across ORC, AES, AAE, LCC, Execution, and operator workflows.

## Implementation Targets

- `apps/v12-api/ai_hedge_bot/governance/policy_gate_engine.py`
- `apps/v12-api/ai_hedge_bot/governance/governance_service.py`
- `apps/v12-api/ai_hedge_bot/data/storage/runtime_store.py`
- `apps/v12-api/ai_hedge_bot/api/routes/system.py`
- `docs/07_interfaces/afg_operator_control_contracts.md`
- `test_bundle/scripts/verify_alpha_factory_governance_packet01.py`

## API Surface

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

## Non-Tasks

- full RBAC
- external notifications
- downstream broker enforcement
- LCC capital model rewrite
- AES scoring rewrite
- replaying ORC v1

