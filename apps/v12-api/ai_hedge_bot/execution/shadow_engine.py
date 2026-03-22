from __future__ import annotations

from ai_hedge_bot.core.utils import make_id, utc_now
from ai_hedge_bot.execution.order_lifecycle import OrderLifecycle
from ai_hedge_bot.execution.shadow_models import ShadowOrder
from ai_hedge_bot.execution.fill_simulator import FillSimulator
from ai_hedge_bot.execution.venue_router import VenueRouter


class ShadowEngine:
    def __init__(self) -> None:
        self.router = VenueRouter()
        self.lifecycle = OrderLifecycle()
        self.simulator = FillSimulator()

    def emit_shadow_orders(self, intents: list, latest_prices: dict[str, float]) -> list[ShadowOrder]:
        orders = []
        for intent in intents:
            latest_price = float(latest_prices[intent.symbol])
            route = self.router.route(intent.symbol, intent.urgency, intent.target_weight)
            qty = round(intent.target_notional_usd / max(latest_price, 1e-9), 6)
            limit_px = latest_price * (1.0 + (0.0005 if intent.side == 'long' else -0.0005))
            orders.append(ShadowOrder(
                shadow_order_id=make_id('sord', f'{intent.decision_id}|{utc_now().isoformat()}'),
                decision_id=intent.decision_id,
                portfolio_id=intent.portfolio_id,
                signal_id=intent.signal_id,
                symbol=intent.symbol,
                side=intent.side,
                venue=route['venue'],
                order_type=route['order_type'],
                tif=route['tif'],
                qty=qty,
                arrival_mid_price=latest_price,
                limit_price=round(limit_px, 6),
                created_ts=utc_now(),
                status='created',
                urgency=intent.urgency,
                participation_rate=intent.max_slice,
            ))
        return orders

    def run_cycle(self, intents: list, latest_prices: dict[str, float]) -> dict:
        decisions = []
        for intent in intents:
            decisions.append({
                'event': 'shadow_decision',
                'decision_id': intent.decision_id,
                'portfolio_id': intent.portfolio_id,
                'signal_id': intent.signal_id,
                'symbol': intent.symbol,
                'side': intent.side,
                'target_weight': intent.target_weight,
                'target_notional_usd': intent.target_notional_usd,
                'urgency': intent.urgency,
                'decision_ts': intent.decision_ts,
                'market_snapshot_ts': intent.market_snapshot_ts,
            })
        orders = self.emit_shadow_orders(intents, latest_prices)
        order_rows, fill_rows, cost_rows, latency_rows, events, transitions = [], [], [], [], [], []
        for order in orders:
            status = self.lifecycle.transition(order.status, 'pending')
            order.status = status
            order_rows.append({'event': 'shadow_order', **order.__dict__})
            transitions.append({'event': 'order_state_transition', 'shadow_order_id': order.shadow_order_id, 'from_state': 'created', 'to_state': 'pending', 'reason': 'accepted', 'transition_ts': utc_now()})
            events.append({'event': 'order_event', 'shadow_order_id': order.shadow_order_id, 'event_type': 'order_accepted', 'event_ts': utc_now(), 'payload_json': {'venue': order.venue, 'order_type': order.order_type}})
            sim = self.simulator.simulate(order, latest_prices[order.symbol])
            fill_rows.append({'event': 'shadow_fill', **sim['fill'].__dict__})
            cost_rows.append({'event': 'execution_cost', **sim['cost'].__dict__})
            latency_rows.append({'event': 'latency_snapshot', **sim['latency'].__dict__})
            next_state = sim['status']
            transitions.append({'event': 'order_state_transition', 'shadow_order_id': order.shadow_order_id, 'from_state': 'pending', 'to_state': next_state, 'reason': 'fill_simulation', 'transition_ts': utc_now()})
            events.append({'event': 'order_event', 'shadow_order_id': order.shadow_order_id, 'event_type': 'fill_simulated', 'event_ts': utc_now(), 'payload_json': {'fill_ratio': sim['filled_ratio'], 'liquidity_bucket': sim['raw_liquidity']['liquidity_bucket']}})
            order.status = next_state
        return {
            'shadow_decisions': decisions,
            'shadow_orders': order_rows,
            'shadow_fills': fill_rows,
            'execution_costs': cost_rows,
            'latency_snapshots': latency_rows,
            'order_events': events,
            'order_state_transitions': transitions,
        }
