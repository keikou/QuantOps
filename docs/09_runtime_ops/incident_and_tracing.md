# Incident And Tracing Guide

Date: `2026-04-02`
Repo: `QuantOps_github`
Status: `current_incident_tracing_guide`

## Purpose

This file is the short entrypoint for runtime incident investigation.

## Read Next For Details

- `./supporting_runtime_ops.md`
- `../correlation-logging-guide.md`
- `../ops-runbook.md`

## Investigation Order

1. confirm the current repo state from canonical docs
2. confirm the symptom is real and current
3. confirm health and startup state
4. inspect runtime logs and correlation logs
5. match by `trace_id`, `request_id`, `session_id`, and `page_path`
6. identify whether the issue belongs to:
   - frontend
   - QuantOps API
   - V12
7. run the narrowest relevant verifier if the issue looks like a regression

## Current Important Log Surfaces

- `apps/quantops-api/runtime/logs/frontend_events.jsonl`
- `apps/quantops-api/runtime/logs/quantops_requests.jsonl`
- `apps/quantops-api/runtime/logs/quantops_upstream_v12.jsonl`
- `apps/v12-api/runtime/logs/v12_requests.jsonl`
- `runtime/logs/writer_cycles.jsonl`
- `runtime/logs/orchestrator_runs.jsonl`

## Current Rule

A conversation claim is not runtime evidence.

Runtime evidence comes from:

- health checks
- log rows
- correlation ids
- verifier failures

Current docs-first runtime route:

- `../00_index/README.md`
- `../03_plans/current.md`
- `../04_tasks/current.md`
- `../10_agent/ai_docs_operating_loop.md`

## Historical Background

`SprintH_completion_report.md` remains useful as background for why the current runtime shape looks the way it does, but it should not be treated as the first incident guide.
