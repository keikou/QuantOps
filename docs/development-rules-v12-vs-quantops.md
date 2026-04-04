# Development Rules: V12 vs QuantOps API

This document defines the recommended development operating rules after `Sprint6H-9.2.12`.

The key point is that V12 and QuantOps API should not be developed with the same mental model.

They serve different roles:

- V12 is the truth, runtime, and writer layer
- QuantOps API is the read-model, aggregation, and operator contract layer

When those roles are mixed, the system becomes harder to reason about, slower to stabilize, and easier to regress.

## Core Principle

Treat the two systems differently:

- V12: correctness-first
- QuantOps API: contract-and-latency-first

This is the most important operating rule.

## V12 Development Rules

### Purpose

V12 is responsible for:

- truth/accounting correctness
- runtime execution state
- writer behavior
- snapshots
- watermark/incremental processing
- stable summary sources for downstream reads

### What To Optimize For

- correctness of fills, positions, equity, and realized/unrealized PnL
- writer efficiency
- reduced read/write contention
- predictable summary routes
- observability of fallback and rebuild behavior

### What A Good V12 Change Looks Like

A good V12 change usually:

- makes writer work more incremental
- reduces full scans or full rewrites
- improves stable summary route cost
- adds or improves observability
- preserves truth semantics

### Required Checks For V12 Changes

If a change touches V12 writer or truth logic, confirm:

1. truth/accounting still matches expected behavior
2. `writer_cycles.jsonl` does not show regression
3. full rebuild reasons do not increase unexpectedly
4. summary route behavior remains stable
5. real stack still works, not just tests

### What Not To Do In V12

Do not:

- add GUI-specific display logic into truth paths
- reshape truth schema just to simplify one frontend view
- hide heavy truth work behind ad-hoc cache
- let ambiguous `latest` values mix stable and live semantics silently

## QuantOps API Development Rules

### Purpose

QuantOps API is responsible for:

- aggregation over V12 summary sources
- stale-first / cache / coalescing
- explicit summary contracts
- operator-facing provenance and freshness
- frontend-facing data shaping

### What To Optimize For

- stable latency
- explicit response contracts
- predictable cache behavior
- explainable freshness
- clean separation of stable summary and live feed

### What A Good QuantOps API Change Looks Like

A good QuantOps API change usually:

- reduces first-hit latency
- avoids repeated upstream calls
- uses read-model style upstream routes
- adds provenance/freshness metadata
- keeps frontend contracts simple and explicit

### Required Checks For QuantOps API Changes

If a change touches QuantOps API read paths, confirm:

1. `stable_value / live_delta / display_value` semantics still make sense
2. `build_status` and freshness fields remain accurate
3. first-hit and repeated-hit latency remain acceptable
4. debug/provenance surfaces still work
5. real stack behavior still matches tests

### What Not To Do In QuantOps API

Do not:

- re-implement truth/accounting logic independently from V12
- bring heavy truth recompute back into request paths
- hide ambiguous derived behavior behind generic fields
- mix stable totals and live feed windows without an explicit contract

## Boundary Rule

When deciding where a change belongs:

### Put it in V12 if it affects

- fills
- orders
- positions
- equity
- execution truth
- runtime truth
- snapshot generation
- writer cost

### Put it in QuantOps API if it affects

- response contract
- stale/fresh/degraded behavior
- cache/coalescing
- read aggregation
- summary route composition
- operator-facing fields
- frontend-friendly normalization

## Frontend Rule

Frontend should not be the place where truth semantics are invented.

Frontend should:

- consume explicit contracts
- prefer `display_value`
- show freshness separately
- keep stable summary and live feed visually separate

Frontend should not:

- infer hidden accounting rules
- reconstruct unstable mixed values from raw fragments unless necessary

## Shared Operational Workflow

Both V12 and QuantOps API changes should still follow the same broad delivery workflow:

1. reproduce on the real stack
2. add or preserve observability
3. make the change in a small step
4. run targeted tests
5. run build if frontend or API contract is touched
6. verify on the real stack
7. update CI-facing regression tests
8. update docs

## CI Rule

Old sprint tests are still active if CI still runs them.

This means:

- a test file name can be old
- but its contract can still be current

So for both V12 and QuantOps API:

- if CI runs the test, maintain it
- update it when contract changes
- delete it only if the contract is intentionally retired

## Documentation Rule

After any meaningful architectural or operational change:

- update runbook if startup/stop/health/log behavior changed
- update summary contracts if API semantics changed
- update architecture docs if read-model or writer boundaries changed

Docs are part of the engineering deliverable, not an afterthought.

## Recommended Default Development Pattern

### For V12 work

Use this pattern:

1. measure writer/read cost
2. add fallback reason visibility if needed
3. reduce `O(total)` work toward `O(delta)`
4. verify truth behavior
5. verify real-stack summary latency

### For QuantOps API work

Use this pattern:

1. define or clarify the response contract
2. prefer stable summary upstreams
3. add stale-first/coalescing if needed
4. verify first-hit vs repeated-hit latency
5. verify frontend rendering and observability

## Long-Term Goal

The target system shape should remain:

- V12 owns truth and efficient summary sources
- QuantOps API owns stable/live operator contracts
- frontend presents stable summary and live feed clearly

This separation is what keeps the system maintainable as new sprints extend functionality beyond `Sprint6H-9.2.12`.

## Related Docs

- [development-workflow.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/development-workflow.md)
- [api-summary-contracts.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/07_interfaces/api-summary-contracts.md)
- [architecture-read-models.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/02_architecture/architecture-read-models.md)
- [writer-observability.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/02_architecture/writer-observability.md)
- [ops-runbook.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/ops-runbook.md)
