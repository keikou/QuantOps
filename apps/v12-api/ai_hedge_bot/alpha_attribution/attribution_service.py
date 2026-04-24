from __future__ import annotations

from ai_hedge_bot.alpha_attribution.alpha_return_loader import AlphaReturnLoader
from ai_hedge_bot.alpha_attribution.attribution_decision_engine import AttributionDecisionEngine
from ai_hedge_bot.alpha_attribution.economic_labeler import EconomicLabeler
from ai_hedge_bot.alpha_attribution.exposure_estimator import ExposureEstimator
from ai_hedge_bot.alpha_attribution.factor_concentration_engine import FactorConcentrationEngine
from ai_hedge_bot.alpha_attribution.factor_data_loader import FactorDataLoader
from ai_hedge_bot.alpha_attribution.hidden_driver_detector import HiddenDriverDetector
from ai_hedge_bot.alpha_attribution.regime_dependency_engine import RegimeDependencyEngine
from ai_hedge_bot.alpha_attribution.residual_alpha_engine import ResidualAlphaEngine
from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id


class AlphaAttributionService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.alpha_loader = AlphaReturnLoader()
        self.factor_loader = FactorDataLoader()
        self.exposure_estimator = ExposureEstimator()
        self.residual_engine = ResidualAlphaEngine()
        self.regime_engine = RegimeDependencyEngine()
        self.concentration_engine = FactorConcentrationEngine()
        self.hidden_driver = HiddenDriverDetector()
        self.labeler = EconomicLabeler()
        self.decision = AttributionDecisionEngine()

    def _latest_run(self) -> dict:
        return self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_attribution_runs
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
        labels = self._latest_rows("alpha_economic_meaning_labels", limit=max(limit * 3, 30))
        items = [
            {
                "alpha_id": row.get("alpha_id"),
                "primary_label": row.get("primary_label"),
                "confidence": row.get("confidence"),
                "production_recommendation": row.get("production_recommendation"),
            }
            for row in labels[:limit]
        ]
        return {
            "status": "ok",
            "run_id": run.get("run_id"),
            "items": items,
            "alpha_factor_attribution_summary": {
                "alpha_count": run.get("alpha_count"),
                "ensemble_count": run.get("ensemble_count"),
                "factor_count": run.get("factor_count"),
                "scale_allowed_count": sum(1 for item in items if item.get("production_recommendation") == "scale_allowed"),
                "system_alpha_factor_attribution_action": "require_economic_meaning_before_scaling",
            },
            "as_of": run.get("completed_at"),
        }

    def _materialize_run(self, limit: int = 20) -> dict:
        alphas = self.alpha_loader.load_selected_alpha(limit=max(limit, 8))
        factors = self.factor_loader.load_factor_set()
        hidden_flags = self.hidden_driver.detect(alphas)
        run_id = new_run_id()
        started_at = utc_now_iso()

        exposure_rows: list[dict] = []
        model_fit_rows: list[dict] = []
        residual_rows: list[dict] = []
        regime_rows_all: list[dict] = []
        concentration_rows: list[dict] = []
        hidden_rows: list[dict] = []
        label_rows: list[dict] = []

        weighted_exposures: dict[str, float] = {}
        ensemble_id = alphas[0].ensemble_id if alphas else "ensemble.synthetic"

        for alpha in alphas:
            exposures = self.exposure_estimator.estimate(alpha, factors)
            residual = self.residual_engine.score(alpha, exposures)
            regime_rows = self.regime_engine.profile(alpha)
            for exposure in exposures:
                weighted_exposures[exposure["factor_name"]] = weighted_exposures.get(exposure["factor_name"], 0.0) + (
                    alpha.weight * float(exposure["beta"])
                )
                exposure_rows.append(
                    {
                        "run_id": run_id,
                        "alpha_id": alpha.alpha_id,
                        "factor_name": exposure["factor_name"],
                        "factor_group": exposure["factor_group"],
                        "beta": exposure["beta"],
                        "t_stat": exposure["t_stat"],
                        "p_value": exposure["p_value"],
                        "exposure_strength": exposure["exposure_strength"],
                        "exposure_direction": exposure["exposure_direction"],
                        "significant": exposure["significant"],
                        "created_at": utc_now_iso(),
                    }
                )
            model_fit_rows.append(
                {
                    "run_id": run_id,
                    "alpha_id": alpha.alpha_id,
                    "model_name": "deterministic_style_model",
                    "sample_count": 180,
                    "r_squared": residual["factor_explained_score"],
                    "adjusted_r_squared": max(0.0, residual["factor_explained_score"] - 0.04),
                    "residual_volatility": residual["residual_volatility"],
                    "intercept_alpha": residual["residual_mean_return"],
                    "intercept_t_stat": residual["residual_sharpe"],
                    "model_valid": True,
                    "fail_reason": "",
                    "created_at": utc_now_iso(),
                }
            )
            residual_rows.append(
                {
                    "run_id": run_id,
                    "alpha_id": alpha.alpha_id,
                    "raw_alpha_score": residual["raw_alpha_score"],
                    "factor_explained_score": residual["factor_explained_score"],
                    "residual_alpha_score": residual["residual_alpha_score"],
                    "residual_sharpe": residual["residual_sharpe"],
                    "residual_hit_rate": residual["residual_hit_rate"],
                    "residual_mean_return": residual["residual_mean_return"],
                    "residual_volatility": residual["residual_volatility"],
                    "residual_quality": residual["residual_quality"],
                    "created_at": utc_now_iso(),
                }
            )
            for regime in regime_rows:
                regime_rows_all.append(
                    {
                        "run_id": run_id,
                        "alpha_id": alpha.alpha_id,
                        "regime_name": regime["regime_name"],
                        "regime_sample_count": regime["regime_sample_count"],
                        "regime_mean_return": regime["regime_mean_return"],
                        "regime_sharpe": regime["regime_sharpe"],
                        "regime_hit_rate": regime["regime_hit_rate"],
                        "dependency_score": regime["dependency_score"],
                        "regime_dependency_flag": regime["regime_dependency_flag"],
                        "created_at": utc_now_iso(),
                    }
                )
            label = self.labeler.label(alpha.alpha_id, exposures, residual, regime_rows, hidden_flags)
            label_rows.append(
                {
                    "run_id": run_id,
                    "alpha_id": alpha.alpha_id,
                    "primary_label": label["primary_label"],
                    "secondary_labels": self.store.to_json(label["secondary_labels"]),
                    "explanation": label["explanation"],
                    "confidence": label["confidence"],
                    "production_recommendation": label["production_recommendation"],
                    "created_at": utc_now_iso(),
                }
            )

        concentration = self.concentration_engine.compute(ensemble_id, weighted_exposures)
        concentration_rows.extend(
            {
                "run_id": run_id,
                "ensemble_id": row["ensemble_id"],
                "factor_name": row["factor_name"],
                "weighted_exposure": row["weighted_exposure"],
                "absolute_weighted_exposure": row["absolute_weighted_exposure"],
                "concentration_score": row["concentration_score"],
                "concentration_flag": row["concentration_flag"],
                "created_at": utc_now_iso(),
            }
            for row in concentration
        )
        hidden_rows.extend(
            {
                "run_id": run_id,
                "alpha_id_a": row["alpha_id_a"],
                "alpha_id_b": row["alpha_id_b"],
                "common_driver_score": row["common_driver_score"],
                "residual_correlation": row["residual_correlation"],
                "suspected_driver": row["suspected_driver"],
                "flag": row["flag"],
                "created_at": utc_now_iso(),
            }
            for row in hidden_flags
        )

        recommendation_lookup = {str(row["alpha_id"]): row for row in label_rows}
        for row in label_rows:
            decision = self.decision.decide(
                next(item for item in residual_rows if item["alpha_id"] == row["alpha_id"]),
                concentration_rows,
                recommendation_lookup[row["alpha_id"]],
                hidden_rows,
                row["alpha_id"],
            )
            row["production_recommendation"] = decision["production_recommendation"]
            row["explanation"] = f"{row['explanation']}; economic_risk={decision['economic_risk_state']}"

        self.store.append(
            "alpha_attribution_runs",
            {
                "run_id": run_id,
                "started_at": started_at,
                "completed_at": utc_now_iso(),
                "alpha_count": len(alphas),
                "ensemble_count": 1 if alphas else 0,
                "factor_count": len(factors),
                "status": "ok",
                "notes": "aes04_economic_meaning_factor_attribution",
            },
        )
        if exposure_rows:
            self.store.append("alpha_factor_exposures", exposure_rows)
        if model_fit_rows:
            self.store.append("alpha_factor_model_fit", model_fit_rows)
        if residual_rows:
            self.store.append("alpha_residual_alpha_scores", residual_rows)
        if regime_rows_all:
            self.store.append("alpha_regime_dependency", regime_rows_all)
        if concentration_rows:
            self.store.append("alpha_factor_concentration", concentration_rows)
        if hidden_rows:
            self.store.append("alpha_hidden_driver_flags", hidden_rows)
        if label_rows:
            self.store.append("alpha_economic_meaning_labels", label_rows)
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
        rows = self._latest_rows("alpha_economic_meaning_labels", limit=max(limit * 3, 30))
        if not rows:
            return self._materialize_run(limit=limit)
        return self._build_latest_payload(run, limit=limit)

    def alpha_factor_exposure_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("alpha_factor_exposures", limit=max(limit * 4, 40))
        return {"status": "ok", "items": rows[:limit]}

    def alpha_residual_alpha_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("alpha_residual_alpha_scores", limit=max(limit * 3, 30))
        return {
            "status": "ok",
            "items": rows[:limit],
            "alpha_residual_alpha_summary": {
                "alpha_count": len(rows[:limit]),
                "strong_residual_alpha_count": sum(1 for row in rows[:limit] if row.get("residual_quality") == "strong_residual_alpha"),
                "system_alpha_residual_action": "scale_only_residual_alpha_with_explained_risk_visible",
            },
        }

    def alpha_economic_risk_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        regime_rows = self._latest_rows("alpha_regime_dependency", limit=max(limit * 6, 60))
        hidden_rows = self._latest_rows("alpha_hidden_driver_flags", limit=max(limit * 4, 40))
        items = []
        for row in regime_rows[:limit]:
            alpha_id = str(row.get("alpha_id") or "")
            hidden_flag = any(alpha_id in {item.get("alpha_id_a"), item.get("alpha_id_b")} and item.get("flag") for item in hidden_rows)
            items.append(
                {
                    "alpha_id": alpha_id,
                    "regime_name": row.get("regime_name"),
                    "dependency_score": row.get("dependency_score"),
                    "regime_dependency_flag": row.get("regime_dependency_flag"),
                    "hidden_common_driver_flag": hidden_flag,
                }
            )
        return {
            "status": "ok",
            "items": items,
            "alpha_economic_risk_summary": {
                "alpha_count": len(items),
                "flagged_count": sum(1 for item in items if item.get("regime_dependency_flag") or item.get("hidden_common_driver_flag")),
                "system_alpha_economic_risk_action": "limit_scaling_for_regime_fragile_or_hidden_driver_alpha",
            },
        }

    def alpha_factor_concentration_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("alpha_factor_concentration", limit=max(limit * 3, 30))
        return {
            "status": "ok",
            "items": rows[:limit],
            "alpha_factor_concentration_summary": {
                "factor_count": len(rows[:limit]),
                "breach_count": sum(1 for row in rows[:limit] if row.get("concentration_flag")),
                "system_alpha_factor_concentration_action": "cap_factor_heavy_ensemble_before_portfolio_scaling",
            },
        }

    def alpha_economic_meaning_latest(self, limit: int = 20) -> dict:
        latest = self.latest(limit=limit)
        return {
            "status": "ok",
            "run_id": latest.get("run_id"),
            "items": list(latest.get("items") or [])[:limit],
            "alpha_economic_meaning_summary": {
                "alpha_count": len(list(latest.get("items") or [])[:limit]),
                "do_not_scale_count": sum(1 for item in list(latest.get("items") or [])[:limit] if item.get("production_recommendation") == "do_not_scale"),
                "system_alpha_economic_meaning_action": "require_explainable_scaling_recommendation_before_mpi_lcc_use",
            },
        }

    def alpha_factor_attribution_candidate(self, alpha_id: str) -> dict:
        self.latest(limit=20)
        label = self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_economic_meaning_labels
            WHERE alpha_id=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [alpha_id],
        ) or {}
        exposures = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_factor_exposures
            WHERE alpha_id=?
            ORDER BY exposure_strength DESC, factor_name ASC
            LIMIT 20
            """,
            [alpha_id],
        )
        residual = self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_residual_alpha_scores
            WHERE alpha_id=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [alpha_id],
        ) or {}
        return {
            "status": "ok" if label else "not_found",
            "alpha_id": alpha_id,
            "label": label,
            "residual": residual,
            "exposures": exposures,
        }

    def alpha_factor_attribution_ensemble(self, ensemble_id: str) -> dict:
        self.latest(limit=20)
        concentration = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_factor_concentration
            WHERE ensemble_id=?
            ORDER BY concentration_score DESC, factor_name ASC
            LIMIT 20
            """,
            [ensemble_id],
        )
        return {
            "status": "ok" if concentration else "not_found",
            "ensemble_id": ensemble_id,
            "factor_concentration": concentration,
        }
