from __future__ import annotations

from ai_hedge_bot.core.settings import SETTINGS
from ai_hedge_bot.core.types import ExpectedReturnEstimate, PortfolioAllocation, PortfolioRiskSnapshot, PortfolioWeight
from ai_hedge_bot.core.utils import make_id, utc_now
from ai_hedge_bot.portfolio.risk_model import RiskModel


class PortfolioBuilder:
    def __init__(self) -> None:
        self.risk_model = RiskModel()

    def build(self, estimates: list[ExpectedReturnEstimate], optimized_weights: dict[str, float], capital_base: float = 100000.0) -> tuple[str, list[PortfolioWeight], list[PortfolioAllocation], PortfolioRiskSnapshot]:
        portfolio_id = make_id('pf', utc_now().isoformat())
        weights: list[PortfolioWeight] = []
        allocations: list[PortfolioAllocation] = []
        gross = 0.0
        net = 0.0
        long_exp = 0.0
        short_exp = 0.0
        portfolio_return = 0.0
        portfolio_vol = 0.0
        for estimate in estimates:
            weight = float(optimized_weights.get(estimate.signal_id, 0.0))
            if weight <= 0:
                continue
            marginal_risk = self.risk_model.marginal_risk(estimate)
            weights.append(PortfolioWeight(
                portfolio_id=portfolio_id,
                signal_id=estimate.signal_id,
                symbol=estimate.symbol,
                side=estimate.side,
                target_weight=round(weight, 6),
                expected_return_net=estimate.expected_return_net,
                expected_volatility=estimate.expected_volatility,
                marginal_risk=marginal_risk,
                timestamp=utc_now(),
            ))
            notional = round(capital_base * weight, 2)
            pnl = round(notional * estimate.expected_return_net, 4)
            allocations.append(PortfolioAllocation(
                portfolio_id=portfolio_id,
                signal_id=estimate.signal_id,
                symbol=estimate.symbol,
                side=estimate.side,
                target_weight=round(weight, 6),
                notional_usd=notional,
                expected_pnl_usd=pnl,
                expected_return_net=estimate.expected_return_net,
                timestamp=utc_now(),
            ))
            gross += weight
            net += weight if estimate.side == 'long' else -weight
            if estimate.side == 'long':
                long_exp += weight
            else:
                short_exp += weight
            portfolio_return += weight * estimate.expected_return_net
            portfolio_vol += (weight * estimate.expected_volatility) ** 2
        portfolio_vol = portfolio_vol ** 0.5
        raw_sharpe = portfolio_return / portfolio_vol if portfolio_vol > 0 else 0.0
        portfolio_sharpe = min(SETTINGS.portfolio_sharpe_cap, raw_sharpe)
        snapshot = PortfolioRiskSnapshot(
            portfolio_id=portfolio_id,
            gross_exposure=round(gross, 6),
            net_exposure=round(net, 6),
            long_exposure=round(long_exp, 6),
            short_exposure=round(short_exp, 6),
            turnover_estimate=round(gross, 6),
            portfolio_expected_return=round(portfolio_return, 6),
            portfolio_expected_volatility=round(portfolio_vol, 6),
            portfolio_expected_sharpe=round(portfolio_sharpe, 6),
            concentration_top_weight=round(max((w.target_weight for w in weights), default=0.0), 6),
            timestamp=utc_now(),
        )
        return portfolio_id, weights, allocations, snapshot
