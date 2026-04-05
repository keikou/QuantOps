# Incident Flow

Date: `2026-04-02`
Status: `canonical`

## When To Use

Use this workflow when the repo, runtime, or docs state appears inconsistent, broken, or stale.

## Flow

1. identify whether the problem is:
   - code/runtime regression
   - stale docs/reference problem
   - resume-state mismatch
2. check the current canonical entrypoints:
   - `../00_index/README.md`
   - `../10_agent/ai_docs_operating_loop.md`
   - `../03_plans/current.md`
   - `../04_tasks/current.md`
   - `../11_reports/current_status.md`
3. decide whether the mismatch is route drift, docs drift, or real runtime break
4. if services matter, run the resume quickcheck and refresh helpers
5. run the narrowest relevant verifier first
6. only reopen a completed lane if the verifier shows a real regression
7. record the mismatch in a report or follow-up doc if it changes repo truth

## Rule

A stale conversation recommendation is not a regression.
A failed verifier or contradicted repo truth is a regression.
