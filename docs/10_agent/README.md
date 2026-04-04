# Agent Index

Date: `2026-04-02`
Repo: `QuantOps_github`
Status: `canonical_agent_entrypoint`

## Purpose

This folder is the canonical entrypoint for AI-agent-specific operating guidance.

It answers:

- what an AI should assume when resuming work
- how ChatGPT app and Codex should split responsibilities
- which constraints should be treated as current, not historical

## Read First

1. `./system_context.md`
2. `./rules.md`
3. `./capabilities.md`
4. `./constraints.md`
5. `./supporting_agent_docs.md`
6. `../Architect_alignment_resume_memo_2026-04-02.md`
7. `../Auto_resume_handover_2026-04-02.md`
8. `../chatgpt-codex-cowork.md`

## Current Agent Rule

Do not rely on thread memory when a canonical doc exists.

For current action, always align with:

- `../03_plans/current.md`
- `../04_tasks/current.md`

## Current Agent Focus

- the hardening/resume slice is already treated as sufficiently complete
- do not restart completed hardening packets unless a real regression is found
- if work continues, the default next candidate is `Strategy Evolution / Regime Adaptation Intelligence`

Historical note:

- `Execution Reality` was the earlier post-hardening default next candidate before the repo advanced through later lane checkpoints
