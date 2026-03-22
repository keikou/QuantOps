from __future__ import annotations

import asyncio
import logging

from app.core.config import get_settings
from app.core.deps import get_analytics_repository, get_risk_repository, get_v12_client
from app.services.analytics_service import AnalyticsService
from app.services.risk_service import RiskService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("quantops-risk-worker")


async def main() -> None:
    settings = get_settings()
    v12_client = get_v12_client()
    risk_service = RiskService(v12_client, get_risk_repository())
    analytics_service = AnalyticsService(v12_client, get_analytics_repository())
    logger.info(
        "starting worker interval=%ss mock_mode=%s",
        settings.risk_refresh_interval_seconds,
        settings.v12_mock_mode,
    )
    while True:
        snapshot = await risk_service.refresh_snapshot()
        analytics = await analytics_service.refresh()
        logger.info(
            "worker refreshed risk alert=%s gross=%.4f net=%.4f alpha_count=%s",
            snapshot["alert_state"],
            snapshot["gross_exposure"],
            snapshot["net_exposure"],
            analytics["alpha_count"],
        )
        await asyncio.sleep(settings.risk_refresh_interval_seconds)


if __name__ == "__main__":
    asyncio.run(main())
