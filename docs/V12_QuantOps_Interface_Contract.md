# V12 ↔ QuantOps Interface Contract

**Project:** QuantOps V12  
**Branch context:** `codex/post-phase7-hardening`  
**Document type:** Master interface contract / source of truth  
**Status:** Draft for hardening branch; intended to become the canonical interface spec after merge

---

## 1. Purpose

This document defines the authoritative contract between:

- **V12**: the trading engine and runtime truth producer
- **QuantOps**: the control plane, aggregation layer, and operator-facing workspace

The goal of this contract is to keep the system **loosely coupled but operationally coherent**.

This contract exists to answer five questions unambiguously:

1. Which side owns which data?
2. Which APIs are authoritative?
3. Which values may be summarized or transformed?
4. Which failures are acceptable and how must they be surfaced?
5. Which compatibility guarantees must be preserved during hardening and later refactors?

---

## 2. System Roles

### 2.1 V12

V12 is the **trading engine**.

It is responsible for:

- market ingestion and market truth
- strategy runtime
- planner and execution bridge behavior
- order and fill truth
- portfolio state truth
- runtime event truth
- risk / guard enforcement truth
- analytics source truth where derived from runtime and fills

V12 is the system of record for trade lifecycle and runtime causality.

### 2.2 QuantOps

QuantOps is the **control plane**.

It is responsible for:

- operator-facing workflows
- dashboard views
- aggregated summaries
- orchestration triggers
- status, health, monitoring, and incidents
- normalized read models for frontend consumption
- stale/degraded/no-data surfacing
- cross-service observability and provenance

QuantOps may summarize, normalize, and combine data from V12, but it must not redefine V12 truth.

### 2.3 Frontend

The frontend is the **presentation layer**.

It is responsible for:

- rendering normalized read models
- reflecting stable/degraded/stale/no-data states
- interacting with QuantOps API only
- presenting provenance, status, and diagnostics to operators

The frontend must not invent runtime values or compensate for backend truth gaps through client-side business logic.

---

## 3. Boundary Rule

The primary boundary rule is:

> **V12 owns trading truth. QuantOps owns operational presentation and orchestration.**

This implies:

- V12 computes runtime truth.
- QuantOps consumes and republishes operational read models.
- The frontend renders those read models.
- No downstream layer may silently override upstream truth.

---

## 4. Ownership Model

## 4.1 Data Ownership Matrix

| Data / View | Canonical Owner | Secondary Consumer | Notes |
|---|---|---|---|
| market prices | V12 | QuantOps | QuantOps may cache or summarize, but price truth originates in V12 |
| runtime runs | V12 | QuantOps | QuantOps may aggregate recent runs and run detail views |
| runtime stage events | V12 | QuantOps | Used for timelines and drilldown |
| planner truth | V12 | QuantOps | QuantOps may surface planner evidence and diagnostics |
| execution orders | V12 | QuantOps | QuantOps is read-only for truth representation |
| execution fills | V12 | QuantOps | Fill truth is authoritative in V12 |
| portfolio positions | V12 | QuantOps | QuantOps may expose snapshots/read models |
| equity snapshots | V12 | QuantOps | QuantOps may render overview summaries |
| risk decisions / enforcement | V12 | QuantOps | QuantOps may display risk state and guard outcomes |
| alerts / incidents | QuantOps | Frontend | May include V12-derived evidence |
| health summaries | QuantOps | Frontend | Aggregated operational health view |
| debug provenance | QuantOps | Frontend | Must preserve upstream origin metadata |

## 4.2 Write Ownership

Only the following write categories are permitted across the boundary:

### QuantOps → V12
- trigger run
- request controlled actions explicitly supported by V12 APIs
- request status/diagnostic retrieval
- request configuration or governance actions **only if** V12 explicitly exposes safe mutating endpoints

### Forbidden
- QuantOps must not directly write runtime truth tables that belong to V12
- QuantOps must not synthesize fills, positions, or equity as if they were V12 truth
- Frontend must not directly call V12 in normal operation

---

## 5. Contract Layers

This contract is split into four layers:

### 5.1 Transport Contract
Defines HTTP endpoints, methods, status codes, timeouts, and versioning expectations.

### 5.2 Data Contract
Defines schema-level expectations for records and summaries.

### 5.3 Semantic Contract
Defines meaning:
- stable vs display semantics
- truth vs summary
- stale vs degraded vs unavailable
- source provenance rules

### 5.4 Operational Contract
Defines:
- retries
- fallback rules
- observability
- trace propagation
- failure exposure

---

## 6. Core Architectural Flow

```text
Operator
  ↓
Frontend
  ↓
QuantOps API
  ↓
V12 API
  ↓
Runtime / Planner / Execution / Portfolio / Risk Truth
```

For read paths:

```text
V12 truth
  ↓
QuantOps normalization / aggregation
  ↓
Frontend rendering
```

For control paths:

```text
Frontend action
  ↓
QuantOps validation / orchestration
  ↓
V12 controlled endpoint
  ↓
V12 runtime mutation or trigger
  ↓
QuantOps read-back / status projection
```

---

## 7. API Contract

## 7.1 General Rules

1. QuantOps consumes V12 through explicit route contracts only.
2. QuantOps must preserve upstream identity and provenance when exposing normalized data.
3. QuantOps may transform payload shapes for the frontend, but:
   - must not alter truth meaning
   - must not suppress authoritative upstream status without surfacing degradation
4. All route-level changes that affect semantics require contract review.
5. New routes should prefer additive evolution over destructive replacement.

## 7.2 Minimum V12 Surface Required by QuantOps

The exact implementation paths may evolve, but the contract categories below must remain available.

### Portfolio
- `GET /portfolio/overview`
- `GET /portfolio/positions`

### Execution
- `GET /execution/orders`
- `GET /execution/fills`

### Runtime
- `POST /runtime/run-once`
- `GET /runtime/runs`
- `GET /runtime/runs/{run_id}` or equivalent run-detail endpoint

### Risk
- `GET /risk/snapshot`

### Analytics
- `GET /analytics/pnl`
- `GET /analytics/execution`

### Diagnostics / Provenance
- planner truth diagnostics
- execution bridge diagnostics
- runtime event / reason by-run diagnostics
- any route required to support run-detail evidence in QuantOps

## 7.3 QuantOps Surface for Frontend

The frontend should prefer QuantOps read models for:
- overview
- execution summaries and run details
- portfolio views
- risk summaries
- monitoring and health
- alerts and incidents
- command-center aggregation
- stale/degraded/no-data rendering

The frontend must not depend on V12 route shape.

---

## 8. Request and Response Requirements

## 8.1 Common Request Requirements

All cross-service requests should support:

- request timestamp
- trace / correlation identifier
- caller identity or service name where relevant
- timeout budget awareness
- deterministic parameter semantics

## 8.2 Common Response Requirements

All responses exposed across the boundary should support, where applicable:

- `status`
- `generated_at` or equivalent timestamp
- source provenance
- stale/degraded/no-data flags when relevant
- machine-readable error surface for partial failure
- stable identifiers for run, symbol, and component entities

## 8.3 Success Semantics

A transport-level success does **not** automatically imply truth completeness.

QuantOps must distinguish:
- request succeeded and data is current
- request succeeded but data is stale
- request succeeded but data is partial
- request succeeded but upstream component is degraded
- request failed

---

## 9. Semantic Contract

## 9.1 Stable Semantics vs Display Semantics

### Stable Semantics
Stable semantics are the durable meanings that downstream systems may rely on safely.

Examples:
- a run status enumeration
- a fill quantity sign convention
- total equity definition
- stale/degraded flag meaning

Stable semantics must not change without an explicit versioning decision.

### Display Semantics
Display semantics are frontend-facing presentation choices.

Examples:
- badge color
- grouped summary labels
- expanded timeline wording
- convenience fields added purely for UX

Display semantics may change more freely as long as stable semantics remain intact.

## 9.2 Truth vs Summary

### Truth
Truth is the authoritative runtime or state representation produced by the owning system.

Examples:
- fills in V12
- planner evidence in V12
- runtime event reasons in V12

### Summary
Summary is a derived operational read model optimized for consumption.

Examples:
- overview cards
- aggregated recent runs
- frontend-normalized execution summary

A summary may compress truth but must not contradict it.

## 9.3 Provenance Rule

Every QuantOps summary that is materially derived from V12 truth should preserve provenance at least at one of these levels:

- source route
- source record identifiers
- source generation timestamp
- source service identity

When a value is partly derived in QuantOps, the derivation layer must be explicit.

---

## 10. Data Contract

## 10.1 Canonical Entity Set

The contract assumes the following conceptual entities exist:

- run
- runtime stage
- order
- fill
- position
- equity snapshot
- market price
- risk snapshot
- alert / incident
- governance / strategy control item

## 10.2 Execution Fill Contract

The fill record must be treated as canonical execution truth.

Minimum conceptual fields:

- `run_id`
- `symbol`
- `side`
- `qty`
- `price`
- `timestamp`
- identifier for the fill record
- optional order linkage
- optional venue / execution metadata

Rules:
- signed exposure must be derivable deterministically
- QuantOps must not synthesize missing fills
- if fills are absent, QuantOps must surface absence rather than infer trade completion

## 10.3 Position Contract

The position read model may be published by QuantOps, but position truth must trace back to V12.

Minimum conceptual fields:

- `symbol`
- `qty`
- `avg_price`
- `mark_price`
- `market_value`
- `unrealized_pnl`
- `realized_pnl` where relevant
- snapshot timestamp

Rules:
- position quantity must ultimately be reconcilable with V12 execution truth
- QuantOps may display snapshots, not redefine state transitions

## 10.4 Equity Contract

Minimum conceptual fields:

- `total_equity`
- `cash_balance`
- `gross_exposure`
- `net_exposure`
- snapshot timestamp

Rule:
- equity summaries rendered in QuantOps must identify whether they are authoritative V12 values or QuantOps-built summaries from authoritative components

## 10.5 Runtime Run Contract

Minimum conceptual fields:

- `run_id`
- `status`
- `trigger`
- `mode`
- `started_at`
- `completed_at` or equivalent
- stage summary / checkpoints
- failure reason if applicable

QuantOps may add:
- operator-friendly diagnosis
- grouped stage timeline
- recurrence context
- remediation hints

But QuantOps must preserve the upstream run identity and status semantics.

---

## 11. UI Binding Contract

The frontend binds to QuantOps read models, but the semantic backing should follow these rules.

## 11.1 Execution Views
Canonical upstream truth: **V12 execution fills and execution orders**

QuantOps responsibilities:
- normalize for page rendering
- expose run-level drilldown
- surface degraded or partial truth
- preserve run linkage and evidence

## 11.2 Portfolio Views
Canonical upstream truth: **V12 positions / portfolio state**

QuantOps responsibilities:
- publish operator-friendly position snapshots
- surface stale state if upstream refresh is delayed
- avoid client-side portfolio recomputation as a truth substitute

## 11.3 Overview Views
Canonical upstream truth: **V12 summary and equity-related truth, combined through QuantOps where needed**

QuantOps responsibilities:
- expose concise overview cards
- preserve stable semantics for operator decisions
- distinguish between authoritative values and convenience summaries when necessary

## 11.4 Monitoring / Alerts / Incidents
Canonical operational owner: **QuantOps**

QuantOps responsibilities:
- aggregate system health
- correlate frontend, QuantOps, and V12 observations
- preserve traceability back to source failures

---

## 12. Runtime Control Contract

## 12.1 Run Triggering

QuantOps may expose operator controls for:
- manual run trigger
- scheduler-driven trigger
- selected operational actions tied to governance or runtime control

Rules:
- all mutating runtime actions must be explicit
- triggered actions must return or expose stable run identity
- QuantOps must read back resulting status rather than assume success from acceptance alone

## 12.2 Run Observation

For each triggered run, QuantOps should be able to retrieve or reconstruct:

- acceptance or rejection
- run identity
- stage progression
- planner evidence
- execution bridge evidence
- final status
- artifacts or diagnostic bundles where available

## 12.3 Risk / Guard Interaction

When risk or guard logic blocks or modifies execution, the contract should allow QuantOps to surface:

- whether enforcement occurred
- at what stage it occurred
- whether it was deny / resize / reduce-only / halt or equivalent
- reason and evidence references where available

---

## 13. Failure Model

## 13.1 Failure Categories

The cross-service failure model distinguishes:

- **upstream unavailable**: V12 cannot be reached
- **upstream timeout**: V12 did not respond within budget
- **partial upstream truth**: route succeeded but returned incomplete truth
- **stale data**: data is older than freshness expectation
- **degraded data**: data exists but should not be treated as fully reliable
- **normal no-data**: empty result is expected and not an error

These categories must not be collapsed into a generic success/failure badge.

## 13.2 Frontend Exposure Rules

The frontend must receive enough information from QuantOps to distinguish:
- stale
- degraded
- unavailable
- empty but valid

## 13.3 Fallback Rules

Fallbacks are allowed only under these principles:

1. fallback must never masquerade as authoritative truth
2. fallback must preserve degraded or partial status
3. fallback must be deterministic and documented
4. fallback must not violate ownership boundaries

Example:
- QuantOps may keep rendering a last-known-good summary with stale labeling
- QuantOps may not invent fills or silently replace missing V12 execution truth

---

## 14. Observability Contract

## 14.1 Trace Propagation

Every request that participates in a cross-service flow should preserve a correlation or trace identifier.

This identifier should allow investigation across:
- frontend events
- QuantOps request logs
- QuantOps upstream V12 calls
- V12 request logs
- run-detail diagnostics when applicable

## 14.2 Timing and Budget Visibility

QuantOps should expose or log timing breakdowns where practical:
- handler time
- serialization time
- total route time
- upstream V12 time

This supports timeout and hardening work.

## 14.3 Provenance and Diagnostics

QuantOps must preserve enough metadata to support:
- run-detail drilldown
- stage evidence display
- origin route tracing
- diagnosis severity and retryability where implemented

---

## 15. Compatibility and Versioning

## 15.1 Additive Change Preference

Prefer additive changes:
- add fields
- add endpoints
- add enum values cautiously with graceful handling

Avoid destructive changes unless versioned.

## 15.2 Breaking Change Criteria

A change is breaking if it alters:
- ownership semantics
- stable field meaning
- required route availability
- status enumeration meaning
- stale/degraded/no-data semantics
- traceability expectations

## 15.3 Version Scope

Versioning may be route-level, domain-level, or service-level, but the following must be documented:
- what changed
- who is affected
- migration path
- rollback plan

---

## 16. Security and Safety Principles

Even in local-first operation, the boundary should preserve these principles:

- only explicit control actions mutate runtime
- read models should be safe to expose to the frontend
- sensitive mutation surfaces should not be proxied casually
- debug endpoints must remain intentional and reviewable
- orchestration must not bypass guard logic

---

## 17. Test Contract

The contract is not complete unless it is testable.

Minimum validation surface:

## 17.1 Contract Tests
Validate:
- route existence
- required fields
- enum semantics
- stale/degraded flags
- trace propagation

## 17.2 Regression Tests
Validate:
- overview normalization
- execution run-detail rendering contract
- portfolio snapshot semantics
- timeout / upstream degradation handling

## 17.3 Smoke Tests
Validate:
- V12 startup
- QuantOps startup
- frontend startup
- one paper run
- run_id visibility
- cross-service diagnostics path

---

## 18. Hardening Rules for Post-Phase7 Work

During post-Phase7 hardening, the following rules should be enforced:

1. Do not merge route-shape changes without checking this contract.
2. Do not rename status meanings without documenting semantic impact.
3. Do not move ownership of trading truth from V12 into QuantOps.
4. Do not compensate for backend uncertainty with frontend business logic.
5. Do not introduce silent fallback paths.
6. Prefer explicit provenance over convenience-only payloads.
7. Keep read-model optimizations downstream of truth, not upstream of it.

---

## 19. Non-Goals

This document does **not** define:
- internal implementation details of V12 modules
- internal implementation details of QuantOps frontend components
- styling rules for the GUI
- every field of every DTO in code

Those details belong in implementation docs or code-level schemas.

This document defines the **cross-system contract** that those details must respect.

---

## 20. Canonical Principles

The contract can be summarized in ten rules:

1. **V12 owns trading truth.**
2. **QuantOps owns operational orchestration and presentation.**
3. **Frontend renders; it does not decide truth.**
4. **Summaries may compress truth but must not contradict it.**
5. **Stable semantics are stronger than display semantics.**
6. **Fallbacks must be visible, never silent.**
7. **Traceability is part of the contract, not an optional extra.**
8. **Timeouts and degradation must be modeled explicitly.**
9. **Boundary changes require contract review.**
10. **If ownership is unclear, the contract is incomplete.**

---

## 21. Recommended Follow-up Documents

This file should be used together with:

- `V12_Architecture_Master.md`
- `QuantOps_Architecture_Master.md`

Recommended implementation-adjacent appendices after merge:

- endpoint-by-endpoint request/response schema appendix
- stale/degraded/no-data semantics appendix
- run-detail and runtime stage enum appendix
- trace / correlation field appendix
- ownership matrix by route appendix

---

## 22. Change Log

### v0.1
- initial canonical interface contract draft for `codex/post-phase7-hardening`
- establishes ownership, semantic, operational, and observability rules
- intended to anchor post-merge documentation cleanup
