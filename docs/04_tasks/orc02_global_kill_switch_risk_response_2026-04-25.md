# ORC-02 Global Kill Switch / Risk Response Task

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Operational Risk & Control Intelligence v1`
Packet: `ORC-02`
Status: `implemented`

## Active Boundary

Implement risk response orchestration, runtime safe-mode contract, order permission matrix, and recovery readiness after `ORC-01`.

## Required Surfaces

- `POST /system/risk-response/orchestrate`
- `GET /system/risk-response-orchestration/latest`
- `GET /system/runtime-safe-mode/latest`
- `GET /system/order-permission-matrix/latest`
- `GET /system/risk-recovery-readiness/latest`
- `POST /system/risk-recovery/request`

## Non-Goals

- do not replace LCC enforcement
- do not execute broker orders
- do not implement AFG approval workflow
- do not replay ORC-01 detection logic
- do not replay completed AES work

## Completion Evidence

- safe-mode contract exists
- response orchestrator exists
- runtime tables exist for orchestration, safe mode, recovery readiness, and recovery requests
- `/system/*` routes expose ORC-02 canonical surfaces
- verifier checks the plan and task surfaces

