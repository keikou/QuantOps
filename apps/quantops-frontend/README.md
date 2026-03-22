# Sprint5 QuantOps Frontend Connected

QuantOps 用 Sprint5 フロントエンド雛形です。Next.js App Router を使い、Overview / Portfolio / Risk / Monitoring / Alerts / Scheduler を実データ接続前提で構成しています。

## 起動

```bash
cp .env.example .env.local
npm install
npm run dev
```

ブラウザ:

```text
http://localhost:3000
```

## 接続先

- QuantOps API: `http://localhost:8010`
- Next.js 側は `/api/proxy/*` で backend に中継
- backend 不達時は `QUANTOPS_ENABLE_MOCK_FALLBACK=true` なら mock で表示

## 主なページ

- `/` Overview
- `/portfolio`
- `/risk`
- `/monitoring`
- `/alerts`
- `/scheduler`
- `/strategies`, `/execution`, `/research`, `/alpha-factory`, `/governance`, `/config`, `/admin`

## 追加点

- Query hooks
- API proxy route
- typed API models
- chart / table / KPI コンポーネント
- Sidebar / Topbar / status shell

## 次の実装候補

1. 認証 / RBAC
2. write mutations (ack alert, pause job, run job)
3. 実際の QuantOps schema に合わせた DTO 調整
4. Governance / Alpha Factory の本実装


## Write-enabled build

This build adds write actions through the QuantOps API proxy. Included write flows:

- alert acknowledge
- scheduler run / pause / resume
- strategy start / stop
- governance approve / reject
- config draft save

When the upstream QuantOps API is unavailable, the proxy can serve mutable in-memory mock responses if `QUANTOPS_ENABLE_PROXY_MOCK=true`.


## Production-ready additions

- RBAC-aware UI gating
- audit log screen
- confirmation modal for write actions
- demo role switcher in top bar
- mock audit trail for local validation
