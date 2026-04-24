# Operational Risk & Control Contracts

Date: `2026-04-25`
Repo: `QuantOps_github`
Status: `orc04_contracts`

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

## ORC-03 Surfaces

1. `POST /system/execution-health/run`
2. `GET /system/execution-health/latest`
3. `GET /system/broker-health/latest`
4. `GET /system/venue-health/latest`
5. `GET /system/execution-anomalies/latest`
6. `GET /system/execution-incidents/latest`
7. `GET /system/execution-safe-mode-recommendation/latest`
8. `GET /system/broker-health/{broker_id}`
9. `GET /system/venue-health/{venue_id}`

## ORC-03 Contract Progression

- execution telemetry ingestion
- broker health state
- venue health state
- order lifecycle anomaly detection
- slippage and latency anomaly detection
- execution incident classification
- ORC-compatible execution safe-mode recommendation

## ORC-04 Surfaces

1. `POST /system/data-integrity/run`
2. `GET /system/data-integrity/latest`
3. `GET /system/market-feed-health/latest`
4. `GET /system/market-feed-health/{feed_id}`
5. `GET /system/symbol-data-health/latest`
6. `GET /system/symbol-data-health/{symbol}`
7. `GET /system/data-anomalies/latest`
8. `GET /system/data-incidents/latest`
9. `GET /system/mark-reliability/latest`
10. `GET /system/data-safe-mode-recommendation/latest`

## ORC-04 Contract Progression

- market feed freshness
- symbol data health
- missing and bad tick detection
- OHLCV integrity
- mark reliability
- data incident classification
- ORC-compatible data safe-mode recommendation
