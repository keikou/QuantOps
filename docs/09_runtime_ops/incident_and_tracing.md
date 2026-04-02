# Incident And Tracing Guide

Date: `2026-04-02`
Repo: `QuantOps_github`
Status: `current_incident_tracing_guide`

## Purpose

This file is the short entrypoint for runtime incident investigation.

## Read Next For Details

- `../correlation-logging-guide.md`
- `../ops-runbook.md`

## Investigation Order

1. confirm the symptom is real and current
2. confirm health and startup state
3. inspect runtime logs and correlation logs
4. match by `trace_id`, `request_id`, `session_id`, and `page_path`
5. identify whether the issue belongs to:
   - frontend
   - QuantOps API
   - V12
6. run the narrowest relevant verifier if the issue looks like a regression

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

## Historical Background

`SprintH_completion_report.md` remains useful as background for why the current runtime shape looks the way it does, but it should not be treated as the first incident guide.
