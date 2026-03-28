from __future__ import annotations

from fastapi import FastAPI
from ai_hedge_bot.app.startup import lifespan
from ai_hedge_bot.middleware.request_logging import RequestLoggingMiddleware
from ai_hedge_bot.api.routes import (
    system,
    market,
    signals,
    portfolio,
    orchestrator,
    runtime,
    scheduler,
    execution,
    analytics,
    dashboard,
    strategy,
    research_factory,
    alpha,
    risk,
    governance,
    analytics_sprint5c,
    orchestrator_sprint5c,
    runtime_sprint5d,
    acceptance,
    incidents,
    analytics_shadow,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title='AI Hedge Bot V12 PhaseH Sprint5 Integrated',
        version='0.12.0-phaseh-sprint5-integrated',
        lifespan=lifespan,
    )
    app.add_middleware(RequestLoggingMiddleware)
    for router in (
        system.router,
        market.router,
        signals.router,
        portfolio.router,
        orchestrator.router,
        runtime.router,
        scheduler.router,
        execution.router,
        analytics.router,
        dashboard.router,
        strategy.router,
        research_factory.router,
        alpha.router,
        risk.router,
        governance.router,
        analytics_sprint5c.router,
        orchestrator_sprint5c.router,
        runtime_sprint5d.router,
        acceptance.router,
        incidents.router,
        analytics_shadow.router,
    ):
        app.include_router(router)
    return app


app = create_app()
