# Operations Runbook

This document is the practical operator guide for starting, stopping, checking, and troubleshooting the local QuantOps stack.

For developer-oriented startup notes, also see:

- [dev-startup.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/dev-startup.md)

## Stack Components

- V12 API
  - port `8000`
  - health: `http://127.0.0.1:8000/system/health`
- QuantOps API
  - port `8010`
  - health: `http://127.0.0.1:8010/api/v1/health`
- QuantOps Frontend
  - port `3000`
  - root: `http://127.0.0.1:3000/`

Use `127.0.0.1`, not `localhost`, to match the verified local configuration.

## Startup Scripts

### Full stack

- [run_all.cmd](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/run_all.cmd)
  - dev stack
- [run_all_prod.cmd](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/run_all_prod.cmd)
  - production-style stack
- [run_all_prod_fast.cmd](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/run_all_prod_fast.cmd)
  - production-style stack with frontend build and QuantOps migrate skipped

### Individual services

- [start_v12_api.cmd](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/start_v12_api.cmd)
- [start_quantops_api.cmd](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/start_quantops_api.cmd)
- [start_frontend.cmd](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/start_frontend.cmd)
- [start_frontend_prod.cmd](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/start_frontend_prod.cmd)

### Important note on frontend production

- [start_frontend_prod.cmd](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/start_frontend_prod.cmd) with `--skip-build` requires an existing `.next` build.
- If `.next` does not exist, use the normal script without `--skip-build`.

## Stop Scripts

### Full stack

- [stop_all.cmd](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/stop_all.cmd)
- [stop_all_prod.cmd](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/stop_all_prod.cmd)

Both call:

- [stop_local_stack.ps1](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/test_bundle/scripts/stop_local_stack.ps1)

### Individual services

- [stop_v12_api.cmd](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/stop_v12_api.cmd)
- [stop_quantops_api.cmd](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/stop_quantops_api.cmd)
- [stop_frontend.cmd](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/stop_frontend.cmd)

These use:

- [stop_ports.ps1](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/test_bundle/scripts/stop_ports.ps1)

`stop_ports.ps1` stops:

- listener processes on known ports
- matching `uvicorn` / `next` child processes by command pattern
- matching parent `cmd.exe` launcher processes when needed

This is important because some failed starts can leave a non-listening process holding files like DuckDB.

## Recommended Operations

### Start dev stack

```bat
run_all.cmd
```

### Start production-style stack

```bat
run_all_prod.cmd
```

### Start fast production-style stack

```bat
run_all_prod_fast.cmd
```

### Stop everything

```bat
stop_all.cmd
```

or

```bat
stop_all_prod.cmd
```

### Restart one service

Example: restart QuantOps API only

```bat
stop_quantops_api.cmd
start_quantops_api.cmd
```

## Health Checks

After startup, verify:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/system/health
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8010/api/v1/health
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:3000/
```

Expected:

- `8000`: `200`
- `8010`: `200`
- `3000`: `200`

## Log Locations

### Dev stack

- `test_bundle/artifacts/recheck_dev_logs/`

Typical files:

- `frontend-dev.log`
- `quantops.log`
- `v12.log`
- `pids.json`

### Production-style stack

- `test_bundle/artifacts/recheck_start_logs_2/`

Typical files:

- `frontend-start.log`
- `quantops.log`
- `v12.log`
- `pids.json`

### Writer observability

- `runtime/logs/writer_cycles.jsonl`
- `runtime/logs/orchestrator_runs.jsonl`

## Common Failure Modes

### V12 fails with DuckDB file-in-use error

Symptom:

- V12 startup fails
- log contains `Cannot open file ... analytics.duckdb`

Likely cause:

- a previous `uvicorn` process or parent launcher `cmd.exe` is still alive

Action:

1. Run [stop_v12_api.cmd](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/stop_v12_api.cmd)
2. Re-check port `8000`
3. Retry [start_v12_api.cmd](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/start_v12_api.cmd)

### Frontend production fails with missing `.next`

Symptom:

- `Could not find a production build in the '.next' directory`

Cause:

- `start_frontend_prod.cmd --skip-build` used without an existing build

Action:

- run [start_frontend_prod.cmd](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/start_frontend_prod.cmd) without `--skip-build`

### Ports look down immediately after a stop script returns

This is expected in some cases for a few seconds because child processes are still exiting.

Action:

- wait `5-10s`
- re-check the health URLs

## Verified Behavior

The following were recently verified on the real local stack:

- `run_all.cmd` starts all three services successfully
- `run_all_prod.cmd` starts all three services successfully
- `run_all_prod_fast.cmd` starts all three services successfully
- `start_v12_api.cmd` starts V12 successfully
- `start_quantops_api.cmd` starts QuantOps API successfully when V12 is already up
- `start_frontend.cmd` starts the frontend dev server successfully
- `start_frontend_prod.cmd` starts the frontend production server successfully
- `stop_all*.cmd` and `stop_*.cmd` stop the intended services successfully

## Related Docs

- [dev-startup.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/dev-startup.md)
- [ci_regression_packs.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/ci_regression_packs.md)
- [timeout-roadmap.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/timeout-roadmap.md)
