# AIがdocsだけで回るループ設計

> Purpose: AI Agentがリポジトリの docs を canonical source として読み、状況把握、タスク選定、実行、検証、報告更新まで回せるようにする。

---

## 0. 目的

この設計は、QuantOps の開発・運用を「人間の記憶」や「チャット履歴」ではなく、`docs/` によって再開・継続できる状態にするためのものです。

目標:

- AI Agentが毎回同じ順番で状況把握できる
- 今やるべき task を docs から決定できる
- 実行後に reports / tasks / plans を更新できる
- 古い情報を現行状態と誤認しない
- 人間も同じ docs から作業状況を理解できる

---

## 1. 基本原則

1. `docs/00_index/README.md` を唯一の起点にする。
2. `docs/03_plans/current.md` を意思決定の起点にする。
3. `docs/04_tasks/current.md` を実行の起点にする。
4. `docs/11_reports/current_status.md` を現在状態の起点にする。
5. `docs/07_interfaces/` をAPI・payload・schemaの正とする。
6. チャット履歴は補助情報。canonical source ではない。
7. 古い report は historical evidence として扱い、current state にはしない。

---

## 2. docs-based agent loop 全体像

```text
START
  ↓
Read 00_index
  ↓
Load Context
  ↓
Load Current Plan
  ↓
Load Current Status
  ↓
Load Active Tasks
  ↓
Select Next Task
  ↓
Read Required Interfaces / Architecture / Runtime Docs
  ↓
Execute Task
  ↓
Verify
  ↓
Update Task / Report / Plan / Interface Docs
  ↓
Write Handover
  ↓
END or Continue
```

---

## 3. 推奨フォルダ責務

| Folder | Agent Role | Human Role |
|---|---|---|
| `00_index` | 起動入口・読み順決定 | 目次・導線 |
| `01_context` | 前提理解 | プロジェクト理解 |
| `02_architecture` | 構造理解 | 設計確認 |
| `03_plans` | 意思決定 | ロードマップ確認 |
| `04_tasks` | 実行対象 | 作業確認 |
| `05_workflows` | 手順判断 | 作業フロー確認 |
| `06_playbooks` | 障害対応 | 問題解決 |
| `07_interfaces` | 契約確認 | API/schema確認 |
| `08_dev_guides` | 実装ルール | 開発規約 |
| `09_runtime_ops` | 実行・検証 | 運用確認 |
| `10_agent` | AI制約・能力 | AIの動作理解 |
| `11_reports` | 状態把握・報告更新 | 進捗確認 |
| `99_archive` | 参照禁止/履歴扱い | 過去資料 |

---

## 4. Agent起動シーケンス

AI Agentは作業開始時に以下を読む。

```text
1. docs/00_index/README.md
2. docs/01_context/project_state.md
3. docs/03_plans/current.md
4. docs/11_reports/current_status.md
5. docs/04_tasks/current.md
6. docs/04_tasks/active_tasks.md
7. docs/10_agent/rules.md
8. docs/10_agent/constraints.md
```

必要に応じて読む:

```text
- docs/02_architecture/current_architecture.md
- docs/07_interfaces/current_contracts.md
- docs/08_dev_guides/current_dev_guide.md
- docs/09_runtime_ops/current_runtime_ops.md
- docs/05_workflows/dev-flow.md
```

---

## 5. ループ詳細

### Step 1: Read Index

目的:

- docs構造を理解する
- AI用読み順を取得する
- current state へのリンクを取得する

出力:

- required reading list
- current source map

---

### Step 2: Load Context

読むファイル:

```text
docs/01_context/project_state.md
docs/01_context/working_assumptions.md
```

確認すること:

- プロジェクトの現在フェーズ
- 作業前提
- 禁止事項
- 現在の主要ブランチ

---

### Step 3: Load Plan

読むファイル:

```text
docs/03_plans/current.md
docs/03_plans/roadmap.md
```

確認すること:

- 現在の開発レーン
- 直近の目標
- 優先順位
- 後回しにする領域

---

### Step 4: Load Current Status

読むファイル:

```text
docs/11_reports/current_status.md
```

確認すること:

- 完了済み
- 未完了
- 失敗/警告
- 次の推奨アクション
- historical report と current state の区別

---

### Step 5: Load Active Tasks

読むファイル:

```text
docs/04_tasks/current.md
docs/04_tasks/active_tasks.md
```

確認すること:

- active task
- blocked task
- next queue
- task priority
- completion criteria

---

### Step 6: Select Next Task

選定ルール:

1. P0 blocker があれば最優先
2. P1 active phase task を次に優先
3. interface gap が task をブロックしていれば interface task を先に実行
4. plan と無関係な task は実行しない
5. acceptance criteria が不明な task は先に task 修正を行う

---

### Step 7: Prepare Execution Context

タスク実行前に読む:

| Task Type | Required Docs |
|---|---|
| API/interface | `07_interfaces/current_contracts.md`, `api_endpoints.md` |
| Runtime/ops | `09_runtime_ops/current_runtime_ops.md`, `05_workflows/runtime-acceptance-flow.md` |
| Architecture | `02_architecture/current_architecture.md` |
| Development | `08_dev_guides/current_dev_guide.md`, `verification_guide.md` |
| Incident | `06_playbooks/<playbook>.md`, `05_workflows/incident-flow.md` |
| Agent behavior | `10_agent/rules.md`, `10_agent/constraints.md` |

---

### Step 8: Execute Task

実行中のルール:

- task の scope 外の変更をしない
- interface 変更は docs/07_interfaces を同時更新する
- runtime 変更は docs/09_runtime_ops を同時更新する
- architecture 変更は docs/02_architecture を同時更新する
- 仕様が曖昧な場合は推測せず、task を blocked にする

---

### Step 9: Verify

検証は task の `Verification` セクションに従う。

最低限の検証:

```text
- lint/typecheck if relevant
- tests if relevant
- docs link integrity if relevant
- acceptance criteria check
- runtime smoke check if relevant
```

検証結果は task の Completion Log または report に残す。

---

### Step 10: Update Docs

実行後に更新する場所:

| 状況 | 更新先 |
|---|---|
| task完了 | `04_tasks/active_tasks.md`, `completed.md` |
| 状態変更 | `11_reports/current_status.md` |
| plan変更 | `03_plans/current.md` |
| interface変更 | `07_interfaces/*` |
| runtime変更 | `09_runtime_ops/*` |
| architecture変更 | `02_architecture/*` |
| AI制約変更 | `10_agent/*` |

---

### Step 11: Handover

作業終了時に以下を残す。

```md
# Handover

## Completed
- <completed item>

## Changed Files
- <file>

## Verification
- <command/result>

## Remaining Work
- <next task>

## Risks / Notes
- <risk>

## Next Recommended Read
1. docs/00_index/README.md
2. docs/04_tasks/current.md
3. docs/11_reports/current_status.md
```

---

## 6. Stop Conditions

AI Agentは以下の場合に停止または human review に回す。

- production credential が必要
- financial/trading action を直接実行する必要がある
- task acceptance criteria が不明
- current plan と task が矛盾
- interface contract が存在しないのに実装が必要
- runtime state が current_status と矛盾
- migration risk が大きい
- destructive operation が必要

---

## 7. Recovery Loop

問題が起きた場合:

```text
Detect failure
  ↓
Read relevant playbook
  ↓
Classify incident
  ↓
Apply safe recovery
  ↓
Verify state
  ↓
Update report
  ↓
Create follow-up task
```

必要ファイル:

```text
docs/06_playbooks/<incident>.md
docs/05_workflows/incident-flow.md
docs/09_runtime_ops/incident_and_tracing.md
docs/11_reports/current_status.md
```

---

## 8. AI Agent用チェックリスト

作業開始前:

- [ ] 00_index を読んだ
- [ ] current plan を読んだ
- [ ] current status を読んだ
- [ ] active task を確認した
- [ ] constraints を確認した

作業中:

- [ ] scope 外変更をしていない
- [ ] interface/runtime/architecture の関連docsを確認した
- [ ] 不明点を推測していない

作業後:

- [ ] acceptance criteria を満たした
- [ ] verification を実行した
- [ ] current_status を更新した
- [ ] active_tasks を更新した
- [ ] handover を残した

---

## 9. 人間向け運用ルール

人間は以下だけ見れば現状把握できる。

```text
1. docs/00_index/README.md
2. docs/03_plans/current.md
3. docs/04_tasks/active_tasks.md
4. docs/11_reports/current_status.md
```

レビュー時は以下を見る。

```text
- task file の Acceptance Criteria
- report の Verification
- interface contract の更新有無
- root-level old docs が current state として扱われていないか
```

---

## 10. 成功条件

この loop は以下を満たせば成功。

- [ ] 新しいAIセッションが docs だけで現在作業を再開できる
- [ ] active task が常に1つ以上明確である
- [ ] current_status が古い report より優先される
- [ ] interface変更が docs/07_interfaces に反映される
- [ ] 実行後に handover が残る
- [ ] 人間が 5分以内に現状把握できる

---

## 11. 最小実装版

最初は以下だけでよい。

```text
docs/00_index/README.md
docs/03_plans/current.md
docs/04_tasks/current.md
docs/04_tasks/active_tasks.md
docs/07_interfaces/current_contracts.md
docs/10_agent/rules.md
docs/10_agent/constraints.md
docs/11_reports/current_status.md
```

この8ファイルが整えば、AI docs loop は回り始める。
