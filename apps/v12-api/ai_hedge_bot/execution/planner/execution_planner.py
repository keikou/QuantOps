from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class ExecutionPlanner:
    default_expire_seconds: int = 60
    default_price_drift_bps: float = 12.0

    def _estimate_observed_volume(self, *, qty: float, arrival_mid: float, spread_bps: float, quote_age_sec: float, observed_volume: float | None) -> float:
        if observed_volume is not None and float(observed_volume) > 0.0:
            return float(observed_volume)
        notional = max(qty * arrival_mid, 0.0)
        liquidity_multiplier = 40.0 if spread_bps <= 5.0 else (25.0 if spread_bps <= 10.0 else 12.0)
        freshness_penalty = max(0.4, 1.0 - min(max(quote_age_sec, 0.0), 60.0) / 100.0)
        return max(qty * 3.0, (notional / max(arrival_mid, 1e-9)) * liquidity_multiplier * freshness_penalty)

    def _choose_route(self, *, side: str, arrival_mid: float, bid: float, ask: float, spread_bps: float, quote_age_sec: float, urgency: str, stale_quote: bool) -> tuple[str, list[dict[str, Any]], bool]:
        maker_price = ask if side == 'buy' else bid
        taker_price = ask if side == 'buy' else bid
        split_price = arrival_mid
        venue_costs = [
            {
                'route': 'maker_bias',
                'fee_bps': 0.8,
                'latency_ms': 35.0,
                'impact_bps': max(spread_bps * 0.35, 0.6),
                'price': maker_price,
            },
            {
                'route': 'taker_primary',
                'fee_bps': 2.2,
                'latency_ms': 12.0,
                'impact_bps': max(spread_bps * 0.55, 1.2),
                'price': taker_price,
            },
            {
                'route': 'split_book',
                'fee_bps': 1.4,
                'latency_ms': 18.0,
                'impact_bps': max(spread_bps * 0.45, 0.9),
                'price': split_price,
            },
        ]
        for venue in venue_costs:
            urgency_penalty = 0.0 if urgency == 'patient' else (0.5 if venue['route'] == 'maker_bias' else 0.0)
            stale_penalty = 8.0 if stale_quote and venue['route'] == 'maker_bias' else 2.5 if stale_quote else 0.0
            age_penalty = min(max(quote_age_sec, 0.0), 30.0) * (0.08 if venue['route'] == 'maker_bias' else 0.03)
            venue['score_bps'] = round(venue['fee_bps'] + venue['impact_bps'] + urgency_penalty + stale_penalty + age_penalty, 4)
        best = min(venue_costs, key=lambda item: float(item['score_bps']))
        routing_fallback = stale_quote and best['route'] != 'maker_bias'
        return str(best['route']), venue_costs, routing_fallback

    def build_plan(
        self,
        *,
        symbol: str,
        side: str,
        qty: float,
        arrival_mid: float,
        bid: float,
        ask: float,
        quote_age_sec: float,
        mode: str,
        participation_rate: float,
        alpha_horizon: str | None = None,
        observed_volume: float | None = None,
        available_margin: float | None = None,
        required_margin: float | None = None,
    ) -> dict[str, Any]:
        qty = max(float(qty or 0.0), 0.0)
        arrival_mid = max(float(arrival_mid or 0.0), 1e-9)
        bid = float(bid or arrival_mid)
        ask = float(ask or arrival_mid)
        quote_age_sec = max(float(quote_age_sec or 0.0), 0.0)
        spread_bps = max(((ask - bid) / arrival_mid) * 10000.0 if arrival_mid else 0.0, 0.0)
        notional_usd = qty * arrival_mid
        stale_quote = quote_age_sec > 20.0

        urgency = 'normal'
        if alpha_horizon in {'intraday', 'fast', 'seconds'} or quote_age_sec > 15:
            urgency = 'aggressive'
        elif alpha_horizon in {'swing', 'daily'}:
            urgency = 'patient'

        observed_volume_qty = self._estimate_observed_volume(qty=qty, arrival_mid=arrival_mid, spread_bps=spread_bps, quote_age_sec=quote_age_sec, observed_volume=observed_volume)
        volume_participation = qty / max(observed_volume_qty, 1e-9)

        if spread_bps <= 4.0 and notional_usd <= 5_000:
            algo = 'aggressive_limit'
        elif notional_usd >= 20_000:
            algo = 'twap'
        elif participation_rate >= 0.1 or spread_bps >= 8.0:
            algo = 'pov'
        else:
            algo = 'twap'

        if urgency == 'aggressive' and algo == 'twap':
            algo = 'pov'

        pov_fallback = False
        if algo == 'pov' and (observed_volume_qty <= 0.0 or volume_participation > max(participation_rate, 1e-9) * 2.5):
            algo = 'twap'
            pov_fallback = True

        expire_seconds = 15 if urgency == 'aggressive' else (180 if urgency == 'patient' else self.default_expire_seconds)
        if spread_bps >= 12.0:
            expire_seconds = min(expire_seconds, 20)

        if algo == 'twap':
            slices = min(5, max(2, math.ceil(notional_usd / 7_500.0)))
        elif algo == 'pov':
            slices = min(6, max(1, math.ceil(qty / max(observed_volume_qty * max(participation_rate, 0.01), 1e-9))))
        else:
            slices = 1

        route, routing_candidates, routing_fallback = self._choose_route(
            side=side,
            arrival_mid=arrival_mid,
            bid=bid,
            ask=ask,
            spread_bps=spread_bps,
            quote_age_sec=quote_age_sec,
            urgency=urgency,
            stale_quote=stale_quote,
        )

        child_orders = []
        remaining_qty = qty
        bucket_sec = max(int(expire_seconds / max(slices, 1)), 1)
        for idx in range(slices):
            if algo == 'pov':
                child_qty = min(remaining_qty, observed_volume_qty * max(participation_rate, 0.01))
            else:
                child_qty = remaining_qty / max(slices - idx, 1)
            child_qty = round(max(child_qty, 0.0), 8)
            remaining_qty = round(max(remaining_qty - child_qty, 0.0), 8)
            child_orders.append({
                'child_index': idx + 1,
                'child_qty': child_qty if idx < slices - 1 else round(child_qty + remaining_qty, 8),
                'style': algo,
                'time_bucket_sec': 0 if slices == 1 else bucket_sec * idx,
                'route': route,
            })
            if idx == slices - 1:
                remaining_qty = 0.0

        price_drift_bps = max(self.default_price_drift_bps, spread_bps * 1.75)
        decision_price = arrival_mid
        expiry_reason = {
            'time_expiry_at_sec': int(expire_seconds),
            'decision_price': round(decision_price, 8),
            'price_drift_bps': round(price_drift_bps, 4),
        }

        available_margin = float(available_margin) if available_margin is not None else None
        required_margin = float(required_margin) if required_margin is not None else notional_usd
        margin_limited = available_margin is not None and required_margin is not None and required_margin > max(available_margin, 0.0)

        return {
            'symbol': symbol,
            'side': side,
            'algo': algo,
            'route': route,
            'urgency': urgency,
            'participation_rate': round(participation_rate, 4),
            'expire_seconds': int(expire_seconds),
            'slice_count': int(slices),
            'child_orders': child_orders,
            'spread_bps': round(spread_bps, 4),
            'notional_usd': round(notional_usd, 2),
            'quote_age_sec': round(quote_age_sec, 3),
            'mode': mode,
            'stale_quote': stale_quote,
            'decision_price': round(decision_price, 8),
            'price_drift_bps': round(price_drift_bps, 4),
            'expiry_policy': expiry_reason,
            'observed_volume_qty': round(observed_volume_qty, 6),
            'volume_participation': round(volume_participation, 6),
            'pov_fallback': pov_fallback,
            'routing_candidates': routing_candidates,
            'routing_fallback': routing_fallback,
            'required_margin': round(required_margin, 2) if required_margin is not None else None,
            'available_margin': round(available_margin, 2) if available_margin is not None else None,
            'margin_limited': margin_limited,
        }
