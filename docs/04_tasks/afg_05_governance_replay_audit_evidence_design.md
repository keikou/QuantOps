# AFG-05 Governance Replay & Audit Evidence System

## Purpose

AFG-05 fixes every governance decision as replayable audit evidence.

Targets:

- Incident
- RCA
- Approval
- Feedback
- Dispatch

## Scope

```text
- governance decision trace recording
- replayable event chain construction
- immutable audit evidence generation
- incident-to-action trace reconstruction
```

## Non-Goals

```text
- new policy enforcement
- RBAC changes
- AFG-04 RCA logic expansion
- direct AES / ORC / LCC / Execution changes
- live trading decision engine changes
```

## Core Concept

```text
Reality -> Record -> Replay -> Verify
```

## Replay Targets

```text
- incident lifecycle
- RCA decision
- approval chain
- action items
- feedback generation
- feedback dispatch
```

## Immutable Design

```text
- append-only audit bundle table
- content hash
- chained previous hash
- timestamped bundle version
- JSON export
```

## Integration

```text
AFG-01: approval trace
AFG-02: enforcement consistency context
AFG-03: permission validation evidence
AFG-04: RCA and feedback source
```

## Checkpoint Complete Conditions

```text
- one incident can replay end-to-end
- approval trace can be reconstructed
- feedback dispatch can be reconstructed
- audit evidence export is available
- replay fails on hash mismatch
- replay fails on missing approval evidence for approval-gated feedback
```

