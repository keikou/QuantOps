from __future__ import annotations


class VenueRouter:
    def route(self, symbol: str, urgency: str, target_weight: float) -> dict:
        if urgency == 'high' or target_weight >= 0.25:
            return {'venue': 'binance_paper', 'order_type': 'market', 'tif': 'IOC'}
        if target_weight >= 0.12:
            return {'venue': 'binance_paper', 'order_type': 'limit', 'tif': 'GTC'}
        return {'venue': 'binance_shadow', 'order_type': 'limit', 'tif': 'GTC'}
