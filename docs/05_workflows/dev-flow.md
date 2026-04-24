# Development Flow

Date: `2026-04-02`
Status: `canonical`

## When To Use

Use this workflow when starting or continuing repo work.

## Flow

1. read `../00_index/README.md`
2. read `../10_agent/ai_docs_operating_loop.md`
3. read `../03_plans/current.md`
4. read `../04_tasks/current.md`
5. confirm branch and worktree state
6. read the relevant plan/report/interface docs for the active lane
7. decide whether the task is:
   - new lane work
   - regression verification
   - docs restructuring
8. implement the smallest high-signal unit first
9. add or run the narrowest relevant verifier
10. update the docs that future threads will actually read

## Guardrails

- do not reopen completed hardening packets unless a real regression is found
- do not treat old architect guidance as current if the repo state has moved on
- prefer canonical entrypoint docs over scattered thread memory
- route root-level workflow docs through `supporting_workflows.md` before moving them physically
- if the current lane is `AAE`, start from the docs-ready task and contract docs before touching code
