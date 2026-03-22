from __future__ import annotations

from dataclasses import asdict

from ai_hedge_bot.core.settings import SETTINGS
from ai_hedge_bot.core.utils import make_id, utc_now
from ai_hedge_bot.execution.cost_model import ExecutionCostModel
from ai_hedge_bot.execution.liquidity_model import LiquidityModel
from ai_hedge_bot.execution.shadow_models import ExecutionCostBreakdown, LatencySnapshot, ShadowFill


class FillSimulator:
    def __init__(self) -> None:
        self.cost_model = ExecutionCostModel()
        self.liquidity_model = LiquidityModel()

    def simulate(self, order, latest_price: float) -> dict:
        liq = self.liquidity_model.classify(latest_price, order.qty, order.qty * latest_price)
        fill_ratio = liq['expected_fill_ratio']
        fill_qty = round(order.qty * fill_ratio, 6)
        partial = fill_qty < order.qty - 1e-9
        side_sign = 1.0 if order.side == 'long' else -1.0
        impact_bps = liq['expected_impact_bps']
        latency_cost_bps = max(0.1, SETTINGS.shadow_latency_ms / 1000.0)
        fee_bps = SETTINGS.shadow_fee_bps
        price_bump = (SETTINGS.shadow_spread_bps / 2.0 + impact_bps + latency_cost_bps) / 10000.0
        fill_price = round(latest_price * (1.0 + side_sign * price_bump), 6)
        notional = fill_qty * fill_price
        fee_usd = round(notional * fee_bps / 10000.0, 6)
        fill = ShadowFill(
            fill_id=make_id('sfill', f'{order.shadow_order_id}|{utc_now().isoformat()}'),
            shadow_order_id=order.shadow_order_id,
            portfolio_id=order.portfolio_id,
            signal_id=order.signal_id,
            symbol=order.symbol,
            side=order.side,
            fill_ts=utc_now(),
            fill_qty=fill_qty,
            fill_price=fill_price,
            maker_taker='taker' if order.order_type == 'market' else 'maker',
            fee_usd=fee_usd,
            fee_bps=fee_bps,
            liquidity_bucket=liq['liquidity_bucket'],
        )
        cost_values = self.cost_model.build(order.side, order.arrival_mid_price, fill_price, impact_bps, latency_cost_bps, fee_bps)
        cost = ExecutionCostBreakdown(
            cost_id=make_id('scost', f'{order.shadow_order_id}|{utc_now().isoformat()}'),
            shadow_order_id=order.shadow_order_id,
            portfolio_id=order.portfolio_id,
            signal_id=order.signal_id,
            symbol=order.symbol,
            side=order.side,
            arrival_mid_price=order.arrival_mid_price,
            effective_fill_price=fill_price,
            timestamp=utc_now(),
            **cost_values,
        )
        latency = LatencySnapshot(
            snapshot_id=make_id('slat', f'{order.shadow_order_id}|{utc_now().isoformat()}'),
            shadow_order_id=order.shadow_order_id,
            portfolio_id=order.portfolio_id,
            symbol=order.symbol,
            decision_to_order_ms=round(SETTINGS.shadow_latency_ms * 0.5, 3),
            order_to_first_fill_ms=round(liq['expected_delay_ms'], 3),
            order_to_complete_ms=round(liq['expected_delay_ms'] * (1.5 if partial else 1.0), 3),
            timestamp=utc_now(),
        )
        status = 'partial' if partial else 'filled'
        return {
            'fill': fill,
            'cost': cost,
            'latency': latency,
            'status': status,
            'filled_ratio': fill_ratio,
            'raw_liquidity': liq,
            'fill_dict': asdict(fill),
        }
