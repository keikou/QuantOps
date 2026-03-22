from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import admin, alerts, analytics, approval, control, dashboard, governance, health, incidents, monitoring, portfolio, risk, scheduler

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["scheduler"])
api_router.include_router(control.router, prefix="/control", tags=["control"])
api_router.include_router(risk.router, prefix="/risk", tags=["risk"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(governance.router, prefix="/governance", tags=["governance"])
api_router.include_router(approval.router, prefix="/approval", tags=["approval"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
