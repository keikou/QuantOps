from __future__ import annotations

from fastapi import APIRouter
from ai_hedge_bot.dashboard import research_dashboard, portfolio_dashboard, execution_dashboard, global_dashboard, alpha_factory_dashboard

router = APIRouter(prefix='/dashboard', tags=['dashboard'])

@router.get('/research')
def dashboard_research() -> dict:
    return research_dashboard.build()

@router.get('/portfolio')
def dashboard_portfolio() -> dict:
    return portfolio_dashboard.build()

@router.get('/execution')
def dashboard_execution() -> dict:
    return execution_dashboard.build()

@router.get('/global')
def dashboard_global() -> dict:
    return global_dashboard.build()

@router.get('/alpha-factory')
def dashboard_alpha_factory() -> dict:
    return alpha_factory_dashboard.build()
