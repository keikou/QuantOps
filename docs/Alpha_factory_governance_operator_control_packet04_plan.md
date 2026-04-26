# Alpha Factory Governance / Operator Control Packet 04 Plan

Date: `2026-04-26`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Factory Governance / Operator Control`
Packet: `AFG-04: Incident Review & Postmortem System`

## Purpose

Turn critical incidents into structured, auditable system learning.

## Core Invariant

```text
Every critical incident must produce structured learning that feeds back into the system.
```

## Scope

- incident ingestion
- severity classification
- review lifecycle
- RCA capture and approval
- action item tracking
- typed postmortem feedback
- approval-gated feedback dispatch to ORC, AES, AFG policy, LCC, and Execution

## Canonical Surface

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

## Runtime Tables

- `postmortem_incidents`
- `postmortem_reviews`
- `postmortem_rca`
- `postmortem_action_items`
- `postmortem_feedback`
- `postmortem_feedback_dispatch`

## Definition of Done

- incidents are stored with severity and lifecycle state
- review, RCA, action, close, and postmortem surfaces exist
- approved RCA can generate typed feedback
- high-severity incidents require approved RCA before close
- feedback adapters exist for `AES`, `ORC`, `AFG_POLICY`, `LCC`, and `EXECUTION`
- medium/high/critical feedback is approval-gated
- feedback dispatch is idempotent and auditable
- AFG-04 never directly mutates live policy code
- canonical API and verifier pass

