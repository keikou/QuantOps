from __future__ import annotations

from ai_hedge_bot.alpha_capacity.capacity_estimator import CapacityEstimator
from ai_hedge_bot.alpha_capacity.capacity_input_loader import CapacityInputLoader
from ai_hedge_bot.alpha_capacity.crowding_detector import CrowdingDetector
from ai_hedge_bot.alpha_capacity.ensemble_capacity_engine import EnsembleCapacityEngine
from ai_hedge_bot.alpha_capacity.impact_model import ImpactModel
from ai_hedge_bot.alpha_capacity.liquidity_model import LiquidityModel
from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id


class AlphaCapacityService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.loader = CapacityInputLoader()
        self.liquidity = LiquidityModel()
        self.impact = ImpactModel()
        self.crowding = CrowdingDetector()
        self.capacity = CapacityEstimator()
        self.ensemble = EnsembleCapacityEngine()

    def _latest_run(self) -> dict:
        return self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_capacity_runs
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

    def _build_latest_payload(self, run: dict, limit: int = 20) -> dict:
        rows = self._latest_rows("alpha_capacity", limit=max(limit * 3, 30))
        items = [
            {
                "alpha_id": row.get("alpha_id"),
                "capacity": row.get("capacity"),
                "liquidity_score": row.get("liquidity_score"),
                "crowding_score": row.get("crowding_score"),
                "scaling_recommendation": row.get("scaling_recommendation"),
            }
            for row in rows[:limit]
        ]
        return {
            "status": "ok",
            "run_id": run.get("run_id"),
            "items": items,
            "alpha_capacity_summary": {
                "alpha_count": run.get("alpha_count"),
                "ensemble_count": run.get("ensemble_count"),
                "scale_block_count": sum(1 for item in items if item.get("scaling_recommendation") == "do_not_scale"),
                "system_alpha_capacity_action": "cap_alpha_scaling_before_mpi_lcc_allocation",
            },
            "as_of": run.get("completed_at"),
        }

    def _materialize_run(self, limit: int = 20) -> dict:
        inputs = self.loader.load(limit=max(limit, 8))
        run_id = new_run_id()
        started_at = utc_now_iso()
        alpha_rows: list[dict] = []
        impact_rows: list[dict] = []
        crowding_rows: list[dict] = []

        for item in inputs:
            liquidity = self.liquidity.score(item)
            impact = self.impact.estimate(item, liquidity["liquidity_score"])
            crowding = self.crowding.score(item)
            capacity = self.capacity.estimate(item, liquidity, impact, crowding)
            now = utc_now_iso()
            alpha_rows.append(
                {
                    "run_id": run_id,
                    "ensemble_id": item.ensemble_id,
                    "alpha_id": item.alpha_id,
                    "weight": item.weight,
                    "liquidity_score": liquidity["liquidity_score"],
                    "turnover": item.turnover,
                    "impact_cost": impact["impact_cost"],
                    "capacity": capacity["capacity"],
                    "crowding_score": crowding["crowding_score"],
                    "impact_adjusted_return": capacity["impact_adjusted_return"],
                    "scaling_recommendation": capacity["scaling_recommendation"],
                    "created_at": now,
                }
            )
            impact_rows.append(
                {
                    "run_id": run_id,
                    "ensemble_id": item.ensemble_id,
                    "alpha_id": item.alpha_id,
                    "trade_size_fraction": impact["trade_size_fraction"],
                    "impact_cost": impact["impact_cost"],
                    "turnover_impact": impact["turnover_impact"],
                    "impact_adjusted_return": capacity["impact_adjusted_return"],
                    "created_at": now,
                }
            )
            crowding_rows.append(
                {
                    "run_id": run_id,
                    "ensemble_id": item.ensemble_id,
                    "alpha_id": item.alpha_id,
                    "correlation_cluster_score": crowding["correlation_cluster_score"],
                    "factor_concentration": crowding["factor_concentration"],
                    "signal_overlap": crowding["signal_overlap"],
                    "volume_anomaly": crowding["volume_anomaly"],
                    "crowding_score": crowding["crowding_score"],
                    "created_at": now,
                }
            )

        ensemble_rows = []
        for ensemble_id in sorted({str(row.get("ensemble_id") or "") for row in alpha_rows}):
            rows = [row for row in alpha_rows if row.get("ensemble_id") == ensemble_id]
            result = self.ensemble.compute(ensemble_id, rows)
            ensemble_rows.append(
                {
                    "run_id": run_id,
                    "ensemble_id": result["ensemble_id"],
                    "total_capacity": result["total_capacity"],
                    "limiting_alpha": result["limiting_alpha"],
                    "scaling_recommendation": result["scaling_recommendation"],
                    "created_at": utc_now_iso(),
                }
            )

        self.store.append(
            "alpha_capacity_runs",
            {
                "run_id": run_id,
                "started_at": started_at,
                "completed_at": utc_now_iso(),
                "alpha_count": len(alpha_rows),
                "ensemble_count": len(ensemble_rows),
                "status": "ok",
                "notes": "aes05_capacity_crowding_risk",
            },
        )
        if alpha_rows:
            self.store.append("alpha_capacity", alpha_rows)
        if impact_rows:
            self.store.append("alpha_impact", impact_rows)
        if crowding_rows:
            self.store.append("alpha_crowding", crowding_rows)
        if ensemble_rows:
            self.store.append("ensemble_capacity", ensemble_rows)
        run = self._latest_run()
        return self._build_latest_payload(run, limit=limit)

    def run(self, limit: int = 20) -> dict:
        latest_run = self._latest_run()
        if latest_run:
            latest = self.latest(limit=limit)
            if list(latest.get("items") or []):
                return latest
        return self._materialize_run(limit=limit)

    def latest(self, limit: int = 20) -> dict:
        run = self._latest_run()
        if not run:
            return self.run(limit=limit)
        rows = self._latest_rows("alpha_capacity", limit=max(limit * 3, 30))
        if not rows:
            return self._materialize_run(limit=limit)
        return self._build_latest_payload(run, limit=limit)

    def alpha_capacity_candidate(self, alpha_id: str) -> dict:
        self.latest(limit=20)
        row = self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_capacity
            WHERE alpha_id=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [alpha_id],
        ) or {}
        impact = self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_impact
            WHERE alpha_id=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [alpha_id],
        ) or {}
        crowding = self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_crowding
            WHERE alpha_id=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [alpha_id],
        ) or {}
        return {"status": "ok" if row else "not_found", "alpha_id": alpha_id, "capacity": row, "impact": impact, "crowding": crowding}

    def alpha_crowding_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("alpha_crowding", limit=max(limit * 3, 30))
        return {
            "status": "ok",
            "items": rows[:limit],
            "alpha_crowding_summary": {
                "alpha_count": len(rows[:limit]),
                "crowded_count": sum(1 for row in rows[:limit] if float(row.get("crowding_score", 0.0) or 0.0) > 0.80),
                "system_alpha_crowding_action": "block_or_limit_crowded_alpha_before_scaling",
            },
        }

    def alpha_impact_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("alpha_impact", limit=max(limit * 3, 30))
        return {
            "status": "ok",
            "items": rows[:limit],
            "alpha_impact_summary": {
                "alpha_count": len(rows[:limit]),
                "high_impact_count": sum(1 for row in rows[:limit] if float(row.get("impact_cost", 0.0) or 0.0) > 0.05),
                "system_alpha_impact_action": "subtract_market_impact_before_capacity_scaling",
            },
        }

    def alpha_capacity_ensemble(self, ensemble_id: str) -> dict:
        self.latest(limit=20)
        row = self.store.fetchone_dict(
            """
            SELECT *
            FROM ensemble_capacity
            WHERE ensemble_id=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [ensemble_id],
        ) or {}
        alphas = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_capacity
            WHERE ensemble_id=?
            ORDER BY capacity ASC, alpha_id ASC
            LIMIT 50
            """,
            [ensemble_id],
        )
        return {"status": "ok" if row else "not_found", "ensemble_id": ensemble_id, "ensemble_capacity": row, "alphas": alphas}
