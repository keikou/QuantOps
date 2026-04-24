from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id
from ai_hedge_bot.data_integrity.bad_tick_detector import BadTickDetector
from ai_hedge_bot.data_integrity.data_incident_classifier import DataIncidentClassifier
from ai_hedge_bot.data_integrity.data_safe_mode_recommender import DataSafeModeRecommender
from ai_hedge_bot.data_integrity.feed_freshness_monitor import FeedFreshnessMonitor
from ai_hedge_bot.data_integrity.market_data_loader import MarketDataLoader
from ai_hedge_bot.data_integrity.mark_reliability_engine import MarkReliabilityEngine
from ai_hedge_bot.data_integrity.missing_data_detector import MissingDataDetector
from ai_hedge_bot.data_integrity.ohlcv_integrity_checker import OhlcvIntegrityChecker
from ai_hedge_bot.data_integrity.symbol_health_engine import SymbolHealthEngine


class DataIntegrityService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.loader = MarketDataLoader()
        self.feed = FeedFreshnessMonitor()
        self.missing = MissingDataDetector()
        self.bad_ticks = BadTickDetector()
        self.ohlcv = OhlcvIntegrityChecker()
        self.mark = MarkReliabilityEngine()
        self.symbol_health = SymbolHealthEngine()
        self.incidents = DataIncidentClassifier()
        self.safe_mode = DataSafeModeRecommender()

    def _latest_run(self) -> dict:
        return self.store.fetchone_dict(
            """
            SELECT *
            FROM data_integrity_runs
            ORDER BY completed_at DESC, started_at DESC
            LIMIT 1
            """
        ) or {}

    def _latest_rows(self, table: str, limit: int = 100) -> list[dict]:
        return self.store.fetchall_dict(
            f"""
            SELECT *
            FROM {table}
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [max(int(limit), 1)],
        )

    def run(self, limit: int = 20) -> dict:
        data = self.loader.load()
        run_id = new_run_id()
        started_at = utc_now_iso()
        now = utc_now_iso()
        feed = self.feed.compute(data)
        mark_rows = [self.mark.compute(row) for row in data]
        mark_by_symbol = {row["symbol"]: row for row in mark_rows}
        symbol_rows = [self.symbol_health.compute(row, mark_by_symbol[row.symbol]) for row in data]
        anomalies = []
        anomalies.extend(self._freshness_anomalies(data))
        anomalies.extend(self.missing.detect(data))
        anomalies.extend(self.bad_ticks.detect(data))
        anomalies.extend(self.ohlcv.detect(data))
        anomalies.extend(self._mark_anomalies(mark_rows))
        incidents = self.incidents.classify(anomalies)
        recommendation = self.safe_mode.recommend(incidents)

        self.store.append("market_feed_health", {**feed, "run_id": run_id, "created_at": now})
        self.store.append("symbol_data_health", [{**row, "run_id": run_id, "created_at": now} for row in symbol_rows])
        self.store.append("mark_reliability_state", [{**row, "run_id": run_id, "created_at": now} for row in mark_rows])
        if anomalies:
            self.store.append("data_anomalies", [{**row, "anomaly_id": new_run_id(), "run_id": run_id, "created_at": now} for row in anomalies])
        if incidents:
            self.store.append("data_incidents", [{**row, "incident_id": new_run_id(), "run_id": run_id, "created_at": now} for row in incidents])
        self.store.append("data_safe_mode_recommendations", {**recommendation, "recommendation_id": new_run_id(), "run_id": run_id, "created_at": now})
        self.store.append(
            "data_integrity_runs",
            {
                "run_id": run_id,
                "started_at": started_at,
                "completed_at": utc_now_iso(),
                "feed_count": len({row.feed_id for row in data}),
                "symbol_count": len(data),
                "anomaly_count": len(anomalies),
                "incident_count": len(incidents),
                "max_risk_level": self._max_risk_level(incidents),
                "status": "ok",
                "notes": "orc04_data_integrity_market_feed_reliability",
            },
        )
        return self.latest(limit=limit)

    def _freshness_anomalies(self, data) -> list[dict]:
        anomalies = []
        for row in data:
            if row.stale_seconds >= 300.0:
                anomalies.append(self._anomaly(row, "stale_feed", row.stale_seconds, 300.0, "critical"))
            elif row.stale_seconds >= 180.0:
                anomalies.append(self._anomaly(row, "stale_feed", row.stale_seconds, 180.0, "severe"))
            elif row.stale_seconds >= 60.0:
                anomalies.append(self._anomaly(row, "stale_feed", row.stale_seconds, 60.0, "warning"))
        return anomalies

    def _mark_anomalies(self, mark_rows: list[dict]) -> list[dict]:
        anomalies = []
        for row in mark_rows:
            if not row["reliable"]:
                anomalies.append(
                    {
                        "feed_id": row["mark_source"],
                        "symbol": row["symbol"],
                        "anomaly_type": "mark_unreliable",
                        "observed_value": row["mark_reliability_score"],
                        "expected_value": 0.60,
                        "anomaly_score": 0.7,
                        "severity": "severe",
                        "evidence_json": f"mark_reliability_score={row['mark_reliability_score']}",
                    }
                )
        return anomalies

    def _anomaly(self, row, anomaly_type: str, observed: float, expected: float, severity: str) -> dict:
        return {
            "feed_id": row.feed_id,
            "symbol": row.symbol,
            "anomaly_type": anomaly_type,
            "observed_value": observed,
            "expected_value": expected,
            "anomaly_score": 1.0 if severity == "critical" else 0.7 if severity == "severe" else 0.45,
            "severity": severity,
            "evidence_json": f"{anomaly_type}:observed={observed};expected={expected}",
        }

    def _max_risk_level(self, incidents: list[dict]) -> str:
        if not incidents:
            return "L0_NORMAL"
        order = {"L1_WATCH": 1, "L3_FREEZE": 3, "L5_GLOBAL_HALT": 5}
        return max((str(row["risk_level"]) for row in incidents), key=lambda item: order.get(item, 0))

    def latest(self, limit: int = 20) -> dict:
        run = self._latest_run()
        if not run:
            return self.run(limit=limit)
        feed = self._rows_for_run("market_feed_health", run.get("run_id"), 1)
        symbols = self._rows_for_run("symbol_data_health", run.get("run_id"), limit)
        return {
            "status": "ok",
            "run_id": run.get("run_id"),
            "feed_health": feed[0] if feed else {},
            "symbols": symbols,
            "data_integrity_summary": {
                "feed_count": run.get("feed_count"),
                "symbol_count": run.get("symbol_count"),
                "anomaly_count": run.get("anomaly_count"),
                "incident_count": run.get("incident_count"),
                "max_risk_level": run.get("max_risk_level"),
            },
            "as_of": run.get("completed_at"),
        }

    def _rows_for_run(self, table: str, run_id: str, limit: int) -> list[dict]:
        return self.store.fetchall_dict(
            f"""
            SELECT *
            FROM {table}
            WHERE run_id=?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [run_id, max(int(limit), 1)],
        )

    def market_feed_health_latest(self, limit: int = 20) -> dict:
        run = self._ensure_run()
        rows = self._rows_for_run("market_feed_health", run.get("run_id"), max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "market_feed_health_summary": {"feed_count": len(rows[:limit])}}

    def market_feed_health(self, feed_id: str) -> dict:
        self._ensure_run()
        row = self.store.fetchone_dict("SELECT * FROM market_feed_health WHERE feed_id=? ORDER BY created_at DESC LIMIT 1", [feed_id]) or {}
        return {"status": "ok" if row else "not_found", "feed_id": feed_id, "feed_health": row}

    def symbol_data_health_latest(self, limit: int = 20) -> dict:
        run = self._ensure_run()
        rows = self._rows_for_run("symbol_data_health", run.get("run_id"), max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "symbol_data_health_summary": {"symbol_count": len(rows[:limit])}}

    def symbol_data_health(self, symbol: str) -> dict:
        self._ensure_run()
        row = self.store.fetchone_dict("SELECT * FROM symbol_data_health WHERE symbol=? ORDER BY created_at DESC LIMIT 1", [symbol]) or {}
        return {"status": "ok" if row else "not_found", "symbol": symbol, "symbol_health": row}

    def data_anomalies_latest(self, limit: int = 20) -> dict:
        run = self._ensure_run()
        rows = self._rows_for_run("data_anomalies", run.get("run_id"), max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "data_anomaly_summary": {"anomaly_count": len(rows[:limit])}}

    def data_incidents_latest(self, limit: int = 20) -> dict:
        run = self._ensure_run()
        rows = self._rows_for_run("data_incidents", run.get("run_id"), max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "data_incident_summary": {"incident_count": len(rows[:limit])}}

    def mark_reliability_latest(self, limit: int = 20) -> dict:
        run = self._ensure_run()
        rows = self._rows_for_run("mark_reliability_state", run.get("run_id"), max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "mark_reliability_summary": {"mark_count": len(rows[:limit])}}

    def data_safe_mode_recommendation_latest(self, limit: int = 20) -> dict:
        run = self._ensure_run()
        rows = self._rows_for_run("data_safe_mode_recommendations", run.get("run_id"), max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "data_safe_mode_summary": {"recommendation_count": len(rows[:limit])}}

    def _ensure_run(self) -> dict:
        run = self._latest_run()
        if not run:
            self.run(limit=20)
            run = self._latest_run()
        return run

