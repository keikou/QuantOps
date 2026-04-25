# AFG-03 RBAC / Permission Model

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Factory Governance / Operator Control`
Packet: `AFG-03`
Status: `implementation_ready`

## Objective

Implement authorization for AFG governance mutations so only actors with the correct role, scope, and risk boundary can approve, reject, override, dispatch, or manage roles.

## Implementation Targets

- `apps/v12-api/ai_hedge_bot/authorization/`
- `apps/v12-api/ai_hedge_bot/governance/governance_service.py`
- `apps/v12-api/ai_hedge_bot/data/storage/runtime_store.py`
- `apps/v12-api/ai_hedge_bot/api/routes/system.py`
- `docs/07_interfaces/afg_operator_control_contracts.md`
- `test_bundle/scripts/verify_alpha_factory_governance_packet03.py`

## API Surface

- `POST /system/authorization/check`
- `GET /system/authorization/latest`
- `GET /system/authorization/denials/latest`
- `GET /system/roles/latest`
- `GET /system/permissions/latest`
- `POST /system/roles/assign`
- `POST /system/roles/revoke`
- `GET /system/actor-permissions/{actor_id}`
- `GET /system/authorization/audit/latest`

## Non-Tasks

- external identity provider
- password / MFA / SSO
- two-person approval
- notifications
- postmortem workflow

