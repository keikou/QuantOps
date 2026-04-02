# Audit Governance Mirroring Plan

Date: `2026-04-01`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `System Reliability Hardening Track`
Status: `in_progress`

## Purpose

This packet extends:

- `docs/Audit_provenance_mirroring_plan.md`

The registration side is already mirrored into `audit_logs`.
The next step is to mirror governance decisions so one unified audit surface can cover:

```text
registration -> governance evaluation -> governance decision
```

## First Governance Mirroring Invariant

```text
promotion / live-review / alpha-decay / rollback / champion-challenger
-> writes canonical governance records
-> also writes one unified audit_logs mirror entry
with actor attribution and key decision identifiers
```

## Scope

This packet should cover:

- `/research-factory/promotion/evaluate`
- `/research-factory/live-review`
- `/research-factory/alpha-decay`
- `/research-factory/rollback/evaluate`
- `/research-factory/champion-challenger/run`

## Mirrored Audit Shape

Each mirror record should keep:

- explicit `event_type`
- `actor`
- decision id or run id
- model id and alpha id when applicable
- the decision or severity field
- creation timestamp

The mirror is intentionally concise.
It is for operator-facing audit continuity, not full payload duplication.

## Verification Artifact

- `test_bundle/scripts/verify_research_governance_audit_mirroring.py`

The verifier should:

- prepare a candidate model lineage
- execute promotion
- execute live review
- execute alpha decay
- execute rollback
- execute champion-challenger
- confirm canonical governance rows exist
- confirm one matching audit row exists for each governance decision

## Why This Packet Matters

With this packet, the unified audit stream can cover both:

- research registration surfaces
- governance decision surfaces

That gives the next provenance work a consistent operator-facing review surface without redesigning the underlying research tables.

## Verification Command

```text
python test_bundle/scripts/verify_research_governance_audit_mirroring.py --json
```

Expected shape:

- `status = ok`
- no failures
- all covered governance decisions produce matching audit mirror rows
