# docs/07_interfaces 完全テンプレート

> Purpose: 人間とAI Agentが、コードを読まずにAPI・イベント・データ・ランタイムI/Oを理解できる状態にする。

---

## 0. このフォルダの役割

`docs/07_interfaces/` は、QuantOps内のすべての「接続点」を定義する canonical layer です。

ここで扱う対象:

- API endpoints
- request / response schema
- internal events
- runtime payloads
- DB / DuckDB / JSON / checkpoint schema
- service-to-service contracts
- operator bundle payloads
- frontend/backend contract

原則:

1. コードを読まないと分からない仕様は、ここに昇格する。
2. 実装詳細ではなく、入出力契約を定義する。
3. 仕様変更時は、関連 task / workflow / runtime docs へリンクする。
4. 古い仕様を削除せず、breaking change として記録する。

---

## 1. 推奨ファイル構成

```text
docs/07_interfaces/
├─ README.md
├─ current_contracts.md
├─ api_endpoints.md
├─ endpoint_contract_matrix.md
├─ event_contracts.md
├─ data_schema.md
├─ runtime_payloads.md
├─ runtime_checkpoint_shapes.md
├─ operator_bundle_payloads.md
├─ frontend_backend_contracts.md
├─ service_contracts.md
└─ changelog.md
```

---

## 2. README.md テンプレート

```md
# 07_interfaces

## Purpose
This folder defines canonical interface contracts for APIs, events, payloads, schemas, and service boundaries.

## Read Order
1. current_contracts.md
2. endpoint_contract_matrix.md
3. api_endpoints.md
4. event_contracts.md
5. data_schema.md
6. runtime_payloads.md
7. operator_bundle_payloads.md

## Rules
- Do not rely on memory for interface behavior.
- If an endpoint, event, or payload is used by more than one component, document it here.
- If a contract is ambiguous, create or update a contract document before implementation.
- Breaking changes must be recorded in changelog.md.

## Related Docs
- ../02_architecture/current_architecture.md
- ../04_tasks/current.md
- ../05_workflows/runtime-acceptance-flow.md
- ../09_runtime_ops/current_runtime_ops.md
```

---

## 3. current_contracts.md テンプレート

```md
# Current Interface Contracts

## Status
- Last updated: YYYY-MM-DD
- Owner: <owner/team/agent>
- Contract stability: draft | active | stable | deprecated

## Active Contract Families

| Family | File | Status | Used By | Notes |
|---|---|---:|---|---|
| API Endpoints | api_endpoints.md | active | backend/frontend/agent | Main HTTP contracts |
| Endpoint Matrix | endpoint_contract_matrix.md | active | backend/frontend/tests | Route-level summary |
| Events | event_contracts.md | draft | runtime/ops/agent | Internal event flow |
| Data Schema | data_schema.md | active | DB/services/reports | Storage schemas |
| Runtime Payloads | runtime_payloads.md | draft | runtime/ops | Runtime I/O payloads |
| Operator Bundles | operator_bundle_payloads.md | draft | operator/agent | AI/operator state bundles |

## Current Gaps

| Gap | Impact | Owner | Target Task |
|---|---|---|---|
| <gap> | <why it matters> | <owner> | ../04_tasks/<task>.md |

## Rules For AI Agents

1. Before modifying API, event, or payload logic, read this file first.
2. If a contract is missing, create a draft contract file before coding.
3. If implementation differs from this doc, update this doc or create a task to reconcile.
```

---

## 4. api_endpoints.md テンプレート

```md
# API Endpoints

## Status
- Last updated: YYYY-MM-DD
- Stability: draft | active | stable

## Endpoint Template

### `<METHOD> <PATH>`

#### Purpose
<What this endpoint does.>

#### Used By
- Frontend: <route/component>
- Backend service: <service/module>
- Agent/runtime: <yes/no>
- Tests: <test path>

#### Request

##### Path Parameters
| Name | Type | Required | Description |
|---|---|---:|---|
| id | string | yes | Resource identifier |

##### Query Parameters
| Name | Type | Required | Default | Description |
|---|---|---:|---|---|
| limit | integer | no | 100 | Max rows |

##### Request Body
```json
{
  "example_key": "example_value"
}
```

##### Request Schema
| Field | Type | Required | Constraints | Description |
|---|---|---:|---|---|
| example_key | string | yes | non-empty | Example field |

#### Response

##### Success Response
```json
{
  "status": "ok",
  "data": {}
}
```

##### Response Schema
| Field | Type | Required | Description |
|---|---|---:|---|
| status | string | yes | `ok` on success |
| data | object | yes | Payload object |

#### Error Responses
| HTTP Status | Error Code | Meaning | Recovery |
|---:|---|---|---|
| 400 | BAD_REQUEST | Invalid input | Fix request payload |
| 404 | NOT_FOUND | Resource missing | Check identifier |
| 500 | INTERNAL_ERROR | Server failure | See runtime logs |

#### Side Effects
- DB write: yes/no
- Cache mutation: yes/no
- Event emitted: yes/no
- Files written: yes/no

#### Related Contracts
- endpoint_contract_matrix.md
- event_contracts.md
- data_schema.md

#### Related Code
- `<path/to/router>`
- `<path/to/service>`

#### Related Tests
- `<path/to/test>`
```

---

## 5. endpoint_contract_matrix.md テンプレート

```md
# Endpoint Contract Matrix

| Method | Path | Purpose | Request Contract | Response Contract | Side Effects | Status | Owner |
|---|---|---|---|---|---|---|---|
| GET | /system/health | Runtime health | none | HealthResponse | none | stable | backend |
| POST | /system/example | Example action | ExampleRequest | ExampleResponse | DB/event | draft | backend |

## Status Legend

- draft: defined but not fully implemented/tested
- active: implemented and used
- stable: tested and safe for consumers
- deprecated: should not be used by new code

## AI Usage Rule

When changing an endpoint, update this matrix first or in the same PR.
```

---

## 6. event_contracts.md テンプレート

```md
# Event Contracts

## Event Lifecycle Overview

```text
producer -> event -> queue/bus/log -> consumer -> state/report/update
```

## Event Template

### Event: `<event.name>`

#### Purpose
<Why this event exists.>

#### Producer
| Component | Code Path | Trigger |
|---|---|---|
| <service> | <path> | <condition> |

#### Consumers
| Component | Code Path | Behavior |
|---|---|---|
| <consumer> | <path> | <what it does> |

#### Payload Example
```json
{
  "event_type": "example.event",
  "event_id": "uuid",
  "timestamp": "2026-04-25T00:00:00Z",
  "source": "service_name",
  "payload": {}
}
```

#### Payload Schema
| Field | Type | Required | Description |
|---|---|---:|---|
| event_type | string | yes | Event name |
| event_id | string | yes | Unique event id |
| timestamp | string | yes | ISO-8601 UTC timestamp |
| source | string | yes | Producer component |
| payload | object | yes | Event-specific payload |

#### Ordering / Idempotency
- Ordering required: yes/no
- Idempotency key: <field>
- Retry safe: yes/no

#### Failure Behavior
| Failure | Expected Behavior | Recovery |
|---|---|---|
| Consumer fails | <behavior> | <recovery> |
| Duplicate event | <behavior> | <recovery> |

#### Related Tasks
- ../04_tasks/<task>.md
```

---

## 7. data_schema.md テンプレート

```md
# Data Schema

## Storage Overview

| Store | Purpose | Location | Owner |
|---|---|---|---|
| DuckDB | analytical/runtime state | <path> | backend |
| JSON | config/checkpoint | <path> | runtime |

## Table Template

### Table: `<table_name>`

#### Purpose
<What this table stores.>

#### Grain
One row per <entity/time/strategy/etc>.

#### Columns
| Column | Type | Nullable | Key | Description |
|---|---|---:|---|---|
| id | string | no | primary | Unique id |
| created_at | timestamp | no | index | Creation time |

#### Example Row
```json
{
  "id": "example",
  "created_at": "2026-04-25T00:00:00Z"
}
```

#### Producers
- <service/module>

#### Consumers
- <service/module/report>

#### Migration Notes
- <schema changes>

#### Validation Rules
- <rule>
```

---

## 8. runtime_payloads.md テンプレート

```md
# Runtime Payloads

## Runtime Payload Template

### Payload: `<payload_name>`

#### Purpose
<What this payload controls or represents.>

#### Created By
- <component>

#### Consumed By
- <component>

#### Example
```json
{
  "run_id": "run_YYYYMMDD_HHMMSS",
  "status": "ok",
  "payload": {}
}
```

#### Schema
| Field | Type | Required | Description |
|---|---|---:|---|
| run_id | string | yes | Runtime execution id |
| status | string | yes | ok/warn/error |
| payload | object | yes | Runtime-specific payload |

#### Invariants
- run_id must be unique per execution.
- status must be one of: ok, warn, error.

#### Failure Behavior
| Condition | Expected Behavior |
|---|---|
| Missing required field | reject payload |
| Unknown status | mark invalid |
```

---

## 9. operator_bundle_payloads.md テンプレート

```md
# Operator Bundle Payloads

## Purpose
Defines payloads passed to humans or AI operators for resume, review, approval, or incident response.

## Bundle Template

### Bundle: `<bundle_name>`

#### Purpose
<Why this bundle exists.>

#### Intended Reader
- human operator
- AI agent
- both

#### Example
```json
{
  "bundle_id": "bundle_YYYYMMDD",
  "created_at": "2026-04-25T00:00:00Z",
  "current_plan": "../03_plans/current.md",
  "active_tasks": ["../04_tasks/current.md"],
  "current_status": "../11_reports/current_status.md",
  "constraints": ["../10_agent/constraints.md"]
}
```

#### Required Sections
| Field | Type | Required | Description |
|---|---|---:|---|
| bundle_id | string | yes | Unique bundle id |
| created_at | string | yes | Creation time |
| current_plan | string | yes | Link to current plan |
| active_tasks | array[string] | yes | Active task docs |
| current_status | string | yes | Current status doc |
| constraints | array[string] | yes | Agent constraints |

#### Validation Checklist
- [ ] Links resolve
- [ ] Current status is latest
- [ ] Active tasks are not archived
- [ ] Constraints are included
```

---

## 10. changelog.md テンプレート

```md
# Interface Changelog

## YYYY-MM-DD

### Added
- <new contract>

### Changed
- <changed contract>

### Deprecated
- <deprecated contract>

### Breaking Changes
| Contract | Change | Migration |
|---|---|---|
| <contract> | <change> | <migration path> |
```

---

## 11. 最低限の完成条件

`07_interfaces` は以下を満たしたら「実用可能」とする。

- [ ] endpoint_contract_matrix.md に主要APIが載っている
- [ ] api_endpoints.md に主要APIのrequest/response例がある
- [ ] event_contracts.md に主要イベントのproducer/consumerがある
- [ ] data_schema.md に主要テーブル/JSON schemaがある
- [ ] runtime_payloads.md にruntime入出力の形がある
- [ ] operator_bundle_payloads.md にAI/human resume payloadがある
- [ ] changelog.md にbreaking change記録ルールがある

---

## 12. AI Agent向け運用ルール

AI Agentは以下を守る。

1. API変更前に `endpoint_contract_matrix.md` を確認する。
2. payload変更前に `runtime_payloads.md` または `operator_bundle_payloads.md` を確認する。
3. event追加前に `event_contracts.md` に producer / consumer / payload を書く。
4. schema変更前に `data_schema.md` に migration note を書く。
5. 不明な契約は推測せず、draft contract を作ってから実装する。
