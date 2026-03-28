# CI Regression Packs

`Sprint6H-9.2.7.12` introduces a small, explicit regression surface for `apps/quantops-api` so CI protects the changes that stabilized the GUI and local runtime.

It also adds lightweight repo-level guard checks for startup hardening, proxy URL normalization, and frontend timeout policy.

`Sprint6H-9.2.8` extends this with a V12-side runtime observability pack that protects the event chain, planner truth, and bridge diagnostics contract.

## Pack Layout

### `truth`

Purpose:
Protect the read-path truth binding between QuantOps and upstream V12-derived values.

Tests:
- `app/tests/test_sprint6h9_2_7_2_command_center_live_execution_bridge.py`
- `app/tests/test_sprint6h9_2_7_equity_breakdown_truth.py`

Guards:
- execution live bridge prefers live metrics when stored summaries are empty
- equity and overview financial calculations stay bound to truth-based field derivation

### `stale`

Purpose:
Protect stale-first behavior for endpoints that should return cached data quickly instead of blocking on synchronous refresh.

Tests:
- `app/tests/test_sprint6h9_2_7_7_risk_snapshot_fast_path.py`
- `app/tests/test_sprint6h9_2_7_7_monitoring_fast_path.py`
- `app/tests/test_sprint6h9_2_7_7_gui_endpoint_fast_paths.py`

Guards:
- risk snapshot cached reads do not block on rebuild
- monitoring snapshot cached reads do not block on refresh
- upstream refresh logic remains parallelized
- overview, portfolio, and secondary analytics fast paths keep their short-TTL/stale-first behavior
- `analytics/equity-history` keeps its explicit freshness and stable/display contract shape

### `debug`

Purpose:
Protect the debug and provenance surfaces that operators use to validate derived state.

Tests:
- `app/tests/test_sprint6h9_2_7_9_debug_surfaces.py`
- `app/tests/test_sprint6h9_2_7_12_debug_contracts.py`
- `app/tests/test_sprint6h9_2_7_9b_execution_overview_debug.py`
- `app/tests/test_sprint6h9_2_7_9c_portfolio_debug.py`

Guards:
- debug routes keep the expected envelope shape
- overview, execution, risk, monitoring, and portfolio provenance remains explicit
- portfolio equity trace stays observable

## Local Usage

Run one pack:

```powershell
./test_bundle/scripts/run_quantops_api_regression_pack.ps1 -Pack truth
```

Run all packs:

```powershell
./test_bundle/scripts/run_quantops_api_regression_pack.ps1 -Pack all
```

The script creates an isolated DuckDB file under `runtime/` for each pack and sets `V12_MOCK_MODE=true` so the checks remain deterministic in CI and local development.

## V12 Runtime Observability Pack

Purpose:
Protect the runtime event chain and the operator-facing planner/bridge diagnostics derived from it.

Script:
- `test_bundle/scripts/run_v12_runtime_observability_pack.ps1`

Pack names:
- `blocked`
- `no_op`
- `degraded`
- `success`
- `all`

Coverage:
- blocked runtime cycles retain explicit reason codes
- no-decision cycles retain explicit zero-submit reasons
- stale-price and submitted-no-fill paths stay observable
- planner truth and bridge diagnostics stay aligned with runtime events

Run all:

```powershell
./test_bundle/scripts/run_v12_runtime_observability_pack.ps1 -Pack all
```

## Runtime Guard Checks

These checks are narrower than the pytest packs and are intended to protect operational hardening that is easy to regress accidentally in scripts or frontend config:

- `test_bundle/scripts/check_startup_script_hardening.ps1`
- `test_bundle/scripts/check_frontend_api_policy.ps1`

The guard workflow is:

- `.github/workflows/runtime-guard-checks.yml`
- `.github/workflows/optional-local-stack-smoke.yml`

Coverage:

- `CI-005` startup scripts still use local venv bootstrap, `ensurepip`, `python -m pip`, and `127.0.0.1`
- `CI-006` proxy/config base URLs still trim trailing slashes and default to `127.0.0.1`
- `CI-007` heavy frontend routes still keep their extended timeout budgets
- `CI-008` debug routes keep a stable envelope contract across risk, monitoring, execution, overview, and portfolio
- `CI-010` optional Windows smoke can run the real local startup path through GitHub Actions when invoked manually
- `QOPS-928-010` local startup smoke now asserts the runtime event chain and planner/bridge diagnostics after a real paper cycle

For the remaining SprintH closeout work, see:

- [sprinth-finish-plan.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/sprinth-finish-plan.md)
