# V8-based route prefix fix

This build keeps the original v8 `app/api/router.py` intact and only fixes the four completion-check route modules.

## Root cause
In v8, `router.py` already mounts these modules with prefixes:
- `/analytics`
- `/monitoring`
- `/alerts`
- `/scheduler`

The route files also had their own prefixes, causing double-prefixed paths such as:
- `/api/v1/analytics/analytics/summary`

## Fix
Replaced these route modules with prefix-free versions:
- `app/api/routes/analytics.py`
- `app/api/routes/monitoring.py`
- `app/api/routes/alerts.py`
- `app/api/routes/scheduler.py`

## Intended final paths
- `/api/v1/analytics/summary`
- `/api/v1/monitoring/system`
- `/api/v1/alerts`
- `/api/v1/scheduler/jobs`
