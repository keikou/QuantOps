# Execution Reality Packet 04 Plan

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `post_hardening_next_lane`
Lane: `Execution Reality`
Packet: `04`
Status: `defined`

## Purpose

Packet 03 established that slippage evidence is visible on both summary and fill surfaces.

Packet 04 now fixes the next narrow question:

```text
latest execution quality surfaces do not conflate run or mode identity across summary and detailed evidence
```

## Invariant

Invariant 4:

```text
latest execution quality summary and detail surfaces remain run-scoped and mode-consistent
```

## What This Checks

The packet should verify that:

- `/execution/quality/latest_summary` returns the newest execution-quality record
- `/execution/quality/latest` returns the same `run_id`, `cycle_id`, and `mode`
- detailed fill evidence attached to `/execution/quality/latest` belongs only to that latest `run_id`
- an older record from another mode does not bleed into the latest execution-quality view

## Why This Comes Before Mode Realism

Before proving:

- slippage realism by mode
- path-dependent execution quality differences
- execution quality drift between paper/live/shadow

the repo first needs to prove that current latest surfaces do not mix evidence across runs or modes.

## Non-Goals

This packet does not yet prove:

- that paper/live/shadow differences are economically realistic
- that path-specific slippage is calibrated
- that venue/path attribution is complete

It only proves that the latest execution-quality surfaces are safe to use as the anchor for later mode/path comparisons.

## Suggested Verifier

- `test_bundle/scripts/verify_execution_reality_mode_path_consistency.py`

## Likely Next Packet

After this packet, the next natural direction is:

- slippage realism by mode or execution path
