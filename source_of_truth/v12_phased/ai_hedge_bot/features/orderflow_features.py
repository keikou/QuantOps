from __future__ import annotations

import pandas as pd


def build_orderflow_features(df: pd.DataFrame) -> dict[str, pd.Series]:
    bid, ask = df['bid_depth'].fillna(0.0), df['ask_depth'].fillna(0.0)
    buy, sell = df['aggressive_buy_volume'].fillna(0.0), df['aggressive_sell_volume'].fillna(0.0)
    return {
        'orderbook_imbalance': ((bid-ask)/(bid+ask+1e-12)).fillna(0.0),
        'depth_ratio': (bid/(ask+1e-12)).fillna(0.0),
        'aggressive_buy_volume': buy,
        'aggressive_sell_volume': sell,
        'trade_flow_imbalance': ((buy-sell)/(buy+sell+1e-12)).fillna(0.0),
    }
