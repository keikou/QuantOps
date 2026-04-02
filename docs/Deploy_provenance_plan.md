# Deploy Provenance Plan

Date: `2026-04-01`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `System Reliability Hardening Track`
Status: `in_progress`

## Purpose

This packet follows:

- `docs/Runtime_config_provenance_plan.md`

The next operator question after config provenance is:

```text
which code / deploy identity produced this run?
```

The first answer should be lightweight and local:

- git commit SHA
- branch
- dirty state
- app version

## First Deploy Provenance Invariant

```text
runtime run start
-> captures deploy provenance snapshot
-> computes stable deploy fingerprint
-> persists the same deploy provenance
in run_started audit and latest_orchestrator_run checkpoint
```

## Scope

This first packet captures:

- `commit_sha`
- `branch`
- `dirty`
- `app_version`

This packet does not yet capture:

- build id
- image digest
- release artifact id

Those can follow later if deployment packaging becomes formalized.

## Persistence Targets

The first implementation should write deploy provenance into:

- `audit_logs` for `event_type=run_started`
- `runtime_checkpoints` for `checkpoint_name=latest_orchestrator_run`
- runtime API response from `/runtime/run-once`

## Verification Artifact

- `test_bundle/scripts/verify_deploy_provenance.py`

The verifier should:

- run one runtime cycle
- read the `run_started` audit payload
- read the `latest_orchestrator_run` checkpoint payload
- confirm both contain `deploy_provenance`
- confirm fingerprints match
- confirm commit SHA and branch are non-empty

## Verification Command

```text
python test_bundle/scripts/verify_deploy_provenance.py --json
```

Expected shape:

- `status = ok`
- no failures
- `run_started` and checkpoint deploy fingerprints match
