# Current Tasks

Date: `2026-04-24`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `autonomous_alpha_expansion_strategy_generation_intelligence`
Status: `aae02_active`

## Purpose

This file is the canonical current-task entrypoint for both humans and AI agents.

It answers:

- what is active now
- what is explicitly not active now
- what should happen next if work resumes

## Current State

The current hardening slice is already treated as sufficiently complete.

That means:

- do not restart `Cross-Phase Acceptance`
- do not reopen `Recovery / Replay Confidence`
- do not deepen resume/handover packaging unless a real regression is found

## Active Task

Current top task:

- establish `Autonomous Alpha Expansion / Strategy Generation Intelligence`
- implement `AAE-02: Alpha Generation Agenda & Replacement Loop`

Current architect-selected candidate:

- `Autonomous Alpha Expansion / Strategy Generation Intelligence`
- current implementation boundary = `AAE-02`
- current dependency 1 = `Research / Promotion Intelligence v1 checkpoint through RPI-06`
- current dependency 2 = `Alpha / Strategy Selection Intelligence v1 checkpoint through ASI-05`
- current dependency 3 = `Portfolio Intelligence v1 checkpoint through PI-05`
- current dependency 4 = `Governance -> Runtime Control v1 checkpoint through C6`
- current dependency 5 = `Execution Reality v1 checkpoint through Packet 10`
- current dependency 6 = `System-Level Learning / Feedback Integration v1 checkpoint through SLLFI-05`
- current dependency 7 = `Policy Optimization / Meta-Control Learning v1 checkpoint through PO-05`
- current dependency 8 = `Deployment / Rollout Intelligence v1 checkpoint through DRI-05`
- current dependency 9 = `Live Capital Control / Adaptive Runtime Allocation v1 checkpoint through LCC-05`
- current dependency 10 = `Meta Portfolio Intelligence / Cross-Strategy Capital Allocation v1 checkpoint through MPI-05`
- current dependency 11 = `Strategy Evolution / Regime Adaptation Intelligence v1 checkpoint through SERI-05`

## Why This Is The Active Task

Architect now treats `Strategy Evolution / Regime Adaptation Intelligence v1` as checkpoint-complete.

The next question is:

- "what should be generated next when inventory replacement pressure is high?"
- "which alpha experiments are actually ready to run?"
- "which validated candidates should replace fragile inventory now?"

This is the next lane beyond the completed hardening/resume slice, but it is no longer the older `Execution Reality` default.

## Next Candidate Options

1. `Autonomous Alpha Expansion / Strategy Generation Intelligence`
   - selected by architect as the next top-level lane
2. `Strategy Evolution / Regime Adaptation Intelligence`
   - now treated as checkpoint-complete input, not the active lane
3. `Deployment / Rollout Intelligence`
   - now treated as checkpoint-complete input, not the active lane
4. `Live Capital Control / Adaptive Runtime Allocation`
   - now treated as checkpoint-complete input, not the active lane
5. `Meta Portfolio Intelligence / Cross-Strategy Capital Allocation`
   - now treated as checkpoint-complete input, not the active lane

## Current Recommendation

Use `AAE-02` as the current active task.

## Explicit Non-Tasks

These are not current tasks:

- replaying old hardening packet order
- creating another acceptance-only lane
- re-packaging resume docs again
- reopening `Phase1` to `Phase7` closure work
- deepening `Execution Reality`
- deepening `Governance -> Runtime Control`
- deepening `Portfolio Intelligence`
- deepening `Alpha / Strategy Selection Intelligence`
- deepening `Research / Promotion Intelligence`
- reopening `SLLFI` as the active packet lane
- reopening `Policy Optimization` as the active packet lane
- continuing `DRI`, `LCC`, `MPI`, or `SERI` packet expansion as the active lane

## Inputs To Read Before Acting

1. `../00_index/README.md`
2. `../Cross_thread_resume_handover_2026-04-24.md`
3. `../Auto_resume_handover_2026-04-24.md`
4. `../Strategy_evolution_regime_adaptation_intelligence_checkpoint_v1.md`
5. `../Autonomous_alpha_expansion_strategy_generation_intelligence_packet02_plan.md`
6. `../07_interfaces/aae_autonomous_alpha_expansion_contracts.md`

## Expected Output Of The Next Task

The current lane follow-up should produce:

- one packet plan doc
- one verifier script
- generation agenda, experiment docket, replacement decision, replacement state, and expansion-effectiveness surfaces

Current `AAE-02` outputs now available:

- `docs/Autonomous_alpha_expansion_strategy_generation_intelligence_packet02_plan.md`
- `test_bundle/scripts/verify_autonomous_alpha_expansion_strategy_generation_intelligence_packet02.py`
- `GET /system/alpha-generation-agenda/latest`
- `GET /system/alpha-experiment-docket/latest`
- `GET /system/alpha-replacement-decision/latest`
- `GET /system/alpha-replacement-state/latest`
- `GET /system/alpha-expansion-effectiveness/latest`

## Single-Block Resume Note

```text
Current task is not another hardening packet, not another Execution Reality packet, not another Governance -> Runtime Control packet, not another Portfolio Intelligence packet, not another Alpha / Strategy Selection Intelligence packet, not another Research / Promotion Intelligence packet, and not another active DRI, LCC, MPI, or SERI packet. Current task is `AAE-02` so the system can decide what to generate next, which experiments are ready, and which candidates should replace fragile inventory after AAE-01 visibility was established.
```
