# Execution Reality Next Lane Plan

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `post_hardening_next_lane`
Lane: `Execution Reality`
Status: `packet_01_defined`

## Purpose

The current hardening/resume slice is already treated as sufficiently complete.

This document defines the first narrow packet for the next lane:

```text
Execution Reality
```

The goal is not to reopen Phase2 closure.
The goal is to improve the next layer of value after correctness and hardening are already in place.

## Why Execution Reality

Architect re-alignment now treats:

- correctness
- consistency
- provenance
- observability

as sufficiently closed for the current slice.

That shifts the next-value question from:

- "can we trust the system?"

to:

- "how real and useful is the execution layer for decision quality and PnL?"

## First Packet

Packet name:

```text
Execution Reality Packet 01
```

Suggested verifier:

- `test_bundle/scripts/verify_execution_reality_next_lane.py`

## First Invariant

Invariant 1:

```text
execution quality summary surface is explicit and internally coherent
```

Definition:

For the latest execution quality summary surface, the repo should expose a consistent operator-facing summary with enough information to reason about execution quality without reopening lower-level raw evidence immediately.

## What This Invariant Checks

The first packet should verify that the execution quality summary includes and preserves:

- `run_id`
- `cycle_id`
- `mode`
- `order_count`
- `fill_count`
- `fill_rate`
- `avg_slippage_bps`
- `latency_ms_p50`
- `latency_ms_p95`

and that the summary remains internally coherent:

- `fill_count <= order_count`
- `0.0 <= fill_rate <= 1.0`
- latency percentiles are non-negative
- `latency_ms_p95 >= latency_ms_p50`

## Why This Comes First

This first packet is intentionally narrower than:

- fill simulation realism
- rejection modeling
- partial-fill sequencing realism
- venue-aware slippage realism

Those are likely later packets.

First we need the execution quality surface itself to be a stable, explicit contract.

## Current Repo Surface To Reuse

Current existing surfaces already suggest this lane can start without a large refactor:

- V12 `/execution/quality/latest_summary`
- V12 analytics execution summary surface
- execution quality snapshot storage
- operator diagnostic bundle references to execution quality

## Non-Goals

This first packet does not yet prove:

- that the slippage model is realistic
- that fills are exchange-realistic
- that partial-fill behavior is production-grade
- that rejection semantics are complete

It only proves that the current execution-quality summary surface is explicit and coherent enough to become the first anchor for the lane.

## Expected Output

The packet is complete when:

- the verifier passes
- the lane is documented as started
- future packets can extend from summary coherence into stronger realism checks

## Likely Next Packet After This

After Packet 01, the next likely candidates are:

1. partial-fill and rejection visibility
2. slippage realism by mode/path
3. execution-quality to PnL leakage linkage
