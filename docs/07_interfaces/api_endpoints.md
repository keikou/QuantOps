# API Endpoints

Date: `2026-04-05`
Repo: `QuantOps_github`
Status: `initial_api_endpoint_index`

## Purpose

This file is the short routing index for the current operator-visible API endpoint families.

## Current Endpoint Families

### Base Health

- `GET /system/health`
- `GET /health`

### Hardening / Resume / Operator Bundles

- `GET /system/hardening-status`
- `GET /system/hardening-evidence-snapshot/latest`
- `GET /system/hardening-architect-handoff/latest`
- `GET /system/resume-operator-packet/latest`
- `GET /system/operator-diagnostic-bundle`
- `GET /system/recovery-replay-diagnostic-bundle`

### Learning And Policy

- `GET /system/learning-feedback/latest`
- `GET /system/learning-policy-updates/latest`
- `GET /system/learning-policy-state/latest`
- `GET /system/learning-resolved-overrides/latest`
- `GET /system/learning-applied-consumption/latest`
- `GET /system/policy-effectiveness/latest`
- `GET /system/policy-tuning/latest`
- `GET /system/meta-policy-state/latest`
- `GET /system/meta-policy-consumption/latest`
- `GET /system/meta-policy-effectiveness/latest`

### Deployment / Capital / Meta-Portfolio

- `GET /system/deployment-rollout-decision/latest`
- `GET /system/deployment-rollout-candidate-docket/latest`
- `GET /system/deployment-rollout-state/latest`
- `GET /system/deployment-rollout-consumption/latest`
- `GET /system/deployment-rollout-effectiveness/latest`
- `GET /system/live-capital-control/latest`
- `GET /system/live-capital-adjustment-decision/latest`
- `GET /system/live-capital-control-state/latest`
- `GET /system/live-capital-control-consumption/latest`
- `GET /system/live-capital-control-effectiveness/latest`
- `GET /system/meta-portfolio-allocation/latest`
- `GET /system/meta-portfolio-decision/latest`
- `GET /system/meta-portfolio-state/latest`
- `GET /system/meta-portfolio-flow/latest`
- `GET /system/meta-portfolio-efficiency/latest`

### Strategy Evolution / Regime Adaptation

- `GET /system/regime-state/latest`
- `GET /system/strategy-regime-compatibility/latest`
- `GET /system/strategy-gating-decision/latest`
- `GET /system/regime-transition-detection/latest`
- `GET /system/strategy-survival-analysis/latest`

### Autonomous Alpha Expansion / Strategy Generation

- `GET /system/alpha-discovery-candidates/latest`
- `GET /system/alpha-validation-results/latest`
- `GET /system/alpha-admission-decision/latest`
- `GET /system/alpha-lifecycle-state/latest`
- `GET /system/alpha-inventory-health/latest`
- `GET /system/alpha-generation-agenda/latest`
- `GET /system/alpha-experiment-docket/latest`
- `GET /system/alpha-replacement-decision/latest`
- `GET /system/alpha-replacement-state/latest`
- `GET /system/alpha-expansion-effectiveness/latest`
- `GET /system/alpha-runtime-deployment-candidates/latest`
- `GET /system/alpha-runtime-governance-feedback/latest`
- `GET /system/alpha-runtime-rollback-response/latest`
- `GET /system/alpha-runtime-champion-challenger/latest`
- `GET /system/alpha-runtime-expansion-effectiveness/latest`
- `GET /system/alpha-next-cycle-learning-input/latest`
- `GET /system/alpha-next-cycle-policy-bridge/latest`
- `GET /system/alpha-regime-adaptation-input/latest`
- `GET /system/alpha-universe-refresh-priorities/latest`
- `GET /system/alpha-expansion-learning-effectiveness/latest`
- `GET /system/alpha-promotion-bridge/latest`
- `GET /system/alpha-family-capital-intent/latest`
- `GET /system/alpha-portfolio-intake-queue/latest`
- `GET /system/alpha-governed-universe-state/latest`
- `GET /system/alpha-strategy-factory-readiness/latest`

### Alpha Synthesis / Structural Discovery

- `GET /system/alpha-synthesis-candidates/latest`
- `GET /system/alpha-structure-search-state/latest`
- `GET /system/alpha-novelty-evaluation/latest`
- `GET /system/alpha-expression-library/latest`
- `GET /system/alpha-synthesis-effectiveness/latest`
- `GET /system/alpha-parent-candidates/latest`
- `GET /system/alpha-mutation-candidates/latest`
- `GET /system/alpha-crossover-candidates/latest`
- `GET /system/alpha-evolution-search-state/latest`
- `GET /system/alpha-evolution-effectiveness/latest`
- `GET /system/alpha-regime-synthesis-agenda/latest`
- `GET /system/alpha-regime-targeted-candidates/latest`
- `GET /system/alpha-regime-fit-evaluation/latest`
- `GET /system/alpha-regime-expression-map/latest`
- `GET /system/alpha-regime-synthesis-effectiveness/latest`
- `GET /system/alpha-hypothesis-agenda/latest`
- `GET /system/alpha-llm-hypothesis-prompts/latest`
- `GET /system/alpha-llm-translation-candidates/latest`
- `GET /system/alpha-hypothesis-critique/latest`
- `GET /system/alpha-hypothesis-effectiveness/latest`
- `GET /system/alpha-hypothesis-feedback-queue/latest`
- `GET /system/alpha-hypothesis-prompt-tuning/latest`
- `GET /system/alpha-synthesis-policy-updates/latest`
- `GET /system/alpha-feedback-learning-state/latest`
- `GET /system/alpha-feedback-optimization-effectiveness/latest`

### Alpha Evaluation / Selection

- `GET /system/alpha-evaluation/latest`
- `GET /system/alpha-decay-analysis/latest`
- `GET /system/alpha-correlation-matrix/latest`
- `GET /system/alpha-robustness-ranking/latest`
- `GET /system/alpha-selection-decisions/latest`
- `POST /system/alpha-evaluation/run`
- `GET /system/alpha-evaluation/candidate/{alpha_id}`
- `POST /system/alpha-walk-forward/run`
- `GET /system/alpha-walk-forward/latest`
- `GET /system/alpha-walk-forward/candidate/{alpha_id}`
- `GET /system/alpha-oos-validation/latest`
- `GET /system/alpha-validation-decisions/latest`
- `GET /system/alpha-validation-failures/latest`
- `POST /system/alpha-factor-attribution/run`
- `GET /system/alpha-factor-attribution/latest`
- `GET /system/alpha-factor-attribution/candidate/{alpha_id}`
- `GET /system/alpha-factor-exposure/latest`
- `GET /system/alpha-residual-alpha/latest`
- `GET /system/alpha-economic-risk/latest`
- `GET /system/alpha-factor-concentration/latest`
- `GET /system/alpha-economic-meaning/latest`
- `GET /system/alpha-factor-attribution/ensemble/{ensemble_id}`
- `POST /system/alpha-capacity/run`
- `GET /system/alpha-capacity/latest`
- `GET /system/alpha-capacity/candidate/{alpha_id}`
- `GET /system/alpha-crowding/latest`
- `GET /system/alpha-impact/latest`
- `GET /system/alpha-capacity/ensemble/{ensemble_id}`
- `POST /system/alpha-dynamic-weights/run`
- `GET /system/alpha-dynamic-weights/latest`
- `GET /system/alpha-dynamic-weights/ensemble/{ensemble_id}`
- `GET /system/alpha-weight-adjustments/latest`
- `GET /system/alpha-weight-drift/latest`
- `GET /system/alpha-weight-constraints/latest`
- `GET /system/alpha-weight-proposals/latest`
- `POST /system/alpha-kill-switch/run`
- `GET /system/alpha-kill-switch/latest`
- `GET /system/alpha-kill-switch/alpha/{alpha_id}`
- `GET /system/alpha-retirement/latest`
- `GET /system/alpha-retirement/alpha/{alpha_id}`
- `GET /system/alpha-deactivation-decisions/latest`
- `GET /system/alpha-kill-switch-events/latest`
- `POST /system/alpha-kill-switch/override`
- `POST /system/alpha-feedback-loop/run`
- `GET /system/alpha-feedback-loop/latest`
- `GET /system/alpha-learning-signals/latest`
- `GET /system/alpha-generation-priors/latest`
- `GET /system/alpha-family-performance/latest`
- `GET /system/alpha-policy-recommendations/latest`
- `GET /system/alpha-feedback-loop/alpha/{alpha_id}`
- `GET /system/alpha-feedback-loop/family/{family_id}`
- `POST /system/alpha-policy-recommendations/apply`

## Read Next

1. `./endpoint_contract_matrix.md`
2. `./runtime_payloads.md`
3. `./event_contracts.md`

## Rule

Use this file to find endpoint families quickly.
Use `endpoint_contract_matrix.md` when you need the contract role of a specific endpoint.
