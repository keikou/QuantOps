# Runtime Notes

This package specifically addresses the previously observed startup blocker:

- missing `apps/v12-api/Dockerfile`
- missing `apps/quantops-api/Dockerfile`

Added in this runtime bundle:
- `apps/v12-api/Dockerfile`
- `apps/v12-api/requirements.txt`
- `apps/quantops-api/Dockerfile`
- `apps/quantops-api/requirements.txt`
- root `docker-compose.full.yml`
- root `.env.full.example`

If imports fail after boot, the next fixes should target:
1. Python package path conflicts
2. missing route/service imports
3. repository wiring for real data
