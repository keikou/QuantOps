# AFG-02 Policy Enforcement Engine

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Factory Governance / Operator Control`
Packet: `AFG-02`
Status: `implementation_ready`

## Objective

Implement runtime policy enforcement gates so approved, blocked, staged, safe-mode, and governance-state decisions cannot be bypassed by downstream dispatch, allocation, execution, lifecycle, or policy-apply paths.

## Implementation Targets

- `apps/v12-api/ai_hedge_bot/enforcement/`
- `apps/v12-api/ai_hedge_bot/data/storage/runtime_store.py`
- `apps/v12-api/ai_hedge_bot/api/routes/system.py`
- `docs/07_interfaces/afg_operator_control_contracts.md`
- `test_bundle/scripts/verify_alpha_factory_governance_packet02.py`

## API Surface

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

## Non-Tasks

- full RBAC
- broker-specific routing
- LCC capital model rewrite
- execution optimization
- notifications
- postmortem workflow

