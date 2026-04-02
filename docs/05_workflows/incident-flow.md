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
   - `../04_tasks/current.md`
   - `../Architect_alignment_resume_memo_2026-04-02.md`
3. if services matter, run the resume quickcheck and refresh helpers
4. run the narrowest relevant verifier first
5. only reopen a completed lane if the verifier shows a real regression
6. record the mismatch in a report or follow-up doc if it changes repo truth

## Rule

A stale conversation recommendation is not a regression.
A failed verifier or contradicted repo truth is a regression.
