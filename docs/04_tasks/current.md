# Current Tasks

Date: `2026-04-26`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `alpha_factory_governance_operator_control`
Status: `srh01_active`

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

- establish `System Reliability / Runtime Hardening`
- implement `SRH-01: Runtime Health & Degradation Control`

Current architect-selected candidate:

- `System Reliability / Runtime Hardening`
- current implementation boundary = `SRH-01`
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

- "can runtime health be observed and scored?"
- "can degradation be detected and classified?"
- "can safe mode and recovery actions be persisted?"

This is the next lane beyond the completed hardening/resume slice, but it is no longer the older `Execution Reality` default.

## Next Candidate Options

1. `Alpha Evaluation / Selection Intelligence`
   - selected as the next top-level lane from the current repo truth
2. `Alpha Synthesis / Structural Discovery Intelligence`
   - now treated as checkpoint-complete input, not the active lane
3. `Autonomous Alpha Expansion / Strategy Generation Intelligence`
   - now treated as checkpoint-complete input, not the active lane
4. `Strategy Evolution / Regime Adaptation Intelligence`
   - now treated as checkpoint-complete input, not the active lane
5. `Deployment / Rollout Intelligence`
   - now treated as checkpoint-complete input, not the active lane
6. `Live Capital Control / Adaptive Runtime Allocation`
   - now treated as checkpoint-complete input, not the active lane

## Current Recommendation

Use `SRH-01` as the current active task.

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
- replaying `AAE-01` through `AAE-05` without a real regression
- extending `AAE` to fake generator-core completion
- replaying `ASD-01` through `ASD-05` without a real regression
- inventing `ASD-06` before next-lane reselection
- using portfolio allocation as a substitute for alpha evaluation
- reopening `AFG-01` through `AFG-05` after Architect marked AFG lane frozen

## Inputs To Read Before Acting

1. `../00_index/README.md`
2. `../Cross_thread_resume_handover_2026-04-24.md`
3. `../Auto_resume_handover_2026-04-24.md`
4. `../Autonomous_alpha_expansion_strategy_generation_intelligence_checkpoint_v1.md`
5. `../Alpha_synthesis_structural_discovery_intelligence_checkpoint_v1.md`
6. `../AES-01_GitHub_Issues.md`
7. `../AES_Threshold_Tuning_Strategy.md`
8. `../AES-02_Walk_Forward_Validation_Design.md`
9. `../AES-03_Alpha_Ensemble_Selection_Engine_Design.md`
10. `../AES-03_GitHub_Issues_Implementation.md`
11. `../AES-03_Weight_Optimization_Algorithms.md`
12. `../AES-03_Portfolio_Integration_MPI_LCC.md`
13. `../AES-04_Economic_Meaning_Factor_Attribution_Design.md`
14. `../AES-05_Capacity_Crowding_Risk_Engine.md`
15. `../AES-06_Dynamic_Alpha_Weighting_Engine.md`
16. `../AES-07_Alpha_Kill_Switch_Retirement_Engine.md`
17. `../AES-08_Self_Improving_Alpha_Loop.md`
18. `../07_interfaces/aes_alpha_evaluation_contracts.md`

## Expected Output Of The Next Task

The current lane follow-up should produce:

- one packet plan doc
- one verifier script
- runtime health signal, score, degradation, control, and recovery surfaces

Current `SRH-01` outputs now planned:

- `docs/System_reliability_runtime_hardening_packet01_plan.md`
- `test_bundle/scripts/verify_runtime_health_packet01.py`
- `POST /system/runtime-health/ingest`
- `GET /system/runtime-health/latest`
- `GET /system/runtime-health/components`
- `GET /system/runtime-health/signals/latest`
- `GET /system/degradation/latest`
- `GET /system/runtime-control/actions/latest`
- `POST /system/control/safe-mode`
- `GET /system/runtime-recovery/latest`

## Single-Block Resume Note

```text
Current task is not another hardening packet replay, not another Execution Reality packet, not another Governance -> Runtime Control packet, not another Portfolio Intelligence packet, not another Alpha / Strategy Selection Intelligence packet, not another Research / Promotion Intelligence packet, and not another active DRI, LCC, MPI, SERI, AAE, ASD, AES, ORC, or AFG packet. Current task is `SRH-01`, so completed `AES-01` through `AES-08`, `ORC-01` through `ORC-05`, and frozen `AFG-01` through `AFG-05` work should be treated as input lanes and not replayed unless a real regression is found.
```
