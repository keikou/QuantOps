from __future__ import annotations

from ai_hedge_bot.execution.shadow_models import OrderState


class OrderLifecycle:
    ALLOWED = {
        'created': {'pending', 'cancelled', 'expired', 'filled', 'partial'},
        'pending': {'partial', 'filled', 'cancelled', 'expired'},
        'partial': {'filled', 'cancelled', 'expired'},
        'filled': set(),
        'cancelled': set(),
        'expired': set(),
    }

    def transition(self, current: OrderState, new: OrderState) -> OrderState:
        if new == current:
            return current
        if new not in self.ALLOWED[current]:
            raise ValueError(f'illegal order state transition: {current} -> {new}')
        return new
