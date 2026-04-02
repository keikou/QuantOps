# Working Assumptions

Date: `2026-04-02`
Repo: `QuantOps_github`
Status: `current_working_assumptions`

## Repo Assumptions

- use `127.0.0.1` for local service checks
- prefer repo truth and verifiers over thread memory
- treat root-level historical docs as context unless `03_plans/current.md` or `04_tasks/current.md` says otherwise

## Architecture Assumptions

- truth semantics and display semantics must not be mixed casually
- stable summaries and live feeds should remain explicitly separated
- UI should prefer explicit contract fields over hidden local recomputation

## Process Assumptions

- Codex should inspect, implement, verify, and update docs
- ChatGPT app should be used for design framing, prioritization, and architect discussion
- major conclusions should be written back into docs rather than left in conversation history

## Planning Assumptions

- do not rename the current track to `Phase8` unless architect changes guidance
- do not reopen completed hardening packets unless a real regression is found
- the current hardening/resume slice is already treated as sufficiently complete
- the next likely lane is `Execution Reality`

## Investigation Assumptions

- a stale recommendation in a chat is not a repo regression
- a failed verifier or contradicted repo truth is a regression
- when in doubt, read the canonical docs index first, then run the narrowest relevant verifier
