# Audit Provenance Gap Review

Date: `2026-04-01`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `System Reliability Hardening Track`
Status: `in_progress`

## Purpose

This packet is the next hardening lane after:

- `Recovery / Replay Confidence`
- `Cross-Phase Acceptance`

The goal is to make current audit and provenance strength explicit:

- what evidence chains already exist
- what evidence chains are still weak or indirect
- what the first local verifier can prove today without reopening prior closure work

## First Audit / Provenance Invariant

```text
dataset / feature provenance
-> immutable experiment record
-> model registration
-> governed alpha promotion
-> promoted runtime signal in the next accepted cycle
-> attributable runtime audit and checkpoint records
-> guard halt / resume audit continuity
```

This is intentionally a hardening invariant, not a new closure claim.

## What The First Local Verifier Should Prove

Artifact:

- `test_bundle/scripts/verify_audit_provenance.py`

The verifier should confirm that one local scenario preserves:

- research-factory provenance from dataset and feature registration into experiment and model registration
- immutable experiment lineage
- model-to-alpha linkage through governance state and promotion records
- runtime reuse of the promoted alpha in the next accepted cycle
- runtime audit records and checkpoint records tied to the accepted run
- guard halt and resume audit records with actor attribution

## Evidence That Already Exists In Repo

Existing surfaces already provide usable provenance anchors:

- `dataset_registry`
- `feature_registry`
- `experiment_tracker`
- `validation_registry`
- `model_registry`
- `model_state_transitions`
- `alpha_library`
- `alpha_status_events`
- `alpha_promotions`
- `signals`
- `runtime_runs`
- `runtime_run_steps`
- `runtime_checkpoints`
- `audit_logs`

That means the current lane can verify evidence linkage without changing prior phase logic.

## Current Strengths

- experiment records are already immutable
- model registration is versioned and emits explicit state transitions
- alpha governance writes explicit state transitions and library state
- runtime cycles already emit run, step, checkpoint, audit, and event records
- guard halt / resume paths already write audit records with actor and payload
- promoted alpha state can already change next-cycle runtime signals

## Current Gaps

### 1. Runtime To Governance Link Is Still Mostly Semantic

Current state:

- runtime signal selection can reflect the promoted alpha
- promotion records include `source_run_id`

Gap:

- there is not yet a strict foreign-key-style link from a runtime run to the exact model / experiment / alpha decision that affected it

Impact:

- attribution is possible, but not yet rigidly machine-verifiable across every boundary

### 2. Research Registration Is Not Mirrored Into Unified Audit Logs

Current state:

- research records are stored in dedicated tables

Gap:

- dataset / feature / experiment / model registrations are not consistently mirrored into `audit_logs`

Impact:

- the lineage exists, but one unified audit stream does not yet cover the full research side

### 3. Config Provenance Is Weak

Current state:

- runtime behavior depends on config, settings, and mode policy surfaces

Gap:

- accepted runs do not yet persist a normalized config fingerprint or effective config snapshot alongside runtime checkpoints

Impact:

- operator review can confirm runtime outcome, but not always the exact effective configuration that produced it

### 4. Deployment Provenance Is Weak

Current state:

- repo branch and code artifacts exist externally

Gap:

- runtime records do not yet persist deploy identity such as commit SHA, build id, image digest, or release marker

Impact:

- runtime-to-deployment traceability is still indirect

## Recommended Next Increment After This Packet

The next improvement should be one of:

1. add unified audit mirroring for research-factory registrations
2. persist effective runtime config snapshots into checkpoints or dedicated provenance tables
3. persist deploy identity on runtime runs and checkpoints
4. add a direct runtime-to-governance evidence link keyed by model / alpha / decision ids

## Verification Command

```text
python test_bundle/scripts/verify_audit_provenance.py --json
```

Expected shape:

- `status = ok`
- no failures
- first invariant holds on currently implemented surfaces
- remaining weaknesses stay documented as explicit gaps, not hidden assumptions
