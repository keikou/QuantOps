# Resume Bundle Index Plan

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `System Reliability Hardening Track`
Status: `in_progress`

## Purpose

This packet follows:

- `docs/Resume_operator_packet_plan.md`
- `docs/Auto_resume_handover_2026-04-02.md`

The repo already has machine-readable and human-readable handover artifacts.
The next step is to add one short index doc that points humans at the right read order and verifier set.

## First Index Invariant

```text
current resume bundle
-> has one human-facing index
-> points to the current docs, artifacts, and live surfaces
-> keeps resume reading order explicit
```

## Verification Artifact

- `test_bundle/scripts/verify_resume_bundle_index.py`
