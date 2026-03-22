from __future__ import annotations

from app.services.analytics_service import AnalyticsService


class _Repo:
    def latest_execution(self):
        return {
            "fill_rate": 5.0,
            "avg_slippage_bps": 1.84,
            "latency_ms_p50": 46.0,
            "latency_ms_p95": 58.0,
            "venue_score": 1.4,
            "as_of": "2026-03-19T10:29:50+00:00",
        }


def test_execution_summary_clamps_fill_rate_and_venue_score() -> None:
    service = AnalyticsService(v12_client=None, analytics_repository=_Repo())  # type: ignore[arg-type]
    latest = service.execution_summary()
    assert latest["fill_rate"] == 1.0
    assert latest["venue_score"] == 1.0
