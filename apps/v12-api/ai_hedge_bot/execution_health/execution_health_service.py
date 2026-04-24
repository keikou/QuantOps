from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id
from ai_hedge_bot.execution_health.broker_health_monitor import BrokerHealthMonitor
from ai_hedge_bot.execution_health.cancel_replace_monitor import CancelReplaceMonitor
from ai_hedge_bot.execution_health.execution_incident_classifier import ExecutionIncidentClassifier
from ai_hedge_bot.execution_health.execution_safe_mode_recommender import ExecutionSafeModeRecommender
from ai_hedge_bot.execution_health.execution_telemetry_loader import ExecutionTelemetryLoader
from ai_hedge_bot.execution_health.fill_quality_engine import FillQualityEngine
from ai_hedge_bot.execution_health.latency_anomaly_detector import LatencyAnomalyDetector
from ai_hedge_bot.execution_health.order_lifecycle_monitor import OrderLifecycleMonitor
from ai_hedge_bot.execution_health.slippage_anomaly_detector import SlippageAnomalyDetector
from ai_hedge_bot.execution_health.venue_health_monitor import VenueHealthMonitor


class ExecutionHealthService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.loader = ExecutionTelemetryLoader()
        self.broker = BrokerHealthMonitor()
        self.venue = VenueHealthMonitor()
        self.lifecycle = OrderLifecycleMonitor()
        self.fill_quality = FillQualityEngine()
        self.slippage = SlippageAnomalyDetector()
        self.latency = LatencyAnomalyDetector()
        self.cancel_replace = CancelReplaceMonitor()
        self.incidents = ExecutionIncidentClassifier()
        self.safe_mode = ExecutionSafeModeRecommender()

    def _latest_run(self) -> dict:
        return self.store.fetchone_dict(
            """
            SELECT *
            FROM execution_health_runs
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
        telemetry = self.loader.load()
        run_id = new_run_id()
        started_at = utc_now_iso()
        now = utc_now_iso()
        broker = self.broker.compute(telemetry)
        venue = self.venue.compute(telemetry)
        lifecycle = self.lifecycle.compute(telemetry)
        fill_quality = self.fill_quality.compute(telemetry)
        metrics = self._metrics(run_id, now, telemetry, broker, venue, lifecycle, fill_quality)
        anomalies = self._domain_anomalies(telemetry, broker, venue, lifecycle)
        anomalies.extend(self.slippage.detect(telemetry))
        anomalies.extend(self.latency.detect(telemetry))
        anomalies.extend(self.cancel_replace.detect(telemetry))
        incidents = self.incidents.classify(anomalies)
        recommendation = self.safe_mode.recommend(incidents, telemetry.broker_id, telemetry.venue_id)

        self.store.append("execution_health_metrics", metrics)
        self.store.append("broker_health_state", {**broker, "run_id": run_id, "created_at": now})
        self.store.append("venue_health_state", {**venue, "run_id": run_id, "created_at": now})
        if anomalies:
            self.store.append("execution_anomalies", [{**row, "anomaly_id": new_run_id(), "run_id": run_id, "created_at": now} for row in anomalies])
        if incidents:
            self.store.append("execution_incidents", [{**row, "incident_id": new_run_id(), "run_id": run_id, "created_at": now} for row in incidents])
        self.store.append("execution_safe_mode_recommendations", {**recommendation, "recommendation_id": new_run_id(), "run_id": run_id, "created_at": now})
        self.store.append(
            "execution_health_runs",
            {
                "run_id": run_id,
                "started_at": started_at,
                "completed_at": utc_now_iso(),
                "order_count": telemetry.order_count,
                "fill_count": telemetry.fill_count,
                "reject_count": telemetry.reject_count,
                "anomaly_count": len(anomalies),
                "incident_count": len(incidents),
                "max_risk_level": self._max_risk_level(incidents),
                "status": "ok",
                "notes": "orc03_execution_anomaly_broker_health",
            },
        )
        return self.latest(limit=limit)

    def _metrics(self, run_id: str, now: str, telemetry, broker: dict, venue: dict, lifecycle: dict, fill_quality: dict) -> list[dict]:
        rows = [
            ("reject_rate", broker["reject_rate"], 0.03, 0.15, "broker"),
            ("cancel_success_rate", broker["cancel_success_rate"], 0.98, 0.90, "broker"),
            ("broker_health_score", broker["broker_health_score"], 0.90, 0.55, "broker"),
            ("fill_rate", venue["fill_rate"], 0.95, 0.60, "venue"),
            ("realized_slippage_bps", venue["realized_slippage_bps"], 5.0, 25.0, "venue"),
            ("latency_ms", max(telemetry.api_latency_ms, telemetry.venue_latency_ms), 100.0, 500.0, "venue"),
            ("order_lifecycle_score", lifecycle["order_lifecycle_score"], 0.98, 0.80, "execution"),
            ("fill_quality_score", fill_quality["fill_quality_score"], 0.95, 0.70, "execution"),
        ]
        return [
            {
                "run_id": run_id,
                "broker_id": telemetry.broker_id,
                "venue_id": telemetry.venue_id,
                "metric_name": name,
                "metric_value": value,
                "baseline_value": baseline,
                "threshold_value": threshold,
                "z_score": round((value - baseline) / (abs(baseline) + 0.01), 6),
                "breach": value >= threshold if name not in {"cancel_success_rate", "broker_health_score", "fill_rate", "order_lifecycle_score", "fill_quality_score"} else value <= threshold,
                "severity": "normal",
                "created_at": now,
            }
            for name, value, baseline, threshold, _ in rows
        ]

    def _domain_anomalies(self, telemetry, broker: dict, venue: dict, lifecycle: dict) -> list[dict]:
        anomalies = []
        if not broker["heartbeat_ok"]:
            anomalies.append(self._anomaly(telemetry, "broker_heartbeat_failure", 0.0, 1.0, "critical"))
        if broker["reject_rate"] >= 0.15:
            anomalies.append(self._anomaly(telemetry, "order_reject_burst", broker["reject_rate"], 0.15, "severe"))
        if venue["fill_rate"] < 0.60:
            anomalies.append(self._anomaly(telemetry, "fill_rate_collapse", venue["fill_rate"], 0.60, "severe"))
        if lifecycle["duplicate_order_count"] > 0:
            anomalies.append(self._anomaly(telemetry, "duplicate_order", lifecycle["duplicate_order_count"], 0.0, "critical"))
        if lifecycle["stuck_order_count"] > 0:
            anomalies.append(self._anomaly(telemetry, "stuck_order", lifecycle["stuck_order_count"], 0.0, "warning"))
        if not broker["position_sync_ok"]:
            anomalies.append(self._anomaly(telemetry, "position_sync_mismatch", 1.0, 0.0, "critical"))
        return anomalies

    def _anomaly(self, telemetry, anomaly_type: str, observed: float, expected: float, severity: str) -> dict:
        return {
            "broker_id": telemetry.broker_id,
            "venue_id": telemetry.venue_id,
            "order_id": "",
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
        broker = self._latest_rows("broker_health_state", limit=1)
        venue = self._latest_rows("venue_health_state", limit=1)
        return {
            "status": "ok",
            "run_id": run.get("run_id"),
            "execution_health": {
                "broker": broker[0] if broker else {},
                "venue": venue[0] if venue else {},
                "max_risk_level": run.get("max_risk_level"),
            },
            "execution_health_summary": {
                "order_count": run.get("order_count"),
                "fill_count": run.get("fill_count"),
                "reject_count": run.get("reject_count"),
                "anomaly_count": run.get("anomaly_count"),
                "incident_count": run.get("incident_count"),
            },
            "as_of": run.get("completed_at"),
        }

    def broker_health_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("broker_health_state", limit=max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "broker_health_summary": {"broker_count": len(rows[:limit])}}

    def venue_health_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("venue_health_state", limit=max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "venue_health_summary": {"venue_count": len(rows[:limit])}}

    def execution_anomalies_latest(self, limit: int = 20) -> dict:
        run = self._latest_run()
        if not run:
            self.latest(limit=limit)
            run = self._latest_run()
        rows = self.store.fetchall_dict(
            """
            SELECT *
            FROM execution_anomalies
            WHERE run_id=?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [run.get("run_id"), max(limit * 3, 30)],
        )
        return {"status": "ok", "items": rows[:limit], "execution_anomaly_summary": {"anomaly_count": len(rows[:limit])}}

    def execution_incidents_latest(self, limit: int = 20) -> dict:
        run = self._latest_run()
        if not run:
            self.latest(limit=limit)
            run = self._latest_run()
        rows = self.store.fetchall_dict(
            """
            SELECT *
            FROM execution_incidents
            WHERE run_id=?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [run.get("run_id"), max(limit * 3, 30)],
        )
        return {"status": "ok", "items": rows[:limit], "execution_incident_summary": {"incident_count": len(rows[:limit])}}

    def execution_safe_mode_recommendation_latest(self, limit: int = 20) -> dict:
        run = self._latest_run()
        if not run:
            self.latest(limit=limit)
            run = self._latest_run()
        rows = self.store.fetchall_dict(
            """
            SELECT *
            FROM execution_safe_mode_recommendations
            WHERE run_id=?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [run.get("run_id"), max(limit * 3, 30)],
        )
        return {"status": "ok", "items": rows[:limit], "execution_safe_mode_summary": {"recommendation_count": len(rows[:limit])}}

    def broker_health(self, broker_id: str) -> dict:
        self.latest(limit=20)
        row = self.store.fetchone_dict(
            "SELECT * FROM broker_health_state WHERE broker_id=? ORDER BY created_at DESC LIMIT 1",
            [broker_id],
        ) or {}
        return {"status": "ok" if row else "not_found", "broker_id": broker_id, "broker_health": row}

    def venue_health(self, venue_id: str) -> dict:
        self.latest(limit=20)
        row = self.store.fetchone_dict(
            "SELECT * FROM venue_health_state WHERE venue_id=? ORDER BY created_at DESC LIMIT 1",
            [venue_id],
        ) or {}
        return {"status": "ok" if row else "not_found", "venue_id": venue_id, "venue_health": row}
