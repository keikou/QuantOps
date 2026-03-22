from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class RiskLimits:
    max_position_weight: float = 0.10
    max_sector_exposure: float = 0.30
    max_drawdown: float = 0.10
    max_gross_exposure: float = 1.50
    max_net_exposure_abs: float = 0.75
    max_portfolio_volatility: float = 0.35


@dataclass(slots=True)
class RiskLimitResult:
    passed: bool
    reasons: list[str] = field(default_factory=list)


class RiskLimitEvaluator:
    def evaluate(self, snapshot: dict, limits: RiskLimits) -> RiskLimitResult:
        reasons: list[str] = []

        if float(snapshot.get('max_position_weight', 0.0)) > limits.max_position_weight:
            reasons.append('max_position_weight_breach')
        if float(snapshot.get('gross_exposure', 0.0)) > limits.max_gross_exposure:
            reasons.append('gross_exposure_breach')
        if abs(float(snapshot.get('net_exposure', 0.0))) > limits.max_net_exposure_abs:
            reasons.append('net_exposure_breach')
        if float(snapshot.get('drawdown', 0.0)) > limits.max_drawdown:
            reasons.append('drawdown_breach')
        if float(snapshot.get('portfolio_volatility', 0.0)) > limits.max_portfolio_volatility:
            reasons.append('volatility_breach')

        for sector, exposure in (snapshot.get('sector_exposure') or {}).items():
            if abs(float(exposure)) > limits.max_sector_exposure:
                reasons.append(f'sector_exposure_breach:{sector}')

        return RiskLimitResult(passed=not reasons, reasons=reasons)
