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

## Read Next

1. `./endpoint_contract_matrix.md`
2. `./runtime_payloads.md`
3. `./event_contracts.md`

## Rule

Use this file to find endpoint families quickly.
Use `endpoint_contract_matrix.md` when you need the contract role of a specific endpoint.
