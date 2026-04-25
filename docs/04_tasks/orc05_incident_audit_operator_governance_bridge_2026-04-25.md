# ORC-05 Incident Audit / Operator Governance Bridge

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Operational Risk & Control Intelligence`
Packet: `ORC-05`
Status: `implementation_ready`

## Objective

Bridge ORC incidents and response recommendations into an auditable governance staging layer for future AFG operator approval and override workflows.

## Implementation Targets

- `apps/v12-api/ai_hedge_bot/operational_governance/`
- `apps/v12-api/ai_hedge_bot/data/storage/runtime_store.py`
- `apps/v12-api/ai_hedge_bot/api/routes/system.py`
- `docs/07_interfaces/orc_operational_risk_contracts.md`
- `test_bundle/scripts/verify_operational_risk_control_intelligence_packet05.py`

## API Surface

- `POST /system/orc-governance/sync`
- `GET /system/orc-governance/latest`
- `GET /system/orc-governance/incidents/latest`
- `GET /system/orc-governance/incident/{incident_id}`
- `GET /system/orc-governance/pending-approvals/latest`
- `GET /system/orc-governance/audit/latest`
- `POST /system/orc-governance/recovery/request`
- `GET /system/orc-governance/recovery/latest`

## Non-Tasks

- implement full AFG
- implement RBAC
- implement external notifications
- replay ORC-01 through ORC-04

