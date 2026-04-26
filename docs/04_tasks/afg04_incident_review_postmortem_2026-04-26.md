# AFG-04 Incident Review & Postmortem System

Date: `2026-04-26`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Factory Governance / Operator Control`
Packet: `AFG-04`
Status: `implementation_ready`

## Objective

Implement incident review and postmortem learning so critical incidents produce RCA, tracked actions, and approval-gated feedback into ORC, AES, AFG policy, LCC, and Execution.

## Implementation Targets

- `apps/v12-api/ai_hedge_bot/postmortem_feedback/`
- `apps/v12-api/ai_hedge_bot/data/storage/runtime_store.py`
- `apps/v12-api/ai_hedge_bot/api/routes/system.py`
- `docs/07_interfaces/afg_operator_control_contracts.md`
- `test_bundle/scripts/verify_alpha_factory_governance_packet04.py`

## API Surface

- `POST /system/incidents/ingest`
- `GET /system/incidents/latest`
- `POST /system/incidents/{id}/review`
- `POST /system/incidents/{id}/rca`
- `POST /system/incidents/{id}/actions`
- `POST /system/incidents/{id}/close`
- `GET /system/postmortem/latest`
- `POST /system/postmortem-feedback/build/{incident_id}`
- `POST /system/postmortem-feedback/dispatch/{feedback_id}`
- `GET /system/postmortem-feedback/latest`
- `GET /system/postmortem-feedback/target/{target_system}`
- `GET /system/postmortem-feedback/dispatch/latest`

## Required Runtime Behavior

- S1/S2 incidents cannot close without approved RCA
- approved RCA can generate typed postmortem feedback
- feedback targets include `AES`, `ORC`, `AFG_POLICY`, `LCC`, and `EXECUTION`
- approval-required feedback creates AFG pending approvals
- dispatch is idempotent through feedback dispatch keys
- live policy code is not mutated directly

## Non-Tasks

- external ticketing integration
- automatic live threshold mutation
- human notification delivery
- reopening AFG-01, AFG-02, or AFG-03 unless a regression is found

