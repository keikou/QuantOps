# Runtime Acceptance Flow

Date: `2026-04-02`
Status: `canonical`

## When To Use

Use this workflow when a task touches runtime truth, execution evidence, acceptance behavior, or operator diagnostics.

## Flow

1. identify the exact runtime property being validated from current docs first
2. define one narrow invariant or measurement target
3. locate the closest existing runtime or hardening verifier
4. decide whether to:
   - extend an existing verifier
   - add one new verifier
5. run the verifier in isolation first
6. only then widen the scenario if the first invariant is stable
7. preserve operator-visible evidence paths where possible

## Current Example

For the current next lane, `Strategy Evolution / Regime Adaptation Intelligence` should likely begin with one narrow regime-state check such as:

- regime degradation consistency
- strategy compatibility drift
- gating trigger visibility
- transition detection continuity

Current docs-ready packet:

- `SERI-01`

## Non-Goal

Do not use this workflow to re-prove already closed hardening packets unless a regression is found.
