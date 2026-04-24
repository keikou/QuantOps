# Operational Risk & Control Contracts

Date: `2026-04-25`
Repo: `QuantOps_github`
Status: `orc02_contracts`

## Contract Intent

```text
the system must detect and respond to system-level risk before capital is irreversibly damaged
```

## ORC-01 Surfaces

1. `POST /system/operational-risk/run`
2. `GET /system/risk-state/latest`
3. `GET /system/global-risk-metrics/latest`
4. `GET /system/anomaly-detection/latest`
5. `GET /system/operational-incidents/latest`
6. `GET /system/risk-response/latest`
7. `POST /system/risk-response/execute`
8. `POST /system/global-kill-switch`
9. `GET /system/global-kill-switch/latest`
10. `POST /system/operational-risk/override`

## Contract Progression

- telemetry ingestion
- domain risk metrics
- anomaly detection
- incident classification
- global risk state
- response recommendation
- global kill-switch event
- operator override record

## ORC-02 Surfaces

1. `POST /system/risk-response/orchestrate`
2. `GET /system/risk-response-orchestration/latest`
3. `GET /system/runtime-safe-mode/latest`
4. `GET /system/order-permission-matrix/latest`
5. `GET /system/risk-recovery-readiness/latest`
6. `POST /system/risk-recovery/request`

## ORC-02 Contract Progression

- risk response orchestration
- runtime safe-mode contract
- order permission matrix
- LCC response payload
- execution safe-mode payload
- recovery readiness
- recovery request record
