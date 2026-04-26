# AFG-05 GitHub Issue Breakdown

## Runtime Tables

```text
governance_audit_bundles
governance_replay_logs
governance_decision_trace
governance_audit_exports
```

## Services

```text
governance_audit.models
governance_audit.audit_bundle_builder
governance_audit.hash_verifier
governance_audit.trace_builder
governance_audit.replay_engine
governance_audit.export_service
governance_audit.audit_service
```

## APIs

```text
GET /system/audit/bundle/{incident_id}
POST /system/audit/replay/{incident_id}
GET /system/audit/replay/{replay_id}
GET /system/audit/export/{incident_id}
GET /system/audit/bundles/latest
GET /system/audit/replays/latest
GET /system/audit/exports/latest
```

## Verifier

```text
test_bundle/scripts/verify_alpha_factory_governance_packet05.py
```

## Acceptance Criteria

```text
- audit bundle can be built
- replay succeeds for complete evidence
- trace rows include decision / approval / feedback / dispatch
- hash tampering fails replay verification
- missing approval fails replay verification
- replay is read-only against AFG-04 source tables
```

## Non-Goals

```text
- policy changes
- trading logic changes
- RBAC rebuild
- AFG-04 RCA expansion
```

