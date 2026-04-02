# Execution Reality Packet 02 Plan

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `post_hardening_next_lane`
Lane: `Execution Reality`
Packet: `02`
Status: `defined`

## Purpose

Packet 01 established that the execution quality summary surface is explicit and internally coherent.

Packet 02 now fixes the next narrow question:

```text
are partial-fill and rejection states operator-visible through the current execution surfaces?
```

## Invariant

Invariant 2:

```text
partial-fill and rejection states are visible and attributable across orders, fills, and execution state surfaces
```

## What This Checks

The packet should verify that:

- `/execution/orders` exposes `partially_filled` and `rejected` order states
- `/execution/fills` exposes fill rows attributable to the partially filled order
- `/execution/state/latest` reflects the open/submitted side correctly for a partially filled order while excluding rejected orders from submitted counts

## Why This Comes Before Deeper Realism

Before proving:

- slippage realism
- venue realism
- richer partial-fill sequencing
- rejection cause quality

the repo first needs to expose these states clearly on the current operator surfaces.

## Expected Surface Behavior

For a simple mixed scenario:

- one `partially_filled` order
- one related fill row
- one `rejected` order

the current execution surfaces should allow an operator or verifier to conclude:

- which order is still open/working
- which order was rejected
- which fill belongs to the partial path

## Suggested Verifier

- `test_bundle/scripts/verify_execution_reality_partial_fill_rejection.py`

## Non-Goals

This packet does not yet require:

- rejection-code taxonomy quality
- multi-fill same-order sequencing depth
- venue-specific partial-fill behavior
- exchange-grade realism

## Likely Next Packet

After this packet, the next natural direction is:

- slippage realism by path or mode
