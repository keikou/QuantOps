# Sprint6H-9.2.4 API Debug Hardening Report

## Changes
- Disabled frontend mock fallback by default.
- Disabled Next.js proxy mock fallback by default.
- Added structured client-side API error capture with:
  - request path/url
  - method
  - page
  - timeout/network/http/parse classification
  - status/statusText
  - response snippet
  - duration_ms
  - correlation/request id
- Added inline debug banner in dashboard shell.
- Preserved last successful query data during refresh failures.
- Reduced page-switch flicker by:
  - keeping previous React Query data
  - disabling refetch-on-mount on Overview / Portfolio / Positions
  - showing stale-value warning instead of swapping to mock/zero state
- Added QuantOps API request logging middleware with `X-Request-Id` propagation.
- Proxy now returns structured 502 details instead of silent mock fallback.

## Root-cause hypothesis for the ~10 second fallback flash
Most likely trigger chain:
1. page switch or remount
2. periodic refetch / revalidate fires later
3. fetch temporarily fails (timeout / 5xx / upstream unavailable / parse issue)
4. previous implementation returned mock data
5. UI briefly showed fixed mock KPIs

This sprint removes that behavior and keeps the last good value visible while surfacing the real error.

## Modified files
- `apps/quantops-frontend/src/lib/api/config.ts`
- `apps/quantops-frontend/src/lib/api/fetcher.ts`
- `apps/quantops-frontend/src/lib/api/error-store.ts`
- `apps/quantops-frontend/src/lib/api/query-provider.tsx`
- `apps/quantops-frontend/src/lib/api/hooks.ts`
- `apps/quantops-frontend/src/app/api/proxy/[...path]/route.ts`
- `apps/quantops-frontend/src/components/shared/api-debug-banner.tsx`
- `apps/quantops-frontend/src/components/layout/app-shell.tsx`
- `apps/quantops-frontend/src/features/overview/overview-page.tsx`
- `apps/quantops-frontend/src/features/portfolio/page.tsx`
- `apps/quantops-frontend/.env.local`
- `apps/quantops-frontend/.env.example`
- `apps/quantops-api/app/middleware/request_logging.py`
- `apps/quantops-api/app/main.py`

## Expected runtime behavior
- No automatic fallback to the fixed mock KPIs.
- When an API call fails, the page keeps the last successful values.
- A banner shows the failing route and details.
- Browser console logs the structured error object.
- Backend and proxy logs include request id and duration.
