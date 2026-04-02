# Audit Provenance Mirroring Plan

Date: `2026-04-01`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `System Reliability Hardening Track`
Status: `in_progress`

## Purpose

This packet is the first direct implementation follow-up from:

- `docs/Audit_provenance_gap_review.md`

The immediate goal is to mirror research-factory registrations into the unified audit stream so research-side provenance and runtime-side provenance can be reviewed from one place.

## First Mirroring Invariant

```text
dataset / feature / experiment / validation / model registration
-> creates the canonical research record
-> also creates a unified audit_logs mirror entry
with actor attribution and key lineage identifiers
```

## Scope

This packet should cover:

- `/research-factory/datasets/register`
- `/research-factory/features/register`
- `/research-factory/experiments/register`
- `/research-factory/validations/register`
- `/research-factory/models/register`

Each successful registration should produce:

- the existing canonical table row
- one mirrored `audit_logs` row in category `research_factory`

## Mirrored Audit Shape

Each audit record should keep:

- explicit `event_type`
- `actor`
- resource id
- relevant version or lineage fields
- creation timestamp copied from the registered resource

This packet does not try to mirror every nested payload field.
It only mirrors the fields needed for operator review and provenance tracing.

## Verification Artifact

- `test_bundle/scripts/verify_research_audit_mirroring.py`

The verifier should:

- register one dataset
- register one feature set
- register one experiment
- register one validation
- register one model
- confirm the canonical rows exist
- confirm one matching audit row exists for each registration
- confirm mirrored audit payloads keep the expected ids, versions, and actor attribution

## Why This Packet Comes Before Deeper Provenance Work

This is the smallest high-value change because:

- it does not alter prior phase logic
- it improves operator review immediately
- it gives the next provenance packets a unified audit surface to build on

## Likely Follow-Up After This Packet

After mirroring is stable, the next provenance implementation should be one of:

- runtime config fingerprint persistence
- deploy identity persistence
- stricter runtime-to-governance foreign-key-like linkage

## Verification Command

```text
python test_bundle/scripts/verify_research_audit_mirroring.py --json
```

Expected shape:

- `status = ok`
- no failures
- all five registration entrypoints produce matching audit mirror rows
