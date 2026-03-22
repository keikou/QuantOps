# Safe For Clean

This file lists generated or machine-local artifacts that are safe to delete when preparing a source-only package of this repository.

## Safe to delete

- `apps/quantops-frontend/.next/`
- `apps/quantops-frontend/node_modules/`
- `apps/quantops-frontend/tsconfig.tsbuildinfo`
- All `__pycache__/` directories under the repo
- All `*.pyc` files under the repo
- `apps/v12-api/.pytest_cache/`
- `apps/v12-api/runtime/`
- `apps/quantops-api/data/quantops.duckdb`
- `apps/quantops-api/.venv/`
- `apps/v12-api/.venv/`
- `source_of_truth/quantops_sprint3/services/v12-api/runtime/`

## Review before deleting

- `apps/quantops-frontend/.env.local`
- `apps/quantops-frontend/next.config.js.bak`
- Anything under `source_of_truth/quantops_sprint3/services/v12-api/runtime/sample_outputs/` if you want to keep historical example outputs

## Do not delete

- Source code
- Tests
- `package.json` and `package-lock.json`
- `requirements.txt`
- Checked-in config files such as `next.config.js`, `tsconfig.json`, `docker-compose.yml`, and `Dockerfile`
