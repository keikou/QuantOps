# Operational Risk & Control Intelligence Packet 02 Plan

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Operational Risk & Control Intelligence v1`
Packet: `ORC-02: Global Kill Switch / Risk Response Orchestrator`
Status: `implemented`

## Purpose

`ORC-02` operationalizes the risk response layer after `ORC-01`.

It answers:

- what runtime safe mode should execution and LCC read
- which order modes are allowed or blocked by risk level
- whether recovery can begin
- how a scoped kill-switch event becomes an auditable response orchestration

## Core Invariant

```text
When system-level risk becomes critical, the system must enter a safe state faster than it can create new risk.
```

## Canonical Surfaces

- `POST /system/risk-response/orchestrate`
- `GET /system/risk-response-orchestration/latest`
- `GET /system/runtime-safe-mode/latest`
- `GET /system/order-permission-matrix/latest`
- `GET /system/risk-recovery-readiness/latest`
- `POST /system/risk-recovery/request`

## Implementation Boundary

`ORC-02` consumes `ORC-01` risk state and global kill-switch events. It does not enforce broker orders directly and does not replace LCC or execution checks.

It produces:

- safe-mode contract
- order permission matrix
- LCC response payload
- execution safe-mode payload
- recovery readiness
- recovery request record

## Definition Of Done

- risk response can be orchestrated from current ORC risk state
- global kill-switch event can drive safe-mode state
- permission matrix is operator-visible
- LCC and execution payloads are explicit
- recovery readiness and request are audited
- docs and contract inventories include ORC-02 surfaces

