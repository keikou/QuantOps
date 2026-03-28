# Correlation Logging Guide

This document is the shortest practical guide for tracing one user action across frontend, QuantOps API, and V12.

Use it when you need to answer:

- which page access triggered a slow or failed API call
- whether the problem stopped in frontend, QuantOps API, or V12
- whether a timeout was user-side only or server-side too

## What To Read

Correlation analysis uses these files:

- [frontend_events.jsonl](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-api/runtime/logs/frontend_events.jsonl)
- [quantops_requests.jsonl](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-api/runtime/logs/quantops_requests.jsonl)
- [quantops_upstream_v12.jsonl](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-api/runtime/logs/quantops_upstream_v12.jsonl)
- [v12_requests.jsonl](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/v12-api/runtime/logs/v12_requests.jsonl)

The common join keys are:

- `trace_id`
- `request_id`
- `session_id`
- `page_path`

The main timing fields are:

- `duration_ms`
- `timeout_detected`
- `timeout_source`

## The Basic Flow

One browser navigation should look like this:

1. frontend writes `page_view`
2. frontend sends API request with `X-Trace-Id`
3. QuantOps API writes one request row
4. QuantOps API writes one or more upstream V12 rows
5. V12 writes its own request row

That means a single `trace_id` can connect:

- page access
- API error
- QuantOps latency
- V12 latency

## Fastest First Check

Run:

```powershell
python test_bundle/scripts/analyze_correlation_timeouts.py
```

If you need the raw grouped data:

```powershell
python test_bundle/scripts/analyze_correlation_timeouts.py --json
```

If this returns no incidents, the current logs do not show a correlated timeout.

## Example 1: User Says “Portfolio Open Is Slow”

Look for the most recent `page_view` for `/portfolio` in [frontend_events.jsonl](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-api/runtime/logs/frontend_events.jsonl).

Typical row shape:

```json
{
  "event_type": "page_view",
  "trace_id": "trace-1711590000000-abcd1234",
  "session_id": "sess-1711589000000-efgh5678",
  "page_path": "/portfolio",
  "status": "ok"
}
```

Then search the same `trace_id` in [quantops_requests.jsonl](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-api/runtime/logs/quantops_requests.jsonl).

Good sign:

- `path=/api/v1/portfolio/overview`
- `status=200`
- `duration_ms` is small

Bad sign:

- `duration_ms` is large
- `timeout_detected=true`

If QuantOps looks slow, continue with the same `trace_id` in [quantops_upstream_v12.jsonl](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-api/runtime/logs/quantops_upstream_v12.jsonl).

Interpretation:

- slow QuantOps + slow upstream V12:
  - V12 or upstream truth path is likely the bottleneck
- slow QuantOps + fast upstream V12:
  - QuantOps aggregation, cache miss, or serialization is more likely

## Example 2: Frontend Timeout But Backend Eventually Finishes

Look for `event_type=api_error` and `status=timeout` in [frontend_events.jsonl](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-api/runtime/logs/frontend_events.jsonl).

Typical row shape:

```json
{
  "event_type": "api_error",
  "trace_id": "trace-1711590100000-aa11bb22",
  "page_path": "/overview",
  "status": "timeout",
  "target": "/api/v1/dashboard/overview",
  "details": {
    "duration_ms": 35014
  }
}
```

Now inspect the same `trace_id` in [quantops_requests.jsonl](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-api/runtime/logs/quantops_requests.jsonl).

Pattern A:

- frontend timeout
- QuantOps `status=200`
- QuantOps `duration_ms` is slightly above frontend timeout window

Meaning:

- the browser gave up first
- the server still completed
- this is a user-visible timeout even if backend has no 5xx

Pattern B:

- frontend timeout
- QuantOps `timeout_detected=true` or `status=504`

Meaning:

- timeout was visible on both client and server side

## Example 3: QuantOps Timeout Is Actually a V12 Timeout

Start with the QuantOps row for the same `trace_id`.

If [quantops_requests.jsonl](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-api/runtime/logs/quantops_requests.jsonl) shows:

- large `duration_ms`
- `path=/api/v1/dashboard/overview`

then check [quantops_upstream_v12.jsonl](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-api/runtime/logs/quantops_upstream_v12.jsonl).

Typical upstream timeout row:

```json
{
  "event_type": "upstream_request_exception",
  "trace_id": "trace-1711590200000-zz99yy88",
  "quantops_path": "/api/v1/dashboard/overview",
  "upstream_path": "/portfolio/overview-summary/latest",
  "timeout_detected": true,
  "timeout_source": "exception"
}
```

Then confirm in [v12_requests.jsonl](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/v12-api/runtime/logs/v12_requests.jsonl).

Interpretation:

- QuantOps slow + upstream timeout + matching V12 slow row:
  - root cause is likely in V12 route/runtime/storage
- QuantOps slow + upstream timeout row exists but no V12 row:
  - request may have failed before V12 app handled it fully
  - check network/process health and startup logs too

## Decision Table

- frontend error only:
  - suspect browser timeout, client network, or render-side issue
- frontend + QuantOps slow, no V12 issue:
  - suspect QuantOps aggregation or cache miss path
- frontend + QuantOps + V12 all slow:
  - suspect V12 truth/read-model path or runtime contention
- QuantOps upstream timeout rows clustered on one path:
  - prioritize that V12 endpoint first

## Practical grep Examples

Find recent portfolio page views:

```powershell
Select-String -Path apps\quantops-api\runtime\logs\frontend_events.jsonl -Pattern '\"page_view\"|\"/portfolio\"'
```

Find one trace across all logs:

```powershell
$trace = "trace-1711590000000-abcd1234"
Select-String -Path apps\quantops-api\runtime\logs\frontend_events.jsonl -Pattern $trace
Select-String -Path apps\quantops-api\runtime\logs\quantops_requests.jsonl -Pattern $trace
Select-String -Path apps\quantops-api\runtime\logs\quantops_upstream_v12.jsonl -Pattern $trace
Select-String -Path apps\v12-api\runtime\logs\v12_requests.jsonl -Pattern $trace
```

Find timeout rows only:

```powershell
Select-String -Path apps\quantops-api\runtime\logs\quantops_requests.jsonl -Pattern '\"timeout_detected\": true'
Select-String -Path apps\quantops-api\runtime\logs\quantops_upstream_v12.jsonl -Pattern '\"timeout_detected\": true'
```

## Limits

- `frontend-start.log` is not a page-access log
- button-level interaction logging is still partial
- one page view can trigger multiple API calls, so always compare by `trace_id` and `path`
- stale data can still change what the user saw, so also check `build_status` and freshness fields in API payloads when needed

## Recommended Use

For a timeout report, use this order:

1. analyzer script
2. frontend `page_view` and `api_error`
3. QuantOps request row
4. QuantOps upstream V12 row
5. V12 request row

That order is usually enough to decide which layer owns the next fix.
