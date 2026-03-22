from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import admin, alerts, analytics, approval, acceptance, auth, command_center, config, control, dashboard, execution, governance, health, incidents, monitoring, modes, portfolio, risk, scheduler, strategy

api_router = APIRouter()
api_router.include_router(health.router, tags=['health'])
api_router.include_router(auth.router, prefix='/auth', tags=['auth'])
api_router.include_router(dashboard.router, prefix='/dashboard', tags=['dashboard'])
api_router.include_router(portfolio.router, prefix='/portfolio', tags=['portfolio'])
api_router.include_router(scheduler.router, prefix='/scheduler', tags=['scheduler'])
api_router.include_router(control.router, prefix='/control', tags=['control'])
api_router.include_router(risk.router, prefix='/risk', tags=['risk'])
api_router.include_router(analytics.router, prefix='/analytics', tags=['analytics'])
api_router.include_router(execution.router, prefix='/execution', tags=['execution'])
api_router.include_router(modes.router, prefix='/modes', tags=['modes'])
api_router.include_router(acceptance.router, prefix='/acceptance', tags=['acceptance'])
api_router.include_router(monitoring.router, prefix='/monitoring', tags=['monitoring'])
api_router.include_router(alerts.router, prefix='/alerts', tags=['alerts'])
api_router.include_router(governance.router, prefix='/governance', tags=['governance'])
api_router.include_router(approval.router, prefix='/approval', tags=['approval'])
api_router.include_router(incidents.router, prefix='/incidents', tags=['incidents'])
api_router.include_router(admin.router, prefix='/admin', tags=['admin'])

api_router.include_router(strategy.router, prefix='/strategy', tags=['strategy'])
api_router.include_router(config.router, prefix='/config', tags=['config'])
api_router.include_router(command_center.router, prefix='/command-center', tags=['command-center'])
