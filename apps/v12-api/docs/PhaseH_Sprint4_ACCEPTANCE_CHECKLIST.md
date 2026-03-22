# PhaseH Sprint4 Acceptance Checklist

## Functional
- Alpha registry exists and is queryable.
- Alpha generate/test/evaluate endpoints are available.
- Alpha ranking and alpha library endpoints are available.
- Alpha factory dashboard is available.
- Global dashboard includes alpha cards.
- OpenAPI includes sprint4 alpha routes.

## Verification
- `python -m pytest -q`
- `powershell -ExecutionPolicy Bypass -File .\scripts\check_phaseh_sprint4.ps1`
- `powershell -ExecutionPolicy Bypass -File .\scripts\check_phaseh_sprint4.ps1 -StartLocalApi`
- `docker compose up --build`
