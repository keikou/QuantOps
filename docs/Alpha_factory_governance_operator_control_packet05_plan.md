# Alpha Factory Governance / Operator Control Packet 05 Plan

Date: `2026-04-26`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Factory Governance / Operator Control`
Packet: `AFG-05: Governance Replay & Audit Evidence System`

## Purpose

Make governance decisions replayable and fixed as audit evidence.

## Core Invariant

```text
Replay is read-only, audit bundles are append-only, and hash mismatch must fail verification.
```

## Scope

- audit evidence bundle
- governance replay log
- decision trace
- approval trace
- feedback dispatch trace
- incident-to-action trace
- immutable snapshot export

## Non-Goals

- new policy enforcement
- RBAC reimplementation
- broad AFG-04 RCA expansion
- direct AES / ORC / LCC / Execution mutation
- live trading decision engine changes

## Canonical Surface

- `GET /system/audit/bundle/{incident_id}`
- `POST /system/audit/replay/{incident_id}`
- `GET /system/audit/replay/{replay_id}`
- `GET /system/audit/export/{incident_id}`
- `GET /system/audit/bundles/latest`
- `GET /system/audit/replays/latest`
- `GET /system/audit/exports/latest`

## Runtime Tables

- `governance_audit_bundles`
- `governance_replay_logs`
- `governance_decision_trace`
- `governance_audit_exports`

## Definition of Done

- one AFG-04 incident can produce an audit bundle
- bundle includes incident, RCA, approval, action, feedback, and dispatch evidence
- content hash and chain hash are stable and verified
- replay reconstructs decision, approval, feedback, and dispatch traces
- replay fails on hash mismatch
- replay fails when approval-gated feedback has no approval evidence
- export produces immutable JSON evidence
- replay does not mutate AFG-04 source tables

