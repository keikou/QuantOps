from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from statistics import pstdev
from typing import Any

from ai_hedge_bot.risk.drawdown_monitor import DrawdownMonitor
from ai_hedge_bot.risk.exposure_model import ExposureModel
from ai_hedge_bot.risk.risk_limits import RiskLimitEvaluator, RiskLimits


@dataclass(slots=True)
class RiskSnapshot:
    run_id: str
    created_at: str
    gross_exposure: float
    net_exposure: float
    max_position_weight: float
    portfolio_volatility: float
    drawdown: float
    sector_exposure: dict[str, float]
    strategy_exposure: dict[str, float]
    risk_flag: bool
    risk_reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RiskEngine:
    def __init__(self, limits: RiskLimits | None = None) -> None:
        self.exposure_model = ExposureModel()
        self.drawdown_monitor = DrawdownMonitor()
        self.limit_evaluator = RiskLimitEvaluator()
        self.limits = limits or RiskLimits()

    def estimate_portfolio_volatility(self, positions: list[dict[str, Any]]) -> float:
        weights = [abs(float(x.get('weight', 0.0))) for x in positions]
        if len(weights) <= 1:
            return weights[0] if weights else 0.0
        return float(pstdev(weights))

    def evaluate_portfolio_risk(
        self,
        *,
        run_id: str,
        positions: list[dict[str, Any]],
        current_equity: float,
        previous_peak_equity: float,
    ) -> RiskSnapshot:
        gross_exposure = self.exposure_model.calculate_gross_exposure(positions)
        net_exposure = self.exposure_model.calculate_net_exposure(positions)
        max_position_weight = self.exposure_model.calculate_max_position_weight(positions)
        sector_exposure = self.exposure_model.calculate_sector_exposure(positions)
        strategy_exposure = self.exposure_model.calculate_strategy_exposure(positions)
        portfolio_volatility = self.estimate_portfolio_volatility(positions)
        dd_state = self.drawdown_monitor.build_state(previous_peak=previous_peak_equity, current_equity=current_equity)

        snapshot = {
            'gross_exposure': gross_exposure,
            'net_exposure': net_exposure,
            'max_position_weight': max_position_weight,
            'portfolio_volatility': portfolio_volatility,
            'drawdown': dd_state.drawdown,
            'sector_exposure': sector_exposure,
        }
        result = self.limit_evaluator.evaluate(snapshot, self.limits)

        return RiskSnapshot(
            run_id=run_id,
            created_at=datetime.now(UTC).isoformat(),
            gross_exposure=gross_exposure,
            net_exposure=net_exposure,
            max_position_weight=max_position_weight,
            portfolio_volatility=portfolio_volatility,
            drawdown=dd_state.drawdown,
            sector_exposure=sector_exposure,
            strategy_exposure=strategy_exposure,
            risk_flag=not result.passed,
            risk_reasons=result.reasons,
        )
