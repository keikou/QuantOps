# V12 PhaseD Ultimate Verification Guide

## Docker one-command verification
From `Source_Code`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_phase_d_docker.ps1
```

This performs:
1. `docker compose up -d --build`
2. wait for `GET /health`
3. `POST /run-once`
4. `POST /runner/run-cycle` multiple times
5. fetch execution analytics endpoints
6. save responses into `runtime/verification_logs`
7. export docker compose logs
8. shut containers down

## Direct cycle verification against a running API

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_phase_d_cycle.ps1
```

## Evidence files
Look in:

```text
Source_Code\runtime\verification_logs
```

You should see JSON files for `run-once`, `runner-cycle`, shadow orders, fills, lifecycle, latency, quality, and slippage.
