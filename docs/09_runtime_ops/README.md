# Runtime Operations Index

Date: `2026-04-02`
Repo: `QuantOps_github`
Status: `initial_runtime_ops_index`

## Purpose

This folder is the canonical entrypoint for runtime operations, startup/stop behavior, health checks, and incident tracing.

It answers:

- how to start and stop the local stack
- where to look when runtime behavior appears wrong
- which docs to read first for health, logs, and correlation tracing

## Read First

1. `./current_runtime_ops.md`
2. `./incident_and_tracing.md`
3. `../ops-runbook.md`
4. `../correlation-logging-guide.md`
5. `../dev-startup.md`

## Runtime Ops Rule

Treat root-level ops docs as source material.
Treat this folder as the canonical entrypoint for deciding where runtime investigation should begin.

## Current Focus

- local stack should still be operated through the verified startup/stop path
- use runtime and correlation logs before guessing where a failure lives
- do not confuse stale chat guidance with runtime evidence
