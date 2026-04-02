# Runtime Governance Linkage Plan

Date: `2026-04-01`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `System Reliability Hardening Track`
Status: `in_progress`

## Purpose

This packet follows the current hardening status update.

The main remaining provenance weakness is:

```text
accepted runtime cycle
can be attributed to config and deploy identity,
but the direct machine-verifiable link back to governance decision identity
is still relatively weak
```

## First Runtime Governance Linkage Invariant

```text
governance-promoted alpha
-> selected by runtime overlay
-> writes model_id / alpha_id / decision_source into signal metadata
-> writes the same linkage summary into runtime checkpoint details
```

## Scope

This first packet should link:

- `alpha_id`
- `model_id`
- governance decision source id
- runtime symbol that received the promoted overlay

Persistence surfaces:

- `signals.metadata_json`
- `alpha_signal_snapshots.summary_json`
- `runtime_checkpoints.latest_orchestrator_run.payload_json`

## Verification Artifact

- `test_bundle/scripts/verify_runtime_governance_linkage.py`

The verifier should:

- register dataset / feature / experiment / model lineage
- create a governed promotion through self-improving keep
- run the next accepted paper cycle
- confirm the promoted runtime signal contains explicit linkage metadata
- confirm checkpoint details contain the same linkage summary

## Why This Packet Matters

Once this packet is in place, the operator can go:

```text
accepted runtime cycle
-> promoted signal
-> linked alpha_id / model_id / decision_source
```

without inferring the linkage from separate tables.

## Verification Command

```text
python test_bundle/scripts/verify_runtime_governance_linkage.py --json
```

Expected shape:

- `status = ok`
- no failures
- runtime signal metadata and checkpoint linkage summary match
