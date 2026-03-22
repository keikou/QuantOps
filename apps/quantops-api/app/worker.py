from __future__ import annotations

from app.db.init_db import init_db

import asyncio
import logging

from app.core.config import get_settings
from app.core.deps import get_analytics_repository, get_risk_repository, get_v12_client
from app.services.analytics_service import AnalyticsService
from app.services.risk_service import RiskService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("quantops-paper-worker")


async def main() -> None:
    init_db()
    settings = get_settings()
    v12_client = get_v12_client()
    risk_service = RiskService(v12_client, get_risk_repository())
    analytics_service = AnalyticsService(v12_client, get_analytics_repository())

    interval = settings.risk_refresh_interval_seconds

    logger.info(
        "starting worker interval=%ss mock_mode=%s",
        interval,
        settings.v12_mock_mode,
    )

    while True:
        try:
            trading_state = get_risk_repository().get_trading_state().get("trading_state", "running")
            if str(trading_state).lower() in {"halted", "paused"}:
                logger.info("paper cycle skipped trading_state=%s", trading_state)
                snapshot = await risk_service.refresh_snapshot()
                analytics = await analytics_service.refresh()
                logger.info("risk/analytics refreshed while blocked alert=%s gross=%.4f net=%.4f alpha_count=%s", snapshot.get("alert_state"), float(snapshot.get("gross_exposure", 0.0)), float(snapshot.get("net_exposure", 0.0)), analytics.get("alpha_count"))
                await asyncio.sleep(interval)
                continue

            runtime_result = await v12_client.run_runtime_once("paper")
            run_id = runtime_result.get("run_id") or (runtime_result.get("result") or {}).get("run_id")
            logger.info(
                "paper cycle submitted run_id=%s status=%s endpoint=%s",
                run_id,
                runtime_result.get("status"),
                runtime_result.get("_endpoint"),
            )

            snapshot = await risk_service.refresh_snapshot()
            analytics = await analytics_service.refresh()

            logger.info(
                "paper cycle finished run_id=%s risk_alert=%s gross=%.4f net=%.4f alpha_count=%s",
                run_id,
                snapshot.get("alert_state"),
                float(snapshot.get("gross_exposure", 0.0)),
                float(snapshot.get("net_exposure", 0.0)),
                analytics.get("alpha_count"),
            )
        except Exception as exc:
            logger.exception("paper cycle failed: %s", exc)

        await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(main())
